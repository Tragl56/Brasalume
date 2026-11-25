# Arte do Brasalume

Aqui se produz a arte do Brasalume: roteiros do Blender, renders, recortes, folhas de conceito e turnaround, referências e o catálogo. A única referência para nomes, conteúdo e visual é o motor em `../jogo/src/gameEngine.js`. O `BASE_REFERENCIA.md` é do projeto antigo (Ecos de Altheria) e não vale para o Brasalume.

## Pastas

- `referencias/`: referências visuais externas, estudos gerais de cenário e capturas do projeto.
- `personagens/portador/turnaround/`: referências 2D do Portador.
- `personagens/classes/<id>/turnaround/`: folhas de referência, uma pasta para cada classe existente no código.
- `inimigos/monstros/<família>/`: conceitos e referências organizados pelas famílias visuais usadas no jogo.
- `inimigos/chefes/`: conceitos e referências de elites, chefes e inimigos especiais.
- `mapas/regioes/<id>/` e `mapas/masmorras/<id>/`: design de cada região e masmorra existente.
- `blender/fontes/`: os roteiros do Blender (kits de herói, monstro e cenário, render, montagem das folhas, integração no jogo e catálogo) e o `dados_jogo.json` extraído do jogo.
- `blender/renders_2d/`: renders brutos do Blender, matéria-prima das folhas e dos recortes (podem ser refeitos com o `gerar.py`).
- `exports/sprites/`: imagens finais destinadas ao jogo, separadas por personagens, inimigos e mapas. `exports/sprites/inimigos_anim/` guarda a animação dos monstros: uma tira por monstro com 6 quadros do ciclo e 1 do golpe. `exports/sprites/personagens_anim/` guarda o herói no mapa: uma tira por vocação com 6 quadros do passo e 1 do golpe.

## Convenções

- Use IDs e nomes conferidos no código; não crie entradas de catálogo por suposição.
- Mantenha referências, conceitos editáveis e exports finais separados.
- Não substitua sprites do jogo sem confirmar compatibilidade com o Canvas 2D.
- `CATALOGO_ARTE.md` lista as classes, regiões, masmorras e inimigos identificados no código. Use-o para acompanhar conceitos, turnarounds, sprites e integração.
- Sprites finais são PNG com transparência real.

## Nomes de arquivo que o catálogo procura

O catálogo marca uma caixa só quando encontra o arquivo neste caminho. `<id>` é o ID do código; `<nome>` é o nome do inimigo em minúsculas, sem acentos e com `_` no lugar de espaços (por exemplo, `Rainha-Musgo Antiga` vira `rainha_musgo_antiga`).

| Coluna | Caminho |
|---|---|
| Portador: conceito, turnaround, sprite | `personagens/portador/portador_conceito.png`, `personagens/portador/turnaround/portador_turnaround.png`, `exports/sprites/personagens/portador.png` |
| Classe: conceito | `personagens/classes/<id>/<id>_conceito.png` |
| Classe: turnaround | `personagens/classes/<id>/turnaround/<id>_turnaround.png` |
| Classe: sprite 2D | `exports/sprites/personagens/<id>.png` |
| Monstro comum ou de masmorra: conceito | `inimigos/monstros/<família>/<nome>.png` |
| Chefe, chefe errante, subchefe: conceito | `inimigos/chefes/<nome>.png` |
| Inimigo: sprite 2D | `exports/sprites/inimigos/<nome>.png` |
| Região ou masmorra: conceito | `mapas/regioes/<id>/<id>_conceito.png` ou `mapas/masmorras/<id>/<id>_conceito.png` |
| Região ou masmorra: assets de cenário | qualquer PNG em `exports/sprites/mapas/<id>/` |
| Integrado | o PNG está em `../jogo/sprites/` e o código do jogo cita esse nome (no `SPRITE_META` ou no `SPRITE_USE`): `heroi_<id>` (retratos das vocações), `inimigo_<nome>`, e para mapas pelo menos uma peça `regiao_<id>_<tipo>` ou `masmorra_<id>_<tipo>` |

