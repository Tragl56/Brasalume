# Brasalume

Jogo RPG idle para navegador. O arquivo principal é `idle/jogar_local.html`.

## Abrir o jogo

- Abra `idle/jogar_local.html` diretamente no navegador; ou
- sirva a pasta `idle` por HTTP e acesse `/jogar_local.html`.

A configuração de execução `.claude/launch.json` serve `idle` na porta 8765. O estúdio de sprites usa `idle/assets/render_server.py` na porta 8790.

## Estrutura

- `idle/`: jogo e recursos necessários para executá-lo.
- `idle/assets/`: estúdio de sprites, geração Tripo e dados de trabalho usados por essas ferramentas.
- `idle/sprites/`: sprites exportados que o jogo pode carregar; vazio significa que o desenho atual de fallback continua em uso.
- `idle/archive/`: cópia preservada da antiga página duplicada `brasalume.html`.
- `design/`: referências e materiais de arte, organizados em `design/README.md`.
- `.claude/`: configurações locais de execução.

`idle/brasalume.html` é um atalho compatível que encaminha para `idle/jogar_local.html`. Edite o arquivo principal para evitar manter duas cópias divergentes do jogo.

## Referências

A referência do Brasalume é só o código do jogo (`idle/jogar_local.html`). O `design/BASE_REFERENCIA.md` é do projeto antigo (Ecos de Altheria) e não vale para o Brasalume.

`design/CATALOGO_ARTE.md` é gerado a partir do código: rode `node design/blender/fontes/extrair_dados.js` e depois `python -I design/blender/fontes/catalogo.py` sempre que o jogo ganhar classes, monstros, regiões ou masmorras.

## Publicação

O artefato do jogo deve ser publicado a partir de `idle/jogar_local.html`. O `idle/brasalume.html` é só o atalho de 345 bytes: publicá-lo deixaria a página sem o jogo.
