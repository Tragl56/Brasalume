"""Liga os sprites da Tripo ao Brasalume.

Lê sprites/sprites.json (gravado pelo estúdio em assets/render.html), confere quais imagens existem
em sprites/ e grava os dados delas no jogar_local.html, entre as marcas /*META*/. Não reconstrói o
jogo nem mexe em outra parte do arquivo; sem sprites, deixa a lista vazia e vale o desenho antigo.

Uso:
  python -I montar_sprites.py            # usa a pasta deste script (E:\\RPGjogo\\idle)
  python -I montar_sprites.py PASTA      # usa outra pasta com jogar_local.html e sprites/ (cópia de teste)

Rode quando nenhuma outra sessão estiver editando o jogar_local.html: o arquivo é regravado inteiro.
Depois, para publicar, envie também as imagens listadas no fim (sprites/NOME.png) junto com a página.
"""
import json
import pathlib
import re
import sys

KEYS = ('w', 'h', 'ax', 'ay', 'hpx')


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')   # acentos certos no terminal do Windows
    except (AttributeError, ValueError):
        pass
    base = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent
    game, sp = base / 'jogar_local.html', base / 'sprites'
    if not game.exists():
        sys.exit(f'Não achei {game}.')
    meta, skipped = {}, []
    man_path = sp / 'sprites.json'
    if man_path.exists():
        man = json.loads(man_path.read_text(encoding='utf-8'))
        for name, m in sorted((man.get('sprites') or {}).items()):
            ok = (re.fullmatch(r'[a-z0-9_]+', name) and isinstance(m, dict)
                  and all(isinstance(m.get(k), (int, float)) for k in KEYS)
                  and m['w'] > 0 and m['h'] > 0 and m['hpx'] > 0)
            if not ok:
                skipped.append(name + ' (dados incompletos)')
            elif not (sp / f'{name}.png').exists():
                skipped.append(name + ' (sem a imagem)')
            else:
                meta[name] = {k: m[k] for k in KEYS}
    html = game.read_text(encoding='utf-8')
    marks = re.findall(r'/\*META\*/.*?/\*META\*/', html, re.S)
    if len(marks) != 1:
        sys.exit(f'Esperava uma única marca /*META*/ no jogo e achei {len(marks)}.')
    new = html.replace(marks[0], '/*META*/' + json.dumps(meta, separators=(',', ':')) + '/*META*/')
    if new != html:
        game.write_text(new, encoding='utf-8', newline='')
    print(f'{len(meta)} sprites ligados ao jogo: ' + (', '.join(meta) or 'nenhum (vale o desenho antigo)'))
    for s in skipped:
        print('  deixado de fora: ' + s)
    if meta:
        print('Para publicar, envie junto com a página: ' + ', '.join(f'sprites/{n}.png' for n in meta))


if __name__ == '__main__':
    main()
