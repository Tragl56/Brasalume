# Catálogo de arte do Brasalume

Inventário gerado a partir de `../jogo/src/gameEngine.js` por `blender/fontes/extrair_dados.js` e `blender/fontes/catalogo.py`. Não edite as caixas à mão: rode os dois scripts de novo. Uma caixa só fica marcada quando o arquivo existe no caminho descrito em `README.md`.

Resumo do código: 48 classes (4 vocações-base e 44 caminhos), 20 famílias visuais de monstros, 13 regiões, 13 chefes errantes e 15 masmorras.

## Portador (antes da vocação)

| ID | Nome | Conceito | Turnaround | Sprite 2D | Integrado |
|---|---|---:|---:|---:|---:|
| `none` | Portador | ☑ | ☑ | ☑ | ☑ |

## Classes

As vocações-base são o estágio 1. Cada caminho tem quatro estágios; o nome do estágio 2 é o nome usado nas pastas e no visual (`LOOK`).

| ID | Nome | Linhagem | Estágios seguintes | Conceito | Turnaround | Sprite 2D | Integrado |
|---|---|---|---|---:|---:|---:|---:|
| `guerreiro` | Guerreiro | Guerreiro | vocação-base | ☑ | ☑ | ☑ | ☑ |
| `arcanista` | Arcanista | Arcanista | vocação-base | ☑ | ☑ | ☑ | ☑ |
| `batedor` | Batedor | Batedor | vocação-base | ☑ | ☑ | ☑ | ☑ |
| `devoto` | Devoto | Devoto | vocação-base | ☑ | ☑ | ☑ | ☑ |
| `baluarte` | Baluarte | Guerreiro | Guardião de Aço → Mestre do Escudo → Muralha Eterna | ☑ | ☑ | ☑ | ☑ |
| `ceifador` | Ceifador | Guerreiro | Ceifador de Almas → Mestre da Foice → Senhor da Colheita | ☑ | ☑ | ☑ | ☑ |
| `duelista` | Duelista | Guerreiro | Esgrimista → Mestre de Armas → Lâmina Lendária | ☑ | ☑ | ☑ | ☑ |
| `furia` | Fúria Rubra | Guerreiro | Sanguinário → Mestre da Fúria → Tempestade Rubra | ☑ | ☑ | ☑ | ☑ |
| `estandarte` | Porta-Estandarte | Guerreiro | Cavaleiro do Estandarte → Comandante de Guerra → Lenda da Vanguarda | ☑ | ☑ | ☑ | ☑ |
| `quebraescudos` | Quebra-Escudos | Guerreiro | Destruidor de Muralhas → Mestre do Martelo → Arauto do Terremoto | ☑ | ☑ | ☑ | ☑ |
| `campeao` | Campeão do Fosso | Guerreiro | Gladiador Veterano → Mestre da Arena → Campeão Imortal | ☑ | ☑ | ☑ | ☑ |
| `farpada` | Couraça Farpada | Guerreiro | Pele de Espinhos → Mestre dos Espinhos → Colosso Farpado | ☑ | ☑ | ☑ | ☑ |
| `corrente` | Guardião de Corrente | Guerreiro | Carcereiro de Ferro → Senhor dos Grilhões → Tirano das Correntes | ☑ | ☑ | ☑ | ☑ |
| `gemeas` | Lâminas Gêmeas | Guerreiro | Duelista de Aço Duplo → Vendaval de Aço → Tempestade Gêmea | ☑ | ☑ | ☑ | ☑ |
| `brasa` | Cavaleiro de Brasa | Guerreiro | Cavaleiro Incandescente → Guardião da Fornalha → Coração de Magma | ☑ | ☑ | ☑ | ☑ |
| `tecelao` | Piromaníaco | Arcanista | Discípulo do Fogo → Mestre do Fogo → Avatar das Chamas | ☑ | ☑ | ☑ | ☑ |
| `glacial` | Vidente Glacial | Arcanista | Adepto do Gelo → Mestre do Inverno → Avatar do Inverno | ☑ | ☑ | ☑ | ☑ |
| `tempestario` | Tempestário | Arcanista | Discípulo do Trovão → Mestre dos Raios → Avatar da Tempestade | ☑ | ☑ | ☑ | ☑ |
| `ocultista` | Ocultista | Arcanista | Adepto das Sombras → Mestre das Almas → Senhor do Véu | ☑ | ☑ | ☑ | ☑ |
| `geomante` | Geomante | Arcanista | Discípulo da Pedra → Mestre da Terra → Avatar da Montanha | ☑ | ☑ | ☑ | ☑ |
| `escriba` | Escriba Arcano | Arcanista | Adepto das Runas → Arquimago Rúnico → Lenda Rúnica | ☑ | ☑ | ☑ | ☑ |
| `enxame` | Chamador de Fagulhas | Arcanista | Pastor do Enxame → Mestre das Brasas Vivas → Coração do Enxame | ☑ | ☑ | ☑ | ☑ |
| `prismatico` | Prismático | Arcanista | Discípulo da Luz → Mestre dos Prismas → Lenda Prismática | ☑ | ☑ | ☑ | ☑ |
| `relojoeiro` | Relojoeiro Arcano | Arcanista | Mestre das Horas → Senhor do Pêndulo → Guardião do Instante Final | ☑ | ☑ | ☑ | ☑ |
| `espelhos` | Conjurador de Espelhos | Arcanista | Ilusionista de Prata → Senhor dos Reflexos → Mil Faces | ☑ | ☑ | ☑ | ☑ |
| `lunar` | Vidente Lunar | Arcanista | Guardião das Fases → Arauto do Eclipse → Soberano da Lua Cheia | ☑ | ☑ | ☑ | ☑ |
| `elite` | Atirador de Elite | Batedor | Franco-Atirador → Mestre Atirador → Lenda do Arco Longo | ☑ | ☑ | ☑ | ☑ |
| `armadilheiro` | Armadilheiro | Batedor | Caçador de Armadilhas → Mestre das Armadilhas → Lenda da Caçada | ☑ | ☑ | ☑ | ☑ |
| `trilheiro` | Trilheiro | Batedor | Patrulheiro → Mestre da Trilha → Lenda das Trilhas | ☑ | ☑ | ☑ | ☑ |
| `domador` | Domador | Batedor | Irmão dos Lobos → Mestre da Matilha → Alfa da Floresta | ☑ | ☑ | ☑ | ☑ |
| `besteiro` | Besteiro de Cerco | Batedor | Artilheiro → Mestre da Besta → Lenda do Cerco | ☑ | ☑ | ☑ | ☑ |
| `errante` | Sombra Errante | Batedor | Lâmina Oculta → Mestre das Sombras → Lenda das Sombras | ☑ | ☑ | ☑ | ☑ |
| `envenenador` | Envenenador | Batedor | Alquimista das Toxinas → Mestre dos Venenos → Praga Viva | ☑ | ☑ | ☑ | ☑ |
| `polvora` | Artífice da Pólvora | Batedor | Bombardeiro → Mestre da Pólvora → Lenda da Explosão | ☑ | ☑ | ☑ | ☑ |
| `falcoeiro` | Falcoeiro | Batedor | Mestre das Garras → Senhor dos Céus → Rei-Falcão | ☑ | ☑ | ☑ | ☑ |
| `espectral` | Flecheiro Espectral | Batedor | Arqueiro do Véu → Caçador de Almas → Lamento Eterno | ☑ | ☑ | ☑ | ☑ |
| `cacador` | Caçador de Prêmios | Batedor | Rastreador → Caçador de Lendas → Lenda da Fronteira | ☑ | ☑ | ☑ | ☑ |
| `aurora` | Sentinela da Aurora | Devoto | Cavaleiro do Sol → Mestre da Luz Solar → Avatar do Sol | ☑ | ☑ | ☑ | ☑ |
| `herbalista` | Herbalista | Devoto | Guardião do Bosque → Mestre das Raízes → Avatar da Floresta | ☑ | ☑ | ☑ | ☑ |
| `juiz` | Juiz de Cinzas | Devoto | Magistrado das Cinzas → Mestre do Veredito → Juiz Supremo | ☑ | ☑ | ☑ | ☑ |
| `cantor` | Cantor de Hinos | Devoto | Coralista Sagrado → Mestre dos Hinos → Lenda dos Hinos | ☑ | ☑ | ☑ | ☑ |
| `limiar` | Guardião do Limiar | Devoto | Vigia dos Portais → Mestre do Limiar → Senhor dos Portões | ☑ | ☑ | ☑ | ☑ |
| `peregrino` | Peregrino | Devoto | Andarilho Sagrado → Mestre do Caminho → Lenda Andarilha | ☑ | ☑ | ☑ | ☑ |
| `augure` | Áugure das Cinzas | Devoto | Vidente dos Corvos → Mestre dos Presságios → Voz do Destino | ☑ | ☑ | ☑ | ☑ |
| `penitente` | Penitente | Devoto | Flagelante → Mestre da Penitência → Mártir Eterno | ☑ | ☑ | ☑ | ☑ |
| `asceta` | Asceta | Devoto | Punho Tranquilo → Mestre do Silêncio → Iluminado | ☑ | ☑ | ☑ | ☑ |
| `mares` | Clérigo das Marés | Devoto | Voz da Correnteza → Guardião do Recife → Senhor das Profundezas | ☑ | ☑ | ☑ | ☑ |
| `relicario` | Guardião do Relicário | Devoto | Portador de Incenso → Arconte das Relíquias → Santuário Vivo | ☑ | ☑ | ☑ | ☑ |

