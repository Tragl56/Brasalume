/* ----- cenário modelado na Tripo: imagens pré-renderizadas no ângulo do jogo (pasta sprites/); sem elas, vale o desenho antigo ----- */
// dados do estúdio (sprites/sprites.json): tamanho, ponto de apoio no chão (ax, ay) e altura do modelo em pixels (hpx)
const SPRITE_META = /*META*/{}/*META*/;
// peças que usam imagem em cada cenário ('*' vale para todas as regiões) e a altura delas na tela com zoom 1
const SPRITE_USE = {
  trees: {pine: 'pinheiro', round: 'arvore_redonda', bush: 'arbusto', rock: 'pedra'},
  '*': {portal: 'portal', menhir: 'menir'},
};
const SPRITE_H = {pine: 64, round: 54, bush: 19, rock: 16, portal: 62, menhir: 26};
const SPR = {};
function loadSprites(){
  for (const name of Object.keys(SPRITE_META)){
    const img = new Image(), rec = {img, meta: SPRITE_META[name], ok: false};
    img.onload = () => { rec.ok = img.naturalWidth > 0; };
    img.onerror = () => { rec.ok = false; };   // sem a imagem, a peça volta ao desenho feito em código
    img.decoding = 'async'; img.src = 'sprites/' + name + '.png'; SPR[name] = rec;
  }
}
function spriteFor(type, z){
  const name = ((z && SPRITE_USE[z.decor]) || {})[type] || SPRITE_USE['*'][type], rec = name && SPR[name];
  return rec && rec.ok ? rec : null;
}
// desenha a imagem com o ponto de apoio em (x, y) e a altura do modelo igual a hh pixels; flip espelha para variar
function drawSprite(c, rec, x, y, hh, flip){
  const m = rec.meta, k = hh / m.hpx;
  if (flip){ c.save(); c.translate(x, y); c.scale(-1, 1); c.drawImage(rec.img, -m.ax * k, -m.ay * k, m.w * k, m.h * k); c.restore(); }
  else c.drawImage(rec.img, x - m.ax * k, y - m.ay * k, m.w * k, m.h * k);
}
