# Brasalume

Jogo de RPG idle para navegador. A interface usa React + Vite, o mundo é desenhado pelo motor Canvas 2D e a arte é original, produzida no Blender.

## Pastas

| Pasta | O que tem | Vai ao ar |
|---|---|---|
| `jogo/` | App React/TypeScript com motor Canvas (`src/gameEngine.js`), imagens (`sprites/`) e configuração da Vercel | Sim |
| `arte/` | Produção da arte no Blender: roteiros (`blender/fontes/`), renders brutos (`blender/renders_2d/`), recortes finais (`exports/sprites/`), folhas de conceito e turnaround (`personagens/`, `inimigos/`, `mapas/`), referências e o catálogo `CATALOGO_ARTE.md` | Não |
| `ferramentas/` | Testes do jogo no navegador (fluidez, erros, todas as abas) e folhas de conferência da arte | Não |
| `arquivo/` | Versões substituídas e o estúdio aposentado da Tripo. Nada é apagado: o que é trocado vem para cá | Não |
| `.claude/` | Configuração de execução local (`launch.json`) | Não |

Cada pasta tem um README com os detalhes.

## Como as partes se ligam

```
jogo/src/gameEngine.js ──(arte/blender/fontes/extrair_dados.js)──> arte/blender/fontes/dados_jogo.json
                                                                     │  classes, monstros, regiões e masmorras
arte/blender/fontes/gerar.py (Blender) ─────────────────────────> arte/blender/renders_2d/   renders brutos
arte/blender/fontes/montar_folhas.py ───────────────────────────> arte/exports/sprites/ e as folhas de conceito
arte/blender/fontes/integrar.py ────────────────────────────────> jogo/sprites/ e o bloco /*META*/ em src/gameEngine.js
                                                                     (a versão trocada vai para arquivo/sprites/)
jogo/src/main.tsx monta a interface React
  ├─ legacyUiAdapter.tsx converte, temporariamente, as abas HTML do motor em elementos React
  ├─ uiBridge.ts transmite estado tipado entre interface e motor
  └─ perfProbe.ts só é ativado na rota de diagnóstico
jogo/src/gameEngine.js contém regras, simulação e ciclo do mundo
  ├─ coreMath.ts oferece cálculos e aleatoriedade determinística
  ├─ canvasPrimitives.ts contém projeção isométrica e primitivas de desenho
  └─ browserStorage.ts isola o armazenamento local do navegador
```

## Jogar

- Na pasta `jogo/`, rode `npm install` uma vez e `npm run dev`.
- A configuração `jogo` do `.claude/launch.json` abre o servidor Vite na porta 8765.
- `jogo/jogar_local.html` continua como endereço compatível e redireciona para o app.

## Publicar

- **Vercel** (brasalume.vercel.app):
  - só quando for pedido;
  - o envio sai da pasta `jogo/`; `npm run build` gera o app e copia os sprites para `dist/`.

## Refazer ou mudar a arte

Veja `arte/README.md`. Em resumo:
1. `node arte/blender/fontes/extrair_dados.js`
2. Os renders no Blender (`gerar.py`).
3. `python -I arte/blender/fontes/montar_folhas.py tudo`
4. `python -I arte/blender/fontes/integrar.py`
5. `python -I arte/blender/fontes/catalogo.py`

## Referência

A única referência para nomes, conteúdo e visual é o motor do jogo (`jogo/src/gameEngine.js`). O `BASE_REFERENCIA.md` era do projeto antigo (Ecos de Altheria) e não vale para o Brasalume.

## Mudança de pastas (24/11/2026)

| Antes | Agora |
|---|---|
| `idle/` | `jogo/` |
| `idle/archive/` | `arquivo/` |
| `idle/assets/` e `idle/montar_sprites.py` (estúdio da Tripo, aposentado) | `arquivo/estudio_tripo/` |
| `design/` | `arte/` |
| `design/imagens/referencias/`, `design/mapas/conceitos/`, `design/mapas/referencias/` (estavam vazias) | `arte/referencias/` |
| testes que viviam numa pasta temporária | `ferramentas/` |