## Regiões e mapas

| ID | Nome | Níveis | Cenário no código | Conceito do mapa | Assets de cenário | Integrado |
|---|---|---|---|---:|---:|---:|
| `clareira` | Clareira das Cinzas | 1–5 | `trees` | ☑ | ☑ | ☑ |
| `brejo` | Brejo das Lamparinas | 6–12 | `reeds` | ☑ | ☑ | ☑ |
| `pedreira` | Pedreira Sussurrante | 13–21 | `rocks` | ☑ | ☑ | ☑ |
| `bosque` | Bosque Pálido | 22–31 | `pale` | ☑ | ☑ | ☑ |
| `ruinas` | Ruínas de Vidro | 32–42 | `ruins` | ☑ | ☑ | ☑ |
| `dunas` | Dunas de Âmbar | 43–54 | `dunes` | ☑ | ☑ | ☑ |
| `cume` | Cume Gélido | 55–66 | `peaks` | ☑ | ☑ | ☑ |
| `coracao` | Coração Apagado | 67–80 | `void` | ☑ | ☑ | ☑ |
| `breu` | Mar de Breu | 81–90 | `tar` | ☑ | ☑ | ☑ |
| `obsidiana` | Bosque de Obsidiana | 91–100 | `crystals` | ☑ | ☑ | ☑ |
| `afundada` | Cidade Afundada | 101–110 | `city` | ☑ | ☑ | ☑ |
| `fornalha` | Fornalha Antiga | 111–120 | `lava` | ☑ | ☑ | ☑ |
| `aurora` | Limiar da Aurora | 121–130 | `dawn` | ☑ | ☑ | ☑ |

