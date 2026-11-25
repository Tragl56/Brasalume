# Ferramentas

Testes do jogo no navegador e conferência da arte. Nada aqui vai ao ar nem é carregado pelo jogo. Rode tudo a partir da raiz do projeto (`E:\RPGjogo`).

## Testar o jogo num navegador sem janela

O Edge sem janela roda o jogo em tempo real e é controlado pelo protocolo de depuração. Não use o painel do navegador escondido para medir, porque ele desacelera os quadros.

1. Sirva o jogo com as páginas de teste:

   ```
   cd jogo
   npm run build
   cd ..
   python -I ferramentas/servidor_teste.py
   ```

   - Por padrão serve o build em `jogo/dist/` na porta 8774.
   - `/__perf.html?z=0&cls=guerreiro&path=baluarte&lv=40&s=12&zoom=1` joga numa região com a vocação escolhida e mostra o relatório depois de `s` segundos. `&dgid=<id da masmorra>` entra numa masmorra.
   - O relatório traz quadros por segundo, quadros lentos, o tempo de cada etapa do desenho (fundo, chão, cena, efeitos e sobreposições), o passo do herói na tela e os erros de script.
2. Abra o Edge sem janela com a porta de depuração:

   ```
   "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --remote-debugging-port=9333 --user-data-dir=<pasta temporária> about:blank
   ```

3. Meça ou confira:

   ```
   node ferramentas/medir.js "http://127.0.0.1:8774/__perf.html?z=4&s=12" 12 9333 captura.png
   node ferramentas/conferir_abas.js http://127.0.0.1:8774 <pasta de saída> 9333
   ```

   - `medir.js` imprime o relatório e, se pedida, grava uma captura da tela. Para comparar uma mudança, mantenha o mesmo cenário e parâmetros, rode pelo menos três medições e compare as médias e p95 por etapa.
   - `conferir_abas.js` semeia um save antigo, clica em cada aba do jogo e grava o texto e uma captura de cada uma, junto com os erros de script.

   Para repetir o perfil completo em dois cenários (três vezes cada), depois de compilar:

   ```
   npm --prefix jogo run perf:loop
   ```

   O resultado é salvo em `arquivo/medidas-loop.txt`.

## Conferir a animação no navegador

- Antes, gere o build com `cd jogo`, `npm run build` e `cd ..`.
- `servidor_anim.py` mostra um monstro de cada família e o quadro que o jogo desenhou em cada momento (`/__quadros.html`). `/__anim.html?z=0` joga numa região e conta os quadros desenhados.
- `servidor_herois.py` faz o mesmo para o herói no mapa (`/__herois.html?de=0&ate=25`, `/__mundo.html?z=0&cls=guerreiro&path=baluarte&lv=40`).

Estas duas páginas precisam de um navegador visível, como o painel do navegador do app. No Edge sem janela, o desenho fica lento demais para contar quadros.

## Arte

- `piloto_monstros.py`: prévia rápida de alguns monstros com a câmera do sprite do jogo, numa pasta à parte, sem tocar nos renders oficiais.

  ```
  blender --background --factory-startup --python ferramentas/piloto_monstros.py -- <pasta> slug1,slug2 [golpe]
  ```

- `rodar_lote.sh <lista.txt> <quadros|monstros> <log> <gpu|cpu>`: renderiza uma lista de monstros (slugs separados por vírgula), um processo do Blender por monstro e com uma nova tentativa, para que uma falha não derrube o resto. Dá para rodar duas filas ao mesmo tempo: uma na placa de vídeo e outra no processador.
- Folhas de conferência (PNG):
  - `folha_monstros.py`: grade com um quadro de cada monstro do jogo.
  - `folha_tiras.py`: as tiras animadas exportadas, uma linha por monstro.
  - `folha_quadros.py`: os quadros brutos do Blender.
  - `comparar_polir.py`: render novo de teste contra o quadro bruto atual.
  - `antes_depois.py`: duas pastas de tiras lado a lado, grandes e no tamanho do jogo, com a mesma gama do jogo.
