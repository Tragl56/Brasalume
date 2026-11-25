# Folha de conferência dos quadros brutos: uma linha por monstro, os 6 quadros do ciclo e o do golpe lado a lado.
# Uso: python -I folha_quadros.py <raiz do projeto> <saida.png> slug1,slug2,...
import os, sys
from PIL import Image, ImageDraw
raiz, saida, lista = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
RAW = os.path.join(raiz, 'arte', 'blender', 'renders_2d', 'inimigos')
nomes = ['quadro_%d.png' % i for i in range(6)] + ['quadro_ataque.png']
cel = 120
linhas = [s for s in lista if all(os.path.isfile(os.path.join(RAW, s, n)) for n in nomes)]
folha = Image.new('RGBA', (cel * 7 + 150, cel * len(linhas)), (27, 43, 37, 255))
d = ImageDraw.Draw(folha)
for r, s in enumerate(linhas):
    d.text((6, r * cel + cel // 2 - 6), s[:22], fill=(230, 220, 196, 255))
    for c, n in enumerate(nomes):
        im = Image.open(os.path.join(RAW, s, n)).convert('RGBA').resize((cel, cel), Image.LANCZOS)
        folha.alpha_composite(im, (150 + c * cel, r * cel))
    d.line([(150 + 6 * cel, r * cel), (150 + 6 * cel, r * cel + cel)], fill=(240, 162, 63, 255))
folha.convert('RGB').save(saida)
print(folha.size, len(linhas), 'de', len(lista))