## Masmorras

| ID | Nome | Entrada | Nível | Tema no código | Conceito do mapa | Assets de cenário | Integrado |
|---|---|---|---:|---|---:|---:|---:|
| `raizes` | Covil das Raízes | Clareira das Cinzas | 8 | `roots` | ☑ | ☑ | ☑ |
| `esporos` | Toca dos Esporos | Brejo das Lamparinas | 15 | `fungus` | ☑ | ☑ | ☑ |
| `mina` | Mina Esquecida | Pedreira Sussurrante | 26 | `mine` | ☑ | ☑ | ☑ |
| `catacumba` | Catacumba Sussurrante | Bosque Pálido | 34 | `bones` | ☑ | ☑ | ☑ |
| `biblioteca` | Biblioteca Partida | Ruínas de Vidro | 47 | `library` | ☑ | ☑ | ☑ |
| `colmeia` | Colmeia de Âmbar | Dunas de Âmbar | 57 | `amber` | ☑ | ☑ | ☑ |
| `gruta` | Gruta Congelada | Cume Gélido | 69 | `ice` | ☑ | ☑ | ☑ |
| `abismo` | Abismo do Eco | Coração Apagado | 84 | `abyss` | ☑ | ☑ | ☑ |
| `naufragio` | Naufrágio Profundo | Mar de Breu | 93 | `wreck` | ☑ | ☑ | ☑ |
| `ninho` | Ninho Espelhado | Bosque de Obsidiana | 105 | `mirror` | ☑ | ☑ | ☑ |
| `cofre` | Cofre do Arquiduque | Cidade Afundada | 114 | `vault` | ☑ | ☑ | ☑ |
| `forja` | Coração da Forja | Fornalha Antiga | 125 | `forge` | ☑ | ☑ | ☑ |
| `trono` | Trono do Crepúsculo | Limiar da Aurora | 128 | `throne` | ☑ | ☑ | ☑ |
| `pin_portador` | Eco do Primeiro Portador | Limiar da Aurora | 200 | `throne` | ☐ | ☐ | ☐ |
| `pin_fome` | Ventre da Fome | Limiar da Aurora | 500 | `abyss` | ☐ | ☐ | ☐ |

