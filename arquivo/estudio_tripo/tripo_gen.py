"""Gera modelos 3D na Tripo (API v3) a partir de uma lista de pedidos.

Uso:
  python -I tripo_gen.py jobs_teste.json --dry-run   # mostra o plano, o custo e o saldo; não gasta nada
  python -I tripo_gen.py jobs_teste.json             # cria as tarefas, espera e baixa os modelos

A chave vem da variável TRIPO_API_KEY, do arquivo E:\\RPGjogo\\.env (linha TRIPO_API_KEY=...) ou do arquivo
%USERPROFILE%\\.tripo_key (só a chave). Ela nunca é impressa nem gravada em outro lugar.
O andamento fica em tripo/manifest.json: rodar de novo retoma as tarefas já criadas em vez de pagar outra vez.
"""
import json
import os
import pathlib
import re
import sys
import time
import urllib.parse

import requests

API = 'https://openapi.tripo3d.com/v3'
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'tripo'
# o Bloco de Notas costuma acrescentar .txt ao salvar, por isso as duas grafias
ENV_FILES = [pathlib.Path(r'E:\RPGjogo\.env'), pathlib.Path(r'E:\RPGjogo\.env.txt')]
KEY_FILES = [pathlib.Path.home() / '.tripo_key', pathlib.Path.home() / '.tripo_key.txt']
# créditos por modelo de texto para 3D com textura (tabela oficial da v3.1); sem textura custa 10
COST = {'fast': 20, 'standard': 20, 'detailed': 30, 'extreme': 40}
MAX_DOWNLOAD = 80 * 1024 * 1024
TERMINAL_BAD = ('failed', 'cancelled', 'banned', 'expired')
JOB_KEYS = ('model', 'negative_prompt', 'texture', 'pbr', 'texture_quality', 'face_limit', 'model_seed',
            'texture_seed', 'smart_low_poly', 'geometry_quality', 'quad', 'auto_size')


class TripoError(Exception):
    def __init__(self, http, code, msg, sug):
        super().__init__(f'HTTP {http}, código {code}: {msg}' + (f' ({sug})' if sug else ''))
        self.http, self.code = http, code


def read_text_any(path):
    """Lê texto salvo pelo Bloco de Notas ou pelo PowerShell (UTF-8, ANSI ou UTF-16)."""
    data = path.read_bytes()
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        return data.decode('utf-16')
    return data.decode('utf-8-sig', errors='replace')


def load_key():
    key = os.environ.get('TRIPO_API_KEY', '').strip()
    for env in ENV_FILES:
        if key:
            break
        if env.exists():
            for line in read_text_any(env).splitlines():
                line = line.strip()
                if line.startswith('TRIPO_API_KEY='):
                    key = line.split('=', 1)[1].strip().strip('"').strip("'")
    for kf in KEY_FILES:   # arquivo só com a chave, compartilhado com as outras sessões
        if key:
            break
        if kf.exists():
            key = next((ln.strip() for ln in read_text_any(kf).splitlines() if ln.strip()), '')
    return key


def est_cost(job):
    if not job.get('texture', True) and not job.get('pbr', False):
        base = 10
    else:
        base = COST.get(job.get('texture_quality', 'standard'), 20)
    return base + (10 if job.get('smart_low_poly') else 0) + (20 if job.get('geometry_quality') == 'detailed' else 0) \
        + (5 if job.get('quad') else 0)


