# Folha de conferência: quadro 0 de cada monstro do jogo (jogo/sprites/inimigo_*.png), em grade, no tom do chão do jogo.
# Uso: python -I folha_monstros.py <pasta sprites> <saida_prefixo> [colunas] [linhas] [celula] [quadro]
import json, os, sys
from PIL import Image, ImageDraw
pasta, saida = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 10
lins = int(sys.argv[4]) if len(sys.argv) > 4 else 7
cel = int(sys.argv[5]) if len(sys.argv) > 5 else 150
qd = int(sys.argv[6]) if len(sys.argv) > 6 else 0
meta = json.load(open(os.path.join(pasta, 'sprites.json'), encoding='utf-8'))
nomes = sorted(k for k in meta if k.startswith('inimigo_'))
por = cols * lins
for f in range(0, len(nomes), por):
    lote = nomes[f:f + por]
    folha = Image.new('RGBA', (cols * cel, lins * (cel + 18)), (27, 43, 37, 255))
    d = ImageDraw.Draw(folha)
    for i, n in enumerate(lote):
        m = meta[n]; im = Image.open(os.path.join(pasta, n + '.png')).convert('RGBA')
        q = min(qd, m.get('n', 1) - 1) if qd >= 0 else m.get('n', 1) - 1
        fr = im.crop((q * m['w'], 0, (q + 1) * m['w'], m['h']))
        k = min((cel - 8) / fr.width, (cel - 8) / fr.height)
        fr = fr.resize((max(1, round(fr.width * k)), max(1, round(fr.height * k))), Image.LANCZOS)
        x, y = (i % cols) * cel, (i // cols) * (cel + 18)
        folha.alpha_composite(fr, (x + (cel - fr.width) // 2, y + cel - fr.height - 2))
        d.text((x + 3, y + cel + 2), n[8:][:24], fill=(230, 220, 196, 255))
    nome = '%s_%d.png' % (saida, f // por + 1)
    folha.convert('RGB').save(nome)
    print(nome, folha.size, len(lote))