## Monstros comuns das regiões

| Nome | Família visual | Onde aparece | Conceito 2D | Sprite 2D | Integrado |
|---|---|---|---:|---:|---:|
| Brotinho de Musgo | `blob` | Clareira das Cinzas | ☑ | ☑ | ☑ |
| Mariposa de Fuligem | `flyer` | Clareira das Cinzas | ☑ | ☑ | ☑ |
| Javali Fumê | `beast` | Clareira das Cinzas | ☑ | ☑ | ☑ |
| Cogumelo Saltitante | `mushroom` | Clareira das Cinzas | ☑ | ☑ | ☑ |
| Sapo-Lampião | `blob` | Brejo das Lamparinas | ☑ | ☑ | ☑ |
| Lodo Errante | `blob` | Brejo das Lamparinas | ☑ | ☑ | ☑ |
| Vagalume Faminto | `flyer` | Brejo das Lamparinas | ☑ | ☑ | ☑ |
| Planta Engolidora | `plant` | Brejo das Lamparinas | ☑ | ☑ | ☑ |
| Golem de Cascalho | `golem` | Pedreira Sussurrante | ☑ | ☑ | ☑ |
| Morcego de Quartzo | `flyer` | Pedreira Sussurrante | ☑ | ☑ | ☑ |
| Escavador Cego | `beast` | Pedreira Sussurrante | ☑ | ☑ | ☑ |
| Caranguejo de Cascalho | `crab` | Pedreira Sussurrante | ☑ | ☑ | ☑ |
| Lobo de Névoa | `beast` | Bosque Pálido | ☑ | ☑ | ☑ |
| Espectro de Galho | `wisp` | Bosque Pálido | ☑ | ☑ | ☑ |
| Corvo Agourento | `flyer` | Bosque Pálido | ☑ | ☑ | ☑ |
| Olho da Névoa | `eye` | Bosque Pálido | ☑ | ☑ | ☑ |
| Sentinela de Vitral | `knight` | Ruínas de Vidro | ☑ | ☑ | ☑ |
| Serpente Prismática | `serpent` | Ruínas de Vidro | ☑ | ☑ | ☑ |
| Eco Quebrado | `wisp` | Ruínas de Vidro | ☑ | ☑ | ☑ |
| Esqueleto de Vitral | `skeleton` | Ruínas de Vidro | ☑ | ☑ | ☑ |
| Escorpião de Âmbar | `beast` | Dunas de Âmbar | ☑ | ☑ | ☑ |
| Djinn de Areia | `wisp` | Dunas de Âmbar | ☑ | ☑ | ☑ |
| Besouro Solar | `flyer` | Dunas de Âmbar | ☑ | ☑ | ☑ |
| Diabrete de Areia | `imp` | Dunas de Âmbar | ☑ | ☑ | ☑ |
| Yeti Errante | `golem` | Cume Gélido | ☑ | ☑ | ☑ |
| Espírito da Nevasca | `wisp` | Cume Gélido | ☑ | ☑ | ☑ |
| Lince de Gelo | `beast` | Cume Gélido | ☑ | ☑ | ☑ |
| Caranguejo de Gelo | `crab` | Cume Gélido | ☑ | ☑ | ☑ |
| Sombra Faminta | `wisp` | Coração Apagado | ☑ | ☑ | ☑ |
| Cavaleiro Oco | `knight` | Coração Apagado | ☑ | ☑ | ☑ |
| Fogo-Fátuo Negro | `flyer` | Coração Apagado | ☑ | ☑ | ☑ |
| Olho Vazio | `eye` | Coração Apagado | ☑ | ☑ | ☑ |
| Enguia de Breu | `serpent` | Mar de Breu | ☑ | ☑ | ☑ |
| Marinheiro Afogado | `knight` | Mar de Breu | ☑ | ☑ | ☑ |
| Medusa de Piche | `jelly` | Mar de Breu | ☑ | ☑ | ☑ |
| Caranguejo de Piche | `crab` | Mar de Breu | ☑ | ☑ | ☑ |
| Aranha de Obsidiana | `spider` | Bosque de Obsidiana | ☑ | ☑ | ☑ |
| Golem Espelhado | `golem` | Bosque de Obsidiana | ☑ | ☑ | ☑ |
| Fada Partida | `wisp` | Bosque de Obsidiana | ☑ | ☑ | ☑ |
| Cogumelo Cristalino | `mushroom` | Bosque de Obsidiana | ☑ | ☑ | ☑ |
| Guarda Afogado | `knight` | Cidade Afundada | ☑ | ☑ | ☑ |
| Polvo de Lama | `blob` | Cidade Afundada | ☑ | ☑ | ☑ |
| Medusa-Lanterna | `jelly` | Cidade Afundada | ☑ | ☑ | ☑ |
| Esqueleto Afogado | `skeleton` | Cidade Afundada | ☑ | ☑ | ☑ |
| Salamandra de Escória | `serpent` | Fornalha Antiga | ☑ | ☑ | ☑ |
| Forjador de Cinzas | `golem` | Fornalha Antiga | ☑ | ☑ | ☑ |
| Fagulha Rebelde | `wisp` | Fornalha Antiga | ☑ | ☑ | ☑ |
| Diabrete de Brasa | `imp` | Fornalha Antiga | ☑ | ☑ | ☑ |
| Eco da Primeira Luz | `wisp` | Limiar da Aurora | ☑ | ☑ | ☑ |
| Sentinela Dourada | `knight` | Limiar da Aurora | ☑ | ☑ | ☑ |
| Cervo de Luz | `beast` | Limiar da Aurora | ☑ | ☑ | ☑ |
| Planta da Alvorada | `plant` | Limiar da Aurora | ☑ | ☑ | ☑ |

