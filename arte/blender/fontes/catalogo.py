"""Gera arte/CATALOGO_ARTE.md a partir do código do jogo (via dados_jogo.json) e dos arquivos que existem no disco.

Uso (na raiz do projeto):
    node arte/blender/fontes/extrair_dados.js
    python -I arte/blender/fontes/catalogo.py

Uma caixa só fica marcada quando o arquivo correspondente existe. Os caminhos esperados estão em arte/README.md.
"""
import json
import os
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.abspath(os.path.join(AQUI, '..', '..'))
RAIZ = os.path.dirname(DESIGN)
IDLE = os.path.join(RAIZ, 'jogo')   # a pasta do jogo (antes se chamava idle)
D = json.load(open(os.path.join(AQUI, 'dados_jogo.json'), encoding='utf-8'))
JOGO = open(os.path.join(IDLE, 'src', 'gameEngine.js'), encoding='utf-8').read()


def slug(nome):
    s = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')


def existe(*partes):
    return os.path.isfile(os.path.join(*partes))


def tem_png(pasta):
    return os.path.isdir(pasta) and any(f.lower().endswith('.png') for f in os.listdir(pasta))


def caixa(ok):
    return '☑' if ok else '☐'


def citado(nome):
    return ("'" + nome + "'") in JOGO or ('"' + nome + '"') in JOGO


def integrado(nome_sprite):
    """Integrado = o PNG está na pasta que o jogo carrega (jogo/sprites) e o código cita esse nome (aspas simples ou duplas)."""
    return existe(IDLE, 'sprites', nome_sprite + '.png') and citado(nome_sprite)


def integrado_prefixo(prefixo):
    """Mapas: pelo menos uma peça <prefixo>_<tipo>.png está em jogo/sprites e o código cita esse nome."""
    pasta = os.path.join(IDLE, 'sprites')
    if not os.path.isdir(pasta):
        return False
    return any(f.startswith(prefixo + '_') and f.endswith('.png') and not f.endswith('.anterior.png') and citado(f[:-4]) for f in os.listdir(pasta))


# ---------- caminhos que cada coluna procura ----------
def st_classe(cid):
    pasta = os.path.join(DESIGN, 'personagens', 'classes', cid)
    return (existe(pasta, cid + '_conceito.png'), existe(pasta, 'turnaround', cid + '_turnaround.png'),
            existe(DESIGN, 'exports', 'sprites', 'personagens', cid + '.png'), integrado('heroi_' + cid))


def st_portador():
    pasta = os.path.join(DESIGN, 'personagens', 'portador')
    return (existe(pasta, 'portador_conceito.png'), existe(pasta, 'turnaround', 'portador_turnaround.png'),
            existe(DESIGN, 'exports', 'sprites', 'personagens', 'portador.png'), integrado('heroi_portador'))


def st_inimigo(nome, kind, chefe):
    s = slug(nome)
    conceito = existe(DESIGN, 'inimigos', 'chefes', s + '.png') if chefe else existe(DESIGN, 'inimigos', 'monstros', kind, s + '.png')
    return conceito, existe(DESIGN, 'exports', 'sprites', 'inimigos', s + '.png'), integrado('inimigo_' + s)


def st_mapa(grupo, mid):
    pasta = os.path.join(DESIGN, 'mapas', grupo, mid)
    return (existe(pasta, mid + '_conceito.png'), tem_png(os.path.join(DESIGN, 'exports', 'sprites', 'mapas', mid)),
            integrado_prefixo(('regiao_' if grupo == 'regioes' else 'masmorra_') + mid))


# ---------- tabelas ----------
LIN = {'guerreiro': 'Guerreiro', 'arcanista': 'Arcanista', 'batedor': 'Batedor', 'devoto': 'Devoto'}
out = []
w = out.append
w('# Catálogo de arte do Brasalume')
w('')
w('Inventário gerado a partir de `../jogo/src/gameEngine.js` por `blender/fontes/extrair_dados.js` e `blender/fontes/catalogo.py`. '
  'Não edite as caixas à mão: rode os dois scripts de novo. Uma caixa só fica marcada quando o arquivo existe no caminho descrito em `README.md`.')
w('')
tot_cl = len(D['CLASSES'])
w('Resumo do código: %d classes (4 vocações-base e %d caminhos), %d famílias visuais de monstros, %d regiões, %d chefes errantes e %d masmorras.'
  % (tot_cl, tot_cl - 4, len(D['KINDS']), len(D['ZONES']), len(D['FIELD_BOSSES']), len(D['DUNGEONS'])))
