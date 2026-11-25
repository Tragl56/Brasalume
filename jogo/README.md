# Jogo

Esta pasta é o que vai ao ar.

| Arquivo | O que é |
|---|---|
| `index.html` | Entrada do app React, compilado com Vite. |
| `src/main.tsx` | Interface React, abas, HUD e diálogos. |
| `src/legacyUiAdapter.tsx` | Adaptador tipado que converte as telas HTML do motor legado em elementos React. |
| `src/uiBridge.ts` | Estado reativo tipado que o motor publica para os componentes React. |
| `src/browserStorage.ts` | Fronteira tipada para acesso e falhas do armazenamento local do navegador. |
| `src/coreMath.ts` | Funções matemáticas puras e gerador pseudoaleatório determinístico do motor. |
| `src/canvasPrimitives.ts` | Primitivas de desenho e projeção isométrica compartilhadas pelo motor Canvas. |
| `src/types.d.ts` | Contratos dos eventos que conectam o motor legado e a interface. |
| `src/perfProbe.ts` | Instrumentação opcional de desempenho, carregada apenas pela interface de diagnóstico. |
| `src/gameEngine.js` | Simulação, regras, conteúdo das abas e desenho do mundo em Canvas 2D. |
| `src/styles.css` | Estilos da interface. |
| `jogar_local.html` | Compatibilidade: redireciona para `index.html`. |
| `brasalume.html` | Atalho compatível que abre o jogo. |
| `sprites/` | As imagens que o jogo carrega: retratos das vocações, o herói no mapa, peças de cenário, monstros, as texturas de chão (`chao_<cenário>.png`, já no ângulo do jogo), os poderes das habilidades (`fx_<peça>.png`) e as peças do HUD (`ui_<peça>.png`), mais o `sprites.json`. Quem grava aqui é o `arte/blender/fontes/integrar.py`, que também atualiza o bloco `/*META*/` do jogo. Não edite à mão. |
| `package.json`, `vite.config.js`, `vercel.json` | Dependências, build e publicação na Vercel. |

O jogo procura cada imagem em `sprites/<nome>.png`. Se a imagem não carregar, o jogo usa o desenho em código.

O React controla e reconcilia os elementos das abas, HUD e diálogos; o conteúdo das abas vem do motor e é convertido em nós React. A simulação e o mapa continuam em Canvas 2D. A interface e o bridge já usam TypeScript; o motor permanece JavaScript nesta etapa para manter a migração gradual e isolada. Os saves continuam no mesmo armazenamento local do navegador.

## Rodar e compilar

Na pasta `jogo/`, rode `npm install` uma vez e depois `npm run dev`. Use `npm run typecheck` para validar os módulos TypeScript e `npm test` para rodar os testes do armazenamento local. Para gerar os arquivos de publicação, rode `npm run build`; o resultado fica em `dist/`.
