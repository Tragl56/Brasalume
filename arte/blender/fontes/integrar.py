# Integra no jogo as imagens que o sistema de sprites usa (pasta jogo/sprites + bloco SPRITE_META do motor React/Canvas):
#  - retratos das vocações (heroi_<id>): cartas da aba de vocação e seletor de visual; o desenho em código continua como reserva;
#  - herói no mapa (heroi_mapa_<id>): tira animada por vocação (6 quadros do passo e 1 do golpe); auras e enfeites seguem em código;
#  - peças de cenário das regiões (regiao_<id>_<tipo>), das masmorras (masmorra_<id>_<tipo>) e comuns (regiao_comum_<tipo>);
#  - monstros (inimigo_<nome>): o jogo acha a imagem pelo nome do monstro e a anima (respira, flutua, balança); sem ela, vale o desenho em código;
#  - texturas de chão (chao_<cenário>, chao_masmorra): o ladrilho de cada cenário projetado no ângulo do jogo, com o brilho da cor do chão;
#  - poderes das habilidades (fx_<efeito>): tiras animadas que o jogo combina por habilidade (receitas SKFX no jogo).
# Este roteiro só reescreve o conteúdo entre os marcadores /*META*/ do jogo; SPRITE_USE e SPRITE_H são editados à mão.
# Uso: python -I arte/blender/fontes/integrar.py   (imprime o SPRITE_USE e o SPRITE_H sugeridos)
import os
import sys
import json
import shutil
import hashlib
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import numpy as np
from PIL import Image
import montar_folhas as MF

RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
DESIGN = os.path.join(RAIZ, 'arte')
SPR = os.path.join(RAIZ, 'jogo', 'sprites')
ARQUIVO = os.path.join(RAIZ, 'arquivo', 'sprites')   # versões substituídas dos sprites
JOGO = os.path.join(RAIZ, 'jogo', 'src', 'gameEngine.js')
D = MF.D
ALTURA = {'pine': 64, 'snowpine': 64, 'round': 54, 'bush': 19, 'rock': 16, 'boulder': 24, 'birch': 56, 'dead': 40, 'reeds': 22, 'column': 48,
          'glass': 24, 'obelisk': 52, 'bones': 14, 'wreck': 46, 'crystal': 44, 'tower': 84, 'pillar': 56, 'shroomprop': 18, 'bonepile': 12,
          'honey': 24, 'icicle': 30, 'crate': 18, 'coins': 9, 'cart': 26, 'bookshelf': 36, 'menhir': 26, 'portal': 62,
          'shard': 42, 'vent': 11}   # shard e vent: o jogo anima em código por cima da imagem (o cristal flutua, a fenda pulsa)
GAMA_MONSTROS = .75   # clareia as sombras dos monstros (armaduras escuras somem na noite do jogo) sem estourar os claros


def _sha(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()


def gravar(img_ou_origem, nome):
    """Grava em jogo/sprites; se já existir um arquivo diferente com o mesmo nome, a versão anterior vai para arquivo/sprites."""
    os.makedirs(SPR, exist_ok=True)
    destino = os.path.join(SPR, nome + '.png')
    tmp = destino + '.novo'
    if isinstance(img_ou_origem, str):
        shutil.copy2(img_ou_origem, tmp)
    else:
        img_ou_origem.save(tmp, format='PNG', optimize=True)
    if os.path.isfile(destino) and _sha(destino) != _sha(tmp):
        os.makedirs(ARQUIVO, exist_ok=True)
        guarda, k = os.path.join(ARQUIVO, nome + '.png'), 2
        while os.path.isfile(guarda):   # nunca sobrescreve uma versão já guardada
            guarda, k = os.path.join(ARQUIVO, '%s_%d.png' % (nome, k)), k + 1
        shutil.copy2(destino, guarda)
    os.replace(tmp, destino)


TW, TH, LADRILHOS = 64, 32, 4   # casa do jogo (losango de 64 x 32 unidades) e casas por lado do ladrilho de chão
CHAO_BRILHO = {'peaks': 1.3, 'dunes': 1.05, 'lava': 1.0, 'void': 1.0}   # brilho do chão em relação à cor do jogo (padrão 1,12)


def _linear(a):
    return np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4)


def _srgb(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= .0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - .055)