## Chefes de região

| Nome | Família visual | Onde aparece | Conceito 2D | Sprite 2D | Integrado |
|---|---|---|---:|---:|---:|
| Rainha-Musgo Antiga | `blob` | Clareira das Cinzas | ☑ | ☑ | ☑ |
| Velho Sapo do Lodo | `blob` | Brejo das Lamparinas | ☑ | ☑ | ☑ |
| Colosso de Granito | `golem` | Pedreira Sussurrante | ☑ | ☑ | ☑ |
| Alfa da Névoa | `beast` | Bosque Pálido | ☑ | ☑ | ☑ |
| Guardião Estilhaçado | `knight` | Ruínas de Vidro | ☑ | ☑ | ☑ |
| Imperatriz Escaravelho | `golem` | Dunas de Âmbar | ☑ | ☑ | ☑ |
| Wyrm do Inverno | `serpent` | Cume Gélido | ☑ | ☑ | ☑ |
| O Apagador | `knight` | Coração Apagado | ☑ | ☑ | ☑ |
| Leviatã de Piche | `serpent` | Mar de Breu | ☑ | ☑ | ☑ |
| Rainha Tecelã | `spider` | Bosque de Obsidiana | ☑ | ☑ | ☑ |
| Arquiduque Afogado | `knight` | Cidade Afundada | ☑ | ☑ | ☑ |
| O Primeiro Ferreiro | `golem` | Fornalha Antiga | ☑ | ☑ | ☑ |
| A Noite Que Resta | `wisp` | Limiar da Aurora | ☑ | ☑ | ☑ |

