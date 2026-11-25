# Folha de conferência das tiras animadas exportadas: uma linha por monstro (ciclo + golpe), na cor do chão do jogo.
# Uso: python -I folha_tiras.py <pasta das tiras> <sprites.json> <saida.png> [slug1,slug2,... | todos] [altura]
import json, os, sys
from PIL import Image, ImageDraw
pasta, meta_p, saida = sys.argv[1], sys.argv[2], sys.argv[3]
meta = json.load(open(meta_p, encoding='utf-8'))
lista = sorted(meta) if len(sys.argv) < 5 or sys.argv[4] == 'todos' else sys.argv[4].split(',')
alt = int(sys.argv[5]) if len(sys.argv) > 5 else 72
linhas = []
for s in lista:
    m = meta.get(s)
    if not m or m.get('n', 1) < 2:
        continue
    im = Image.open(os.path.join(pasta, s + '.png')).convert('RGBA')
    k = alt / m['h']
    linhas.append((s, im.resize((max(1, round(im.width * k)), alt), Image.LANCZOS), round(m['w'] * k)))
larg = max(l[1].width for l in linhas) + 170
folha = Image.new('RGBA', (larg, (alt + 6) * len(linhas)), (27, 43, 37, 255))
d = ImageDraw.Draw(folha)
for r, (s, im, fw) in enumerate(linhas):
    y = r * (alt + 6)
    d.text((6, y + alt // 2 - 6), s[:26], fill=(230, 220, 196, 255))
    folha.alpha_composite(im, (170, y))
    d.line([(170 + fw * 6, y), (170 + fw * 6, y + alt)], fill=(240, 162, 63, 255))
folha.convert('RGB').save(saida)
print(folha.size, len(linhas))