class Tripo:
    def __init__(self, key):
        self.s = requests.Session()
        self.s.headers.update({'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})

    def call(self, method, path, **kw):
        for attempt in range(7):
            try:
                r = self.s.request(method, API + path, timeout=60, **kw)
            except requests.RequestException as e:
                wait = min(32, 2 ** attempt)
                print(f'  rede: {type(e).__name__}; nova tentativa em {wait}s')
                time.sleep(wait)
                continue
            if r.status_code == 429:
                wait = int(r.headers.get('Retry-After') or min(32, 2 ** (attempt + 1)))
                print(f'  limite da API; esperando {wait}s')
                time.sleep(wait)
                continue
            try:
                body = r.json()
            except ValueError:
                raise TripoError(r.status_code, None, 'resposta que não é JSON', '')
            if r.status_code >= 400 or body.get('code', 0) != 0:
                raise TripoError(r.status_code, body.get('code'), body.get('message') or r.reason, body.get('suggestion') or '')
            return body.get('data') or {}
        raise TripoError(0, None, 'a Tripo não respondeu depois de várias tentativas', '')


def fetch(url, path):
    """Baixa um arquivo gerado (sem o cabeçalho de autorização: a URL já é assinada)."""
    u = urllib.parse.urlparse(url or '')
    if u.scheme != 'https':
        raise TripoError(0, None, 'URL de download inesperada', '')
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        size = 0
        tmp = path.with_suffix(path.suffix + '.part')
        with open(tmp, 'wb') as f:
            for chunk in r.iter_content(1 << 16):
                size += len(chunk)
                if size > MAX_DOWNLOAD:
                    raise TripoError(0, None, 'arquivo grande demais', '')
                f.write(chunk)
        tmp.replace(path)
    return size


def ext_of(url, default):
    suf = pathlib.PurePosixPath(urllib.parse.urlparse(url).path).suffix.lower()
    return suf if suf in ('.png', '.webp', '.jpg', '.jpeg', '.glb', '.fbx', '.obj', '.zip') else default


def save(man_path, man):
    man_path.write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding='utf-8')


def main():
    for stream in (sys.stdout, sys.stderr):   # acentos certos no terminal do Windows
        try:
            stream.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError):
            pass
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    if not args:
        sys.exit(__doc__)
    spec = json.loads(pathlib.Path(args[0]).read_text(encoding='utf-8'))
    defaults, style = spec.get('defaults', {}), spec.get('style', '')
    jobs = []
    for j in spec['jobs']:
        if not re.fullmatch(r'[a-z0-9_]+', j['name']):
            sys.exit('Nome inválido: ' + j['name'])
        job = {k: v for k, v in defaults.items() if k in JOB_KEYS}
        job.update({k: v for k, v in j.items() if k in JOB_KEYS})
        job['prompt'] = (j['prompt'] + (', ' + style if style else ''))[:1024]
        if 'negative_prompt' in job:
            job['negative_prompt'] = job['negative_prompt'][:255]
        jobs.append((j['name'], job))

    OUT.mkdir(exist_ok=True)
    man_path = OUT / 'manifest.json'
    man = json.loads(man_path.read_text(encoding='utf-8')) if man_path.exists() else {}
    todo = [(n, j) for n, j in jobs if not (man.get(n, {}).get('status') == 'success' and (OUT / f'{n}.glb').exists())]
    new = [(n, j) for n, j in todo if not man.get(n, {}).get('task_id') or man[n].get('status') in TERMINAL_BAD]
    est = sum(est_cost(j) for _, j in new)
    print(f'{len(jobs)} pedidos: {len(jobs) - len(todo)} prontos, {len(todo) - len(new)} em andamento, {len(new)} novos.')
    print(f'Custo estimado das tarefas novas: {est} créditos.')
    for n, j in new:
        print(f'  {n}: {est_cost(j)} créditos | {j["prompt"][:96]}...')

    key = load_key()
    if not key:
        sys.exit('Chave não encontrada. Salve só a chave em %USERPROFILE%\\.tripo_key, '
                 'ou crie E:\\RPGjogo\\.env com a linha TRIPO_API_KEY=sua_chave.')
    t = Tripo(key)
    try:
        bal = t.call('GET', '/account/balance')
    except TripoError as e:
        sys.exit('Não consegui ler o saldo: ' + str(e) + (' A chave foi recusada.' if e.http in (401, 403) else ''))
    balance = float(bal.get('balance') or 0)
    print(f'Saldo da API: {balance:g} créditos (reservados agora: {bal.get("frozen", 0)}).')
    if dry:
        return
    if est and balance < est:
        sys.exit(f'Saldo insuficiente: a leva precisa de {est} créditos.')

    for n, j in new:
        try:
            data = t.call('POST', '/generation/text-to-model', json=j)
        except TripoError as e:
            man[n] = {'status': 'failed', 'error': 'criação: ' + str(e), 'prompt': j['prompt']}
            save(man_path, man)
            print(f'  não criou {n}: {e}')
            continue
        man[n] = {'task_id': data['task_id'], 'status': 'queued', 'prompt': j['prompt'], 'created': int(time.time())}
        save(man_path, man)
        print(f'  criada: {n}')

    pending = [n for n, _ in todo if man.get(n, {}).get('task_id') and man[n].get('status') not in TERMINAL_BAD]
    t0, delay = time.time(), 2.0
    while pending and time.time() - t0 < 1800:
        time.sleep(delay)
        delay = min(15.0, delay * 1.4)
        for n in list(pending):
            try:
                info = t.call('GET', '/tasks/' + man[n]['task_id'])
            except TripoError as e:
                print(f'  consulta de {n} falhou: {e}')
                continue
            st = info.get('status')
            man[n]['status'], man[n]['progress'] = st, info.get('progress')
            if st == 'success':
                out = info.get('output') or {}
                man[n]['credits'] = info.get('credits_consumed')
                try:
                    size = fetch(out.get('model_url'), OUT / f'{n}.glb')
                    man[n]['bytes'] = size
                    if out.get('rendered_image_url'):
                        fetch(out['rendered_image_url'], OUT / (n + '_preview' + ext_of(out['rendered_image_url'], '.png')))
                except (TripoError, requests.RequestException) as e:
                    man[n]['status'] = 'download_failed'
                    man[n]['error'] = str(e)
                    print(f'  {n} ficou pronta, mas o download falhou: {e}')
                else:
                    print(f'  pronta: {n} ({man[n]["credits"]} créditos, {size // 1024} KB)')
                pending.remove(n)
            elif st in TERMINAL_BAD:
                man[n]['error'] = f'{info.get("error_code")} {info.get("error_message")}'
                pending.remove(n)
                print(f'  falhou: {n}: {man[n]["error"]} (tarefa falha não é cobrada)')
        save(man_path, man)
        if pending:
            prog = ', '.join(f'{n} {man[n].get("progress") or 0}%' for n in pending)
            print(f'  aguardando: {prog}')
    if pending:
        print('Ainda em andamento depois de 30 min: rode de novo para continuar esperando (não cobra outra vez).')

    spent = sum((man[n].get('credits') or 0) for n, _ in jobs if man.get(n, {}).get('status') == 'success')
    ok = [n for n, _ in jobs if man.get(n, {}).get('status') == 'success']
    print(f'Prontos: {len(ok)} de {len(jobs)}. Créditos desta lista: {spent}.')
    try:
        bal = t.call('GET', '/account/balance')
        print(f'Saldo agora: {float(bal.get("balance") or 0):g} créditos.')
    except TripoError:
        pass


if __name__ == '__main__':
    main()