def textura_chao(im, decor, escala=2, amostras=4):
    """Ladrilho de chão (quadrado, 4 x 4 casas, visto de cima) projetado no ângulo do jogo: vira um retângulo de
    4 * TW x 4 * TH unidades (escala pixels por unidade) que também repete sem emenda, com o canto de cima do mapa num
    canto. Cada pixel é a média de amostras x amostras pontos em luz linear, para o detalhe fino não serrilhar.
    O brilho médio fica igual ao da cor do chão do cenário no jogo (GROUND) vezes CHAO_BRILHO; a textura das
    masmorras fica em cinza médio, porque o jogo a mistura em sobreposição com a cor do piso de cada masmorra."""
    lin = _linear(np.asarray(im.convert('RGB'), dtype=np.float64) / 255.0)
    N = lin.shape[0]
    W, H, k = LADRILHOS * TW * escala, LADRILHOS * TH * escala, amostras
    ys, xs = np.mgrid[0:H * k, 0:W * k]
    x, y = (xs + .5) / (k * escala), (ys + .5) / (k * escala)            # unidades do jogo a partir do canto do mapa
    u = (x / (TW / 2) + y / (TH / 2)) / 2 * N / LADRILHOS - .5             # casa i (pixel da imagem)
    v = (y / (TH / 2) - x / (TW / 2)) / 2 * N / LADRILHOS - .5             # casa j
    x0, y0 = np.floor(u).astype(int), np.floor(v).astype(int)
    fx, fy = (u - x0)[..., None], (v - y0)[..., None]
    x0, y0 = x0 % N, y0 % N
    x1, y1 = (x0 + 1) % N, (y0 + 1) % N
    c = (lin[y0, x0] * (1 - fx) * (1 - fy) + lin[y0, x1] * fx * (1 - fy) + lin[y1, x0] * (1 - fx) * fy + lin[y1, x1] * fx * fy)
    c = c.reshape(H, k, W, k, 3).mean(axis=(1, 3))
    lum = np.array([.2126, .7152, .0722])
    if decor == 'masmorra':
        alvo = _linear(np.array(128 / 255.0))
    else:
        g0, g1 = (np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0 for h in D['GROUND'][decor])
        alvo = float((_linear(g0) + _linear(g1)) / 2 @ lum) * CHAO_BRILHO.get(decor, 1.12)
    px = c @ lum   # média; com rachaduras e pontos acesos, a mediana (o brilho deles não conta)
    ref = np.median(px) if decor in ('lava', 'void', 'crystals') else px.mean()
    ganho = float(np.clip(alvo / max(ref, 1e-4), .3, 2.5))
    out = Image.fromarray(np.round(_srgb(c * ganho) * 255).astype(np.uint8), 'RGB')
    return out, ganho