## Ferramentas

- `blender/fontes/extrair_dados.js` lê o jogo e grava `blender/fontes/dados_jogo.json` (classes, visuais, monstros, regiões e masmorras). Não executa o jogo.
- `blender/fontes/catalogo.py` gera `CATALOGO_ARTE.md` a partir desse JSON e dos arquivos que existem.

Na raiz do projeto:

```
node arte/blender/fontes/extrair_dados.js
python -I arte/blender/fontes/catalogo.py
```

- `blender/fontes/kit_base.py` (materiais, primitivas, luz, câmera, render), `kit_heroi.py` (heróis pela tabela `LOOK`), `kit_monstros.py` (uma base por família de `KINDS`, com traços pelo nome) e `kit_mapas.py` (peças de cenário, cena de região em losango e sala de masmorra) montam a cena no Blender. `gerar.py` renderiza; os renders brutos ficam em `blender/renders_2d/`.
- `blender/fontes/montar_folhas.py` monta as folhas finais (conceito, turnaround, cartões de inimigo, folhas de mapa) e exporta os sprites recortados para `exports/sprites/`.
- `blender/fontes/integrar.py` copia para `../jogo/sprites/` os retratos das vocações, o herói no mapa (`heroi_mapa_<id>`), as peças de cenário e os monstros (estes com gama .75, para não sumirem na noite do jogo) e atualiza o bloco `SPRITE_META` em `../jogo/src/gameEngine.js`. Quando um arquivo muda, a versão anterior fica em `../arquivo/sprites/`. No jogo, cada monstro acha a imagem pelo nome (`inimigo_<nome>`) e carrega quando aparece pela primeira vez; sem a imagem, vale o desenho em código.
- Animação dos monstros: no kit, as peças que se mexem ficam dentro de `with parte(R, tipo, pivô, ...)` (perna, asa, cauda, tentáculo, braço, cabeça, boca...). `kit_monstros.pose()` gira essas partes quadro a quadro; `gerar.py -- quadros` renderiza 6 quadros do ciclo e 1 do golpe com a mesma câmera do sprite, e `montar_folhas.py quadros` junta tudo numa tira com o mesmo recorte. No jogo, asas, tentáculos, chamas e caules animam o tempo todo; quem anda (feras, aranhas, caranguejos, esqueletos, cavaleiros, golens, mímicos) anima ao andar, e todos mostram o quadro do golpe ao atacar.
- Acabamento dos monstros: ao renderizar inimigos, `gerar.py` liga `kit_base.ACAB`, que dá a todos os materiais (menos vidro e luz) manchas largas de cor, sombra nas dobras e encontros de peças (oclusão do Cycles) e um brilho molhado menos plástico. Heróis e retratos não usam. Desde 25/11/2026, as peças de cenário (`gerar.py -- pecas`) e as cenas de região e de masmorra também usam. No `kit_mapas.py`:
  - os pinheiros têm galhos em estrela com as pontas caídas (`_estrela`);
  - as copas são cachos irregulares;
  - há capim de fios baixo na base de árvores e colunas, nas regiões de chão com mato (`capim()`; o anel que carrega os fios some do render por `show_instancer_for_render`);
  - as pedras têm musgo de fios (`musgo_fios`) e cascalho (`pedrinhas`), sem capim, que nelas virava franja;
  - as colunas têm rachaduras e trepadeira, o caixote tem tábuas e os cogumelos da Toca dos Esporos seguem o estilo novo.

  No `kit_monstros.py`:
  - `relevo()` deixa a superfície irregular (gosma, carne, chapéu de cogumelo, casco). O ruído fica preso à peça e não escorrega quando ela se mexe na animação.
  - `pelo()` faz pelagem de fios (partículas de cabelo) em feras, morcegos, mariposa, zangão, aranha, iéti e musgo. No Blender, o comprimento do fio é a soma das "velocidades" em metros (normal e direção do pente); `hair_length` não serve, porque só reescreve a parte da normal.
  - `espectral()` é o corpo de fantasmas e águas-vivas: transparente no meio e aceso na borda.
  - `esclera()` faz olhos com veias, `vitral()` faz cacos de vidro colorido com filetes de chumbo, e há os materiais `gosma` (luz espalhada por dentro) e `escama`.
  - Gosmas e cogumelos foram redesenhados (base que cede, escorridos, entulho meio afundado, musgo; pé com rosto, saia esfarrapada, lamelas e verrugas). Feras de gelo e de névoa têm pelo, e a névoa fica na ponta dos fios.