## Chefes errantes

| Nome | Família visual | Onde aparece | Conceito 2D | Sprite 2D | Integrado |
|---|---|---|---:|---:|---:|
| Javali Rei da Fuligem | `beast` | Clareira das Cinzas | ☑ | ☑ | ☑ |
| Mãe-Lodo | `blob` | Brejo das Lamparinas | ☑ | ☑ | ☑ |
| Morcego Ancião de Quartzo | `flyer` | Pedreira Sussurrante | ☑ | ☑ | ☑ |
| Corvo das Mil Penas | `flyer` | Bosque Pálido | ☑ | ☑ | ☑ |
| Serpente de Vitral | `serpent` | Ruínas de Vidro | ☑ | ☑ | ☑ |
| Djinn do Simum | `wisp` | Dunas de Âmbar | ☑ | ☑ | ☑ |
| Lince Branco Ancestral | `beast` | Cume Gélido | ☑ | ☑ | ☑ |
| Cavaleiro Sem Nome | `knight` | Coração Apagado | ☑ | ☑ | ☑ |
| Medusa Rainha | `jelly` | Mar de Breu | ☑ | ☑ | ☑ |
| Viúva de Vidro | `spider` | Bosque de Obsidiana | ☑ | ☑ | ☑ |
| Colosso Coralino | `golem` | Cidade Afundada | ☑ | ☑ | ☑ |
| Salamandra Imperatriz | `serpent` | Fornalha Antiga | ☑ | ☑ | ☑ |
| Arauto do Crepúsculo | `knight` | Limiar da Aurora | ☑ | ☑ | ☑ |

## Monstros de masmorra

Alguns nomes repetem monstros das regiões; a arte pode ser a mesma, com a pasta da família visual.