def main():
    meta, uso = {}, {}
    # 1) retratos das vocações: vista de conceito (3/4 de frente), recortada, 240 px de altura
    for cid in ['none'] + list(D['CLASSES']):
        src = os.path.join(DESIGN, 'blender', 'renders_2d', 'personagens', cid, 'conceito.png')
        if not os.path.isfile(src):
            continue
        im = MF.recorte(MF.abrir(src))
        k = 240 / im.height
        im = im.resize((max(1, round(im.width * k)), 240), Image.LANCZOS)
        nome = 'heroi_' + ('portador' if cid == 'none' else cid)
        gravar(im, nome)
        meta[nome] = {'w': im.width, 'h': im.height, 'ax': round(im.width / 2, 1), 'ay': im.height, 'hpx': im.height}
    # 1b) herói no mapa: uma tira por vocação, sem mudar a escala entre elas; u = unidades do jogo por pixel (o jogo desenha com s * u)
    pa = os.path.join(DESIGN, 'exports', 'sprites', 'personagens_anim', 'sprites.json')
    herois = json.load(open(pa, encoding='utf-8')) if os.path.isfile(pa) else {}
    for cid, m in sorted(herois.items()):
        src = os.path.join(DESIGN, 'exports', 'sprites', 'personagens_anim', cid + '.png')
        if not os.path.isfile(src) or not m.get('u'):
            continue
        nome = 'heroi_mapa_' + ('portador' if cid == 'none' else cid)
        gravar(src, nome)
        meta[nome] = {k: m[k] for k in ('w', 'h', 'ax', 'ay', 'hpx', 'n', 'u')}
    # 1c) texturas de chão: um ladrilho sem emenda por cenário (chao_<cenário>) e o das masmorras (chao_masmorra),
    #     já projetado no ângulo do jogo e com o brilho acertado (textura_chao); o jogo cobre o chão repetindo a imagem
    pasta_chao = os.path.join(DESIGN, 'blender', 'renders_2d', 'chao')
    brilhos = {}
    for arq in sorted(os.listdir(pasta_chao)) if os.path.isdir(pasta_chao) else []:
        decor = arq[:-4]
        if not arq.endswith('.png') or (decor != 'masmorra' and decor not in D['GROUND']):
            continue
        im, ganho = textura_chao(Image.open(os.path.join(pasta_chao, arq)), decor)
        nome = 'chao_' + decor
        gravar(im, nome)
        meta[nome] = {'w': im.width, 'h': im.height, 'ax': 0, 'ay': 0, 'hpx': im.height, 'tex': 1}
        print('chão %-9s brilho x%.2f' % (decor, ganho))
        if decor != 'masmorra':   # cor do material que dá o chão do jogo, para as cenas de região (kit_mapas)
            brilhos[decor] = round(ganho / CHAO_BRILHO.get(decor, 1.12), 3)
    if brilhos:
        json.dump(brilhos, open(os.path.join(pasta_chao, 'brilho.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True)
    # 1d) poderes das habilidades (fx_<efeito>): os quadros de cada efeito recortados juntos (a mesma caixa para
    #     todos) e postos numa grade de até 4096 px de largura; os de luz em cinza com transparência (o jogo pinta)
    pasta_fx = os.path.join(DESIGN, 'blender', 'renders_2d', 'efeitos')
    for nome in sorted(os.listdir(pasta_fx)) if os.path.isdir(pasta_fx) else []:
        info_p = os.path.join(pasta_fx, nome, 'quadros.json')
        if not os.path.isfile(info_p):
            continue
        info = json.load(open(info_p, encoding='utf-8'))
        qs = [Image.open(os.path.join(pasta_fx, nome, 'quadro_%d.png' % i)).convert('RGBA') for i in range(info['n'])
              if os.path.isfile(os.path.join(pasta_fx, nome, 'quadro_%d.png' % i))]
        if len(qs) != info['n']:
            print('efeito incompleto, fica de fora:', nome)
            continue
        caixa = None
        for q in qs:
            b = q.getchannel('A').point(lambda v: 255 if v > 3 else 0).getbbox()
            if b:
                caixa = b if caixa is None else (min(caixa[0], b[0]), min(caixa[1], b[1]), max(caixa[2], b[2]), max(caixa[3], b[3]))
        if caixa is None:
            print('efeito vazio, fica de fora:', nome)
            continue
        x0, y0 = max(0, caixa[0] - 2), max(0, caixa[1] - 2)
        x1, y1 = min(qs[0].width, caixa[2] + 2), min(qs[0].height, caixa[3] + 2)
        w, h = x1 - x0, y1 - y0
        cols = max(1, min(len(qs), 4096 // w))
        linhas = (len(qs) + cols - 1) // cols
        tinta = bool(info.get('tinta'))
        folha = Image.new('LA' if tinta else 'RGBA', (w * cols, h * linhas), (0, 0) if tinta else (0, 0, 0, 0))
        for i, q in enumerate(qs):
            r = q.crop((x0, y0, x1, y1))
            if tinta:   # o brilho em cinza (o render já é cinza) com a transparência
                r = Image.merge('LA', (r.getchannel('R'), r.getchannel('A')))
            folha.paste(r, ((i % cols) * w, (i // cols) * h))
        gravar(folha, 'fx_' + nome)
        m = {'w': w, 'h': h, 'n': len(qs), 'c': cols, 'ax': round(info['ox'] - x0, 1), 'ay': round(info['oy'] - y0, 1), 'hpx': h, 'u': info['u'],
             'dur': info.get('dur', .5), 'modo': info.get('modo', 'iso')}
        for k in ('luz', 'tinta', 'laco', 'chao'):
            if info.get(k):
                m[k] = 1
        if info.get('brilho'):
            m['brilho'] = info['brilho']
        meta['fx_' + nome] = m
    # 1e) peças do HUD (ui_*): o CSS do jogo usa direto (molduras em border-image, fundos); não entram no META
    pasta_ui = os.path.join(DESIGN, 'blender', 'renders_2d', 'ui')
    for arq in sorted(os.listdir(pasta_ui)) if os.path.isdir(pasta_ui) else []:
        if arq.startswith('ui_') and arq.endswith('.png'):
            gravar(Image.open(os.path.join(pasta_ui, arq)).convert('RGBA'), arq[:-4])
    # 2) peças de cenário
    p = os.path.join(DESIGN, 'exports', 'sprites', 'mapas', 'sprites.json')
    pecas = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
    zonas = {z['id']: z for z in D['ZONES']}
    dgs = {g['id']: g for g in D['DUNGEONS']}
    for chave, m in sorted(pecas.items()):
        pasta, tipo = chave.split('/')
        if tipo not in ALTURA:
            continue
        if pasta == 'comum':
            nome, grupo = 'regiao_comum_' + tipo, '*'
        elif pasta in zonas:
            nome, grupo = 'regiao_%s_%s' % (pasta, tipo), zonas[pasta]['decor']
        elif pasta in dgs:
            nome, grupo = 'masmorra_%s_%s' % (pasta, tipo), '*'
        else:
            continue
        gravar(os.path.join(DESIGN, 'exports', 'sprites', 'mapas', pasta, tipo + '.png'), nome)
        meta[nome] = m
        uso.setdefault(grupo, {})[tipo] = nome
    # 3) monstros: o sprite de 3/4 já olha para a esquerda, como o desenho em código; o ponto de apoio fica nos pés.
    #    Com animação (exports/sprites/inimigos_anim), a imagem é uma tira: n quadros de largura w; o último é o golpe.
    p = os.path.join(DESIGN, 'exports', 'sprites', 'inimigos', 'sprites.json')
    inimigos = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
    pa = os.path.join(DESIGN, 'exports', 'sprites', 'inimigos_anim', 'sprites.json')
    anim = json.load(open(pa, encoding='utf-8')) if os.path.isfile(pa) else {}
    curva = [round(255 * (v / 255) ** GAMA_MONSTROS) for v in range(256)]
    for s, m in sorted(inimigos.items()):
        src = os.path.join(DESIGN, 'exports', 'sprites', 'inimigos', s + '.png')
        tira = os.path.join(DESIGN, 'exports', 'sprites', 'inimigos_anim', s + '.png')
        if s in anim and os.path.isfile(tira):
            src, m = tira, anim[s]
        if not os.path.isfile(src):
            continue
        r, g, b, a = Image.open(src).convert('RGBA').split()
        im = Image.merge('RGBA', (r.point(curva), g.point(curva), b.point(curva), a))
        nome = 'inimigo_' + s
        gravar(im, nome)
        meta[nome] = {'w': m.get('w', im.width), 'h': m.get('h', im.height), 'ax': m['ax'], 'ay': m['ay'], 'hpx': m.get('hpx', m['ay'])}
        if m.get('n', 1) > 1:
            meta[nome]['n'] = m['n']
    # 4) sprites.json e o bloco META do jogo
    json.dump(meta, open(os.path.join(SPR, 'sprites.json'), 'w', encoding='utf-8'), indent=1)
    s = open(JOGO, encoding='utf-8', newline='').read()   # sem traduzir fins de linha
    a = s.index('/*META*/')
    b = s.index('/*META*/', a + 8)
    s = s[:a + 8] + json.dumps(meta, separators=(',', ':')) + s[b:]
    open(JOGO, 'w', encoding='utf-8', newline='').write(s)
    n = {p: sum(k.startswith(p) for k in meta) for p in ('heroi_', 'heroi_mapa_', 'inimigo_', 'chao_', 'fx_')}
    print('imagens no jogo:', len(meta), '(retratos %d, herói no mapa %d, peças %d, monstros %d, texturas de chão %d, poderes %d)' % (
        n['heroi_'] - n['heroi_mapa_'], n['heroi_mapa_'], len(meta) - n['heroi_'] - n['inimigo_'] - n['chao_'] - n['fx_'], n['inimigo_'],
        n['chao_'], n['fx_']))
    print('const SPRITE_USE = {')
    for g in sorted(uso, key=lambda x: (x == '*', x)):
        print("  %s: {%s}," % (repr(g) if g == '*' else g, ', '.join("%s: '%s'" % (t, n) for t, n in uso[g].items())))
    print('};')
    tipos = sorted({t for g in uso.values() for t in g})
    print('const SPRITE_H = {%s};' % ', '.join('%s: %s' % (t, ALTURA[t]) for t in tipos))


if __name__ == '__main__':
    main()
