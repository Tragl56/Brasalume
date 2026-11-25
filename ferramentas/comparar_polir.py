# Antes e depois do polimento: para cada monstro, o render antigo (quadro 0) e o novo lado a lado, grandes e no tamanho do jogo
# (uns 60 px de altura, com a mesma gama .75 que o integrar.py aplica), sobre o tom do chão do jogo.
# Uso: python -I comparar_polir.py <pasta_nova> <saida.png> slug1,slug2,... [colunas] [sufixo_novo]
import os, sys
from PIL import Image, ImageDraw
RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'arte', 'blender', 'renders_2d', 'inimigos')
nova, saida, lista = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
suf = sys.argv[5] if len(sys.argv) > 5 else ''
curva = [round(255 * (v / 255) ** .75) for v in range(256)]
CH = (27, 43, 37, 255)
GR, PQ = 180, 58


def recorte(im):
    b = im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(b) if b else im


def alt(im, h):
    k = h / im.height
    return im.resize((max(1, round(im.width * k)), h), Image.LANCZOS)


def gama(im):
    r, g, b, a = im.split()
    return Image.merge('RGBA', (r.point(curva), g.point(curva), b.point(curva), a))


celw, celh = 2 * 200 + 20, GR + PQ + 40
lins = (len(lista) + cols - 1) // cols
folha = Image.new('RGBA', (cols * celw, lins * celh), CH)
d = ImageDraw.Draw(folha)
for i, s in enumerate(lista):
    x, y = (i % cols) * celw, (i // cols) * celh
    a_p = os.path.join(RAW, s, 'quadro_0.png')
    b_p = os.path.join(nova, s + suf + '.png')
    d.text((x + 6, y + 2), s[:40], fill=(230, 220, 196, 255))
    for j, p in enumerate((a_p, b_p)):
        if not os.path.isfile(p):
            continue
        im = recorte(Image.open(p).convert('RGBA'))
        g = alt(im, GR)
        if g.width > 196:
            g = g.resize((196, max(1, round(g.height * 196 / g.width))), Image.LANCZOS)
        folha.alpha_composite(g, (x + 8 + j * 205 + (196 - g.width) // 2, y + 14 + GR - g.height))
        p2 = gama(alt(im, PQ))
        folha.alpha_composite(p2, (x + 8 + j * 205 + (196 - p2.width) // 2, y + 20 + GR + PQ - p2.height))
    d.text((x + 8, y + celh - 14), 'antes', fill=(150, 150, 140, 255))
    d.text((x + 213, y + celh - 14), 'depois', fill=(240, 162, 63, 255))
folha.convert('RGB').save(saida)
print(saida, folha.size)