| Nome | Família visual | Onde aparece | Conceito 2D | Sprite 2D | Integrado |
|---|---|---|---:|---:|---:|
| Broto Raivoso | `plant` | Covil das Raízes | ☑ | ☑ | ☑ |
| Besouro de Casca | `crab` | Covil das Raízes | ☑ | ☑ | ☑ |
| Cogumelo Saltitante | `mushroom` | Covil das Raízes | ☑ | ☑ | ☑ |
| Cogumelo Venenoso | `mushroom` | Toca dos Esporos | ☑ | ☑ | ☑ |
| Lodo de Caverna | `blob` | Toca dos Esporos | ☑ | ☑ | ☑ |
| Golem de Carvão | `golem` | Mina Esquecida | ☑ | ☑ | ☑ |
| Morcego de Mina | `flyer` | Mina Esquecida | ☑ | ☑ | ☑ |
| Verme de Cascalho | `worm` | Mina Esquecida | ☑ | ☑ | ☑ |
| Esqueleto Vigia | `skeleton` | Catacumba Sussurrante | ☑ | ☑ | ☑ |
| Olho da Cripta | `eye` | Catacumba Sussurrante | ☑ | ☑ | ☑ |
| Morcego Ossudo | `flyer` | Catacumba Sussurrante | ☑ | ☑ | ☑ |
| Livro Mordedor | `tome` | Biblioteca Partida | ☑ | ☑ | ☑ |
| Sentinela de Leitura | `knight` | Biblioteca Partida | ☑ | ☑ | ☑ |
| Olho Bibliotecário | `eye` | Biblioteca Partida | ☑ | ☑ | ☑ |
| Diabrete de Areia | `imp` | Colmeia de Âmbar | ☑ | ☑ | ☑ |
| Zangão de Âmbar | `flyer` | Colmeia de Âmbar | ☑ | ☑ | ☑ |
| Planta Melífera | `plant` | Colmeia de Âmbar | ☑ | ☑ | ☑ |
| Caranguejo de Gelo | `crab` | Gruta Congelada | ☑ | ☑ | ☑ |
| Olho Gélido | `eye` | Gruta Congelada | ☑ | ☑ | ☑ |
| Espírito do Degelo | `wisp` | Gruta Congelada | ☑ | ☑ | ☑ |
| Boca do Vazio | `maw` | Abismo do Eco | ☑ | ☑ | ☑ |
| Cavaleiro Oco | `knight` | Abismo do Eco | ☑ | ☑ | ☑ |
| Olho Vazio | `eye` | Abismo do Eco | ☑ | ☑ | ☑ |
| Caranguejo de Piche | `crab` | Naufrágio Profundo | ☑ | ☑ | ☑ |
| Esqueleto Marujo | `skeleton` | Naufrágio Profundo | ☑ | ☑ | ☑ |
| Medusa das Profundezas | `jelly` | Naufrágio Profundo | ☑ | ☑ | ☑ |
| Aranha de Obsidiana | `spider` | Ninho Espelhado | ☑ | ☑ | ☑ |
| Golem Espelhado | `golem` | Ninho Espelhado | ☑ | ☑ | ☑ |
| Livro de Vidro | `tome` | Ninho Espelhado | ☑ | ☑ | ☑ |
| Baú Mímico | `mimic` | Cofre do Arquiduque | ☑ | ☑ | ☑ |
| Guarda do Cofre | `knight` | Cofre do Arquiduque | ☑ | ☑ | ☑ |
| Olho do Tesouro | `eye` | Cofre do Arquiduque | ☑ | ☑ | ☑ |
| Diabrete de Brasa | `imp` | Coração da Forja | ☑ | ☑ | ☑ |
| Forjador de Cinzas | `golem` | Coração da Forja | ☑ | ☑ | ☑ |
| Salamandra Menor | `serpent` | Coração da Forja | ☑ | ☑ | ☑ |
| Sentinela Dourada | `knight` | Trono do Crepúsculo | ☑ | ☑ | ☑ |
| Eco da Primeira Luz | `wisp` | Trono do Crepúsculo | ☑ | ☑ | ☑ |
| Boca do Crepúsculo | `maw` | Trono do Crepúsculo | ☑ | ☑ | ☑ |
| Sombra de Portador | `knight` | Eco do Primeiro Portador | ☐ | ☐ | ☐ |
| Lanterna Partida | `wisp` | Eco do Primeiro Portador | ☐ | ☐ | ☐ |
| Devorador Menor | `maw` | Ventre da Fome | ☐ | ☐ | ☐ |

## Subchefes de masmorra