w('')
w('## Portador (antes da vocação)')
w('')
w('| ID | Nome | Conceito | Turnaround | Sprite 2D | Integrado |')
w('|---|---|---:|---:|---:|---:|')
c = st_portador()
w('| `none` | Portador | %s | %s | %s | %s |' % tuple(caixa(x) for x in c))
w('')
w('## Classes')
w('')
w('As vocações-base são o estágio 1. Cada caminho tem quatro estágios; o nome do estágio 2 é o nome usado nas pastas e no visual (`LOOK`).')
w('')
w('| ID | Nome | Linhagem | Estágios seguintes | Conceito | Turnaround | Sprite 2D | Integrado |')
w('|---|---|---|---|---:|---:|---:|---:|')
for cid, C in D['CLASSES'].items():
    tiers = C.get('tiers') or []
    nome = C.get('nome') or (tiers[0]['nome'] if tiers else cid)
    depois = ' → '.join(t['nome'] for t in tiers[1:]) if tiers else ('vocação-base' if C.get('base') else '')
    s = st_classe(cid)
    w('| `%s` | %s | %s | %s | %s | %s | %s | %s |' % (cid, nome, LIN.get(C.get('arch'), C.get('arch', '')), depois, *(caixa(x) for x in s)))
w('')
w('## Regiões e mapas')
w('')
w('| ID | Nome | Níveis | Cenário no código | Conceito do mapa | Assets de cenário | Integrado |')
w('|---|---|---|---|---:|---:|---:|')
for z in D['ZONES']:
    s = st_mapa('regioes', z['id'])
    w('| `%s` | %s | %d–%d | `%s` | %s | %s | %s |' % (z['id'], z['nome'], z['lv'][0], z['lv'][1], z['decor'], *(caixa(x) for x in s)))
w('')
w('## Masmorras')
w('')
w('| ID | Nome | Entrada | Nível | Tema no código | Conceito do mapa | Assets de cenário | Integrado |')
w('|---|---|---|---:|---|---:|---:|---:|')
for g in sorted(D['DUNGEONS'], key=lambda x: x['lv']):
    s = st_mapa('masmorras', g['id'])
    w('| `%s` | %s | %s | %d | `%s` | %s | %s | %s |' % (g['id'], g['nome'], D['ZONES'][g['after']]['nome'], g['lv'], g['theme'], *(caixa(x) for x in s)))
w('')


def tabela(titulo, linhas, chefe, nota=None):
    w('## ' + titulo)
    w('')
    if nota:
        w(nota)
        w('')
    w('| Nome | Família visual | Onde aparece | Conceito 2D | Sprite 2D | Integrado |')
    w('|---|---|---|---:|---:|---:|')
    vistos = set()
    for nome, kind, onde in linhas:
        if nome in vistos:
            continue
        vistos.add(nome)
        s = st_inimigo(nome, kind, chefe)
        w('| %s | `%s` | %s | %s | %s | %s |' % (nome, kind, onde, *(caixa(x) for x in s)))
    w('')


zn = {z['id']: z['nome'] for z in D['ZONES']}
tabela('Monstros comuns das regiões', [(m[0], m[1], z['nome']) for z in D['ZONES'] for m in z['mobs']], False)
tabela('Chefes de região', [(z['boss'][0], z['boss'][1], z['nome']) for z in D['ZONES']], True)
tabela('Chefes errantes', [(fb[0], fb[1], zn.get(zid, zid)) for zid, fb in D['FIELD_BOSSES'].items()], True)
DG = sorted(D['DUNGEONS'], key=lambda x: x['lv'])
tabela('Monstros de masmorra', [(m[0], m[1], g['nome']) for g in DG for m in g['mobs']], False,
       'Alguns nomes repetem monstros das regiões; a arte pode ser a mesma, com a pasta da família visual.')
tabela('Subchefes de masmorra', [(g['mini'][0], g['mini'][1], g['nome']) for g in DG], True)
tabela('Chefes de masmorra', [(g['boss'][0], g['boss'][1], g['nome']) for g in DG], True)

# famílias e quantos inimigos usam cada uma
uso = {}
for z in D['ZONES']:
    for m in z['mobs'] + [z['boss']]:
        uso.setdefault(m[1], set()).add(m[0])
for fb in D['FIELD_BOSSES'].values():
    uso.setdefault(fb[1], set()).add(fb[0])
for g in D['DUNGEONS']:
    for m in g['mobs'] + [g['mini'], g['boss']]:
        uso.setdefault(m[1], set()).add(m[0])
w('## Famílias visuais (`KINDS`)')
w('')
w('Cada família tem uma pasta em `inimigos/monstros/<família>/`. Entradas da mesma família podem partir da mesma base, mas cada uma precisa continuar distinguível.')
w('')
w('| Família | Inimigos que usam |')
w('|---|---:|')
for k in D['KINDS']:
    w('| `%s` | %d |' % (k, len(uso.get(k, ()))))
w('')
open(os.path.join(DESIGN, 'CATALOGO_ARTE.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
print('catálogo gerado:', len(out), 'linhas')
