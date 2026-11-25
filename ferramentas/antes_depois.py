# Antes e depois a partir das tiras exportadas (quadro 0 de cada tira, com a gama .75 do jogo), grande e no tamanho do jogo.
# Uso: python -I antes_depois.py <pasta tiras antes> <pasta tiras depois> <saida.png> slug1,slug2,... [colunas]
import json, os, sys
from PIL import Image, ImageDraw
antes, depois, saida, lista = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
cols = int(sys.argv[5]) if len(sys.argv) > 5 else 4
curva = [round(255 * (v / 255) ** .75) for v in range(256)]
CH = (27, 43, 37, 255)
GR, PQ = 170, 56
ma = json.load(open(os.path.join(antes, 'sprites.json'), encoding='utf-8'))
md = json.load(open(os.path.join(depois, 'sprites.json'), encoding='utf-8'))


def quadro(pasta, meta, s):
    m = meta[s]
    im = Image.open(os.path.join(pasta, s + '.png')).convert('RGBA').crop((0, 0, m['w'], m['h']))
    r, g, b, a = im.split()
    im = Image.merge('RGBA', (r.point(curva), g.point(curva), b.point(curva), a))
    bb = a.point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(bb) if bb else im


def alt(im, h, wmax):
    k = min(h / im.height, wmax / im.width)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


celw, celh = 2 * 190 + 16, GR + PQ + 36
lins = (len(lista) + cols - 1) // cols
folha = Image.new('RGBA', (cols * celw, lins * celh), CH)
d = ImageDraw.Draw(folha)
for i, s in enumerate(lista):
    x, y = (i % cols) * celw, (i // cols) * celh
    d.text((x + 6, y + 2), s[:44], fill=(230, 220, 196, 255))
    for j, (p, m) in enumerate(((antes, ma), (depois, md))):
        if s not in m:
            continue
        im = quadro(p, m, s)
        g = alt(im, GR, 184)
        folha.alpha_composite(g, (x + 6 + j * 192 + (184 - g.width) // 2, y + 14 + GR - g.height))
        q = alt(im, PQ, 120)
        folha.alpha_composite(q, (x + 6 + j * 192 + (184 - q.width) // 2, y + 18 + GR + PQ - q.height))
    d.text((x + 8, y + celh - 13), 'antes', fill=(150, 150, 140, 255))
    d.text((x + 200, y + celh - 13), 'depois', fill=(240, 162, 63, 255))
folha.convert('RGB').save(saida, quality=92)
print(saida, folha.size)