- Cuidados no Blender 5.3 sem janela:
  - pelo com brilho acetinado (sheen) e transparência derruba o Cycles, por isso o material do pelo não usa sheen;
  - converter curva em malha pelo operador derruba o programa depois de limpar a cena, por isso partes com pelo usam `tubo_malha()`.
- Peças que se mexem no jogo: o cristal do Abismo (`shard`) e a fenda de lava da Forja (`vent`) são imagens paradas, e o jogo faz o cristal flutuar e a fenda pulsar e soltar brasas em código, por cima da imagem. Tocha e poça continuam só com o desenho em código (`PECAS_ANIMADAS` no `gerar.py`).
- Herói no mapa: `gerar.py -- quadros_herois` monta cada vocação com `kit_heroi.construir(..., mapa=True)` (sem aura e sem companheiro, que o jogo desenha em código, e com a lanterna no quadril direito, visível nesse ângulo) e renderiza o passo e o golpe na vista do sprite, olhando para a direita. `montar_folhas.py quadros_herois` faz as tiras sem mudar a escala entre vocações; `quadros.json` guarda onde cai o pé e quantas unidades do jogo cabem num pixel, para o herói sair do tamanho do desenho em código. No jogo, o passo segue a fase da caminhada, o golpe aparece no avanço do ataque, e auras, enfeites do estágio e companheiros continuam em código.

- Chão das regiões e das masmorras (desde 25/11/2026): `kit_chao.py` faz um ladrilho sem emenda por cenário. O ladrilho cobre 4 x 4 casas do mapa e é visto de cima. `gerar.py -- chao` o renderiza em `blender/renders_2d/chao/<cenário>.png`, com a lajota cinza das masmorras em `masmorra.png`.
  - Sem emenda: as coordenadas viram um toro em 4D, e todo ruído e Voronoi é 4D. A borda direita continua na esquerda, e a de cima na de baixo.
  - Relevo de verdade: a malha tem um quadradinho por pixel e é deslocada pela altura do material. Pedras, tufos, lajes e ondulações fazem sombra com o sol, que vem do alto da tela do jogo. A malha passa do quadro, para as sombras de fora também aparecerem.
  - Peças: pedras de quina (`pedras_quinas`), rachaduras em trechos soltos (`rachaduras`) e lajes alinhadas às casas (`lajes`). O sorteio de cada laje também repete no ladrilho.
  - Nada grande dentro do ladrilho: manchas de terra, poças, placas de rocha e o piche ficam menores que uma casa e meia. A variação larga vem do jogo, que não se repete.
  - Para acertar quanto cada mancha cobre, `BRASALUME_SONDA=<nome>` troca o material pelo valor guardado com `sonda()`, em cinza. Use com `BRASALUME_RAW` numa pasta de teste e meça os percentis da imagem.
  - `integrar.py` (função `textura_chao`) projeta o ladrilho no ângulo do jogo, num retângulo de 4 casas de largura (512 x 256) que também repete sem emenda. A média é feita em luz linear, então não serrilha. O brilho médio fica igual ao da cor do chão do cenário no jogo (`GROUND`) vezes `CHAO_BRILHO`; as masmorras ficam em cinza médio.
  - No jogo, `cobrirChao` cobre o chão com a imagem, e `manchasChao` põe por cima manchas de várias casas (mais claras ou escuras, mais quentes ou frias). Nas masmorras, a lajota entra em sobreposição com a cor do piso de cada uma. Sem a imagem, o chão continua pintado em código.
  - As cenas de região das folhas de mapa usam o mesmo material, só com o relevo de sombreamento, porque a malha da cena é grossa. Lá uma casa mede `CASA_CENA`, a proporção entre casa e pinheiro do jogo. O `integrar.py` grava o brilho de cada chão em `blender/renders_2d/chao/brilho.json`, e a cena usa esse valor, para o chão da folha ficar com a luz do jogo.
