# Arquivo

Versões substituídas e ferramentas aposentadas. Nada aqui é carregado pelo jogo. Não apague nada desta pasta: é aqui que fica o que foi trocado.

| O que | O que é |
|---|---|
| `brasalume-standalone-original.html` | A página original do jogo, de antes de virar o `jogo/jogar_local.html`. Não alterar. |
| `sprites/` | Sprites substituídos. O `arte/blender/fontes/integrar.py` guarda aqui a versão anterior sempre que grava uma imagem nova com o mesmo nome; quando o nome já existe aqui, acrescenta `_2`, `_3`. |
| `design_monstros_antes_polimento/` | A arte dos monstros antes do polimento de 24/11/2026: recortes (`exports_sprites/`) e folhas de conceito (`inimigos/`). `antes_e_depois.png` compara 16 monstros antes e depois. |
| `arte_cenario_antes_polimento/` | O cenário antes do polimento de 25/11/2026: recortes das peças (`exports_sprites_mapas/`) e folhas de mapa (`folhas_mapas/`). `antes_e_depois.png` compara 12 peças, e `jogo_depois_seis_regioes.png` mostra o jogo depois. |
| `CATALOGO_ARTE-anterior-2026-11-24.md` | O catálogo de arte antes de ser gerado a partir do código. |
| `estudio_tripo/` | O estúdio de sprites da Tripo, aposentado quando a arte passou para o Blender. Os caminhos de dentro ainda apontam para a antiga pasta `idle/`. Não rode o `montar_sprites.py`: ele reescreveria o bloco `/*META*/` do jogo, que agora é do `integrar.py`. |