| Nome | Família visual | Onde aparece | Conceito 2D | Sprite 2D | Integrado |
|---|---|---|---:|---:|---:|
| Toco Ranzinza | `treant` | Covil das Raízes | ☑ | ☑ | ☑ |
| Cogumelo Guardião | `mushroom` | Toca dos Esporos | ☑ | ☑ | ☑ |
| Capataz de Pedra | `golem` | Mina Esquecida | ☑ | ☑ | ☑ |
| Arauto Ossudo | `skeleton` | Catacumba Sussurrante | ☑ | ☑ | ☑ |
| Bibliotecária de Vitral | `wisp` | Biblioteca Partida | ☑ | ☑ | ☑ |
| Guarda da Colmeia | `imp` | Colmeia de Âmbar | ☑ | ☑ | ☑ |
| Sentinela de Gelo | `golem` | Gruta Congelada | ☑ | ☑ | ☑ |
| Carcereiro Oco | `knight` | Abismo do Eco | ☑ | ☑ | ☑ |
| Imediato Afogado | `knight` | Naufrágio Profundo | ☑ | ☑ | ☑ |
| Sentinela Espelhada | `golem` | Ninho Espelhado | ☑ | ☑ | ☑ |
| Mímico Ancião | `mimic` | Cofre do Arquiduque | ☑ | ☑ | ☑ |
| Capataz da Forja | `golem` | Coração da Forja | ☑ | ☑ | ☑ |
| Guarda do Crepúsculo | `knight` | Trono do Crepúsculo | ☑ | ☑ | ☑ |
| Guardião das Cinzas | `knight` | Eco do Primeiro Portador | ☐ | ☐ | ☐ |
| Arauto da Fome | `maw` | Ventre da Fome | ☐ | ☐ | ☐ |

## Chefes de masmorra

| Nome | Família visual | Onde aparece | Conceito 2D | Sprite 2D | Integrado |
|---|---|---|---:|---:|---:|
| Avó-Raiz | `treant` | Covil das Raízes | ☑ | ☑ | ☑ |
| Mãe-Esporo | `plant` | Toca dos Esporos | ☑ | ☑ | ☑ |
| Verme Devorador | `worm` | Mina Esquecida | ☑ | ☑ | ☑ |
| Rei das Catacumbas | `skeleton` | Catacumba Sussurrante | ☑ | ☑ | ☑ |
| Grimório Desperto | `tome` | Biblioteca Partida | ☑ | ☑ | ☑ |
| Rainha-Colmeia | `imp` | Colmeia de Âmbar | ☑ | ☑ | ☑ |
| Caranguejo Rei de Gelo | `crab` | Gruta Congelada | ☑ | ☑ | ☑ |
| Devorador de Ecos | `maw` | Abismo do Eco | ☑ | ☑ | ☑ |
| Capitão Afogado | `skeleton` | Naufrágio Profundo | ☑ | ☑ | ☑ |
| Matriarca de Obsidiana | `spider` | Ninho Espelhado | ☑ | ☑ | ☑ |
| Mímico Dourado | `mimic` | Cofre do Arquiduque | ☑ | ☑ | ☑ |
| Ferreiro de Cinzas | `golem` | Coração da Forja | ☑ | ☑ | ☑ |
| O Rei Sem Aurora | `knight` | Trono do Crepúsculo | ☑ | ☑ | ☑ |
| O Primeiro Portador | `knight` | Eco do Primeiro Portador | ☐ | ☐ | ☐ |
| A Fome Sem Forma | `maw` | Ventre da Fome | ☐ | ☐ | ☐ |

## Famílias visuais (`KINDS`)

Cada família tem uma pasta em `inimigos/monstros/<família>/`. Entradas da mesma família podem partir da mesma base, mas cada uma precisa continuar distinguível.

| Família | Inimigos que usam |
|---|---:|
| `blob` | 8 |
| `flyer` | 11 |
| `beast` | 9 |
| `golem` | 14 |
| `wisp` | 13 |
| `serpent` | 8 |
| `knight` | 19 |
| `jelly` | 4 |
| `spider` | 4 |
| `mushroom` | 4 |
| `skeleton` | 7 |
| `imp` | 4 |
| `plant` | 5 |
| `crab` | 5 |
| `eye` | 6 |
| `mimic` | 3 |
| `treant` | 2 |
| `worm` | 2 |
| `tome` | 3 |
| `maw` | 6 |