- Poderes das habilidades (desde 25/11/2026): `kit_efeitos.py` (a base) e `kit_poderes.py` (o catálogo `EFEITOS`, com 98 peças) fazem uma biblioteca de efeitos animados. `gerar.py -- efeitos` grava cada peça em `blender/renders_2d/efeitos/<peça>/quadro_<n>.png`, com um `quadros.json` que guarda o ponto de apoio, a escala e a duração.
  - Tipos de peça: golpes (faixas de luz), estouros, clarões e partículas; volumes (fogo, explosão, fumaça, poeira, veneno, sombra, nevasca, incenso); raios; traços (círculos mágicos, runas, mira); corpos de luz (escudo, espada, martelo, foice, mãos, lobo, olho, relógio, portal, sol, lua); e objetos de verdade (flechas, virotes, lança, bomba, barril, correntes, rede, armadilha, cristais, pilar de pedra, vinhas, relíquia, estandarte, falcão, corvo).
  - As peças de luz saem em cinza com transparência: o jogo pinta cada uma na cor da habilidade (do escuro para a cor e para o branco no miolo) e soma a luz na tela. As outras saem nas cores de verdade.
  - Câmera `iso` a 30 graus para o que fica no chão ou em pé; câmera `lado` para golpes, projéteis e feixes, que o jogo gira na direção do alvo.
  - `integrar.py` recorta os quadros de cada peça com a mesma caixa, monta a tira em grade (até 4096 px de largura) e grava `jogo/sprites/fx_<peça>.png` e a entrada no `/*META*/`.
  - No jogo, `SKFX` dá a receita de cada uma das 181 habilidades: o projétil, o efeito no alvo, o de cada golpe, o de cada tique de dano contínuo, o que prende ou marca o alvo e a aura dos reforços. Nenhuma receita repete a de outra. A barra do HUD pinta o ícone de cada habilidade com a peça que mais a representa.
  - As peças só carregam quando o herói tem a habilidade; sem a imagem, valem os efeitos antigos, feitos em código.
- Peças do HUD (desde 25/11/2026): `kit_ui.py` renderiza, vistos de cima, as molduras de ferro e bronze, o medalhão do retrato, o tubo das barras, o encaixe e a placa da barra de habilidades, as placas dos botões, a faixa e o divisor dos títulos, os ícones de ouro, cinzas e insígnias e o couro sem emenda dos painéis. `gerar.py -- ui` grava em `blender/renders_2d/ui/`, e `integrar.py` copia para `jogo/sprites/ui_<peça>.png`. O CSS do jogo usa as molduras em `border-image`, com o meio de cada lado repetindo.

Render (Blender 5 em `E:\blender.exe`, sem janela; `BRASALUME_GPU=CUDA` usa a placa de vídeo, `BRASALUME_PREVIA=1` faz prévia rápida):

```
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- classes all
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- monstros all
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- pecas all
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- regioes all
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- masmorras all
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- quadros all
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- quadros_herois all
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- chao all
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- efeitos all
blender --background --factory-startup --python arte/blender/fontes/gerar.py -- ui all
# renders de teste numa pasta à parte, sem tocar nos renders oficiais:
# BRASALUME_RAW=<pasta> blender --background --factory-startup --python arte/blender/fontes/gerar.py -- quadros <slug>
python -I arte/blender/fontes/montar_folhas.py tudo
python -I arte/blender/fontes/integrar.py
```

O resultado é 2D: o Blender serve só para gerar imagens; o jogo continua em Canvas 2D e nada de 3D é carregado nele.

Para conferir a arte e o jogo depois de mudar algo (prévia de monstros, render em lote, folhas de antes e depois, medição de fluidez e teste de todas as abas), veja `../ferramentas/README.md`.
