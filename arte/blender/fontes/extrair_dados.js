// Extrai do motor do jogo (jogo/src/gameEngine.js) as tabelas que a arte usa e grava dados_jogo.json.
// Não executa o jogo: recorta só as declarações de dados e as avalia isoladas.
// Uso: node extrair_dados.js
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const RAIZ = path.resolve(__dirname, '..', '..', '..');
const src = fs.readFileSync(path.join(RAIZ, 'jogo', 'src', 'gameEngine.js'), 'utf8');

// acha o fim do literal que começa em src[i] ('{', '[' ou '('), respeitando strings e comentários
function fimDoBloco(s, i){
  const abre = s[i], fecha = {'{': '}', '[': ']', '(': ')'}[abre];
  let d = 0;
  for (let k = i; k < s.length; k++){
    const ch = s[k];
    if (ch === '"' || ch === "'" || ch === '`'){ const q = ch; k++; while (k < s.length && s[k] !== q){ if (s[k] === '\\') k++; k++; } continue; }
    if (ch === '/' && s[k + 1] === '/'){ while (k < s.length && s[k] !== '\n') k++; continue; }
    if (ch === '/' && s[k + 1] === '*'){ k = s.indexOf('*/', k + 2) + 1; continue; }
    if (ch === '{' || ch === '[' || ch === '('){ d++; continue; }
    if (ch === '}' || ch === ']' || ch === ')'){ d--; if (d === 0) return k; }
  }
  throw new Error('bloco sem fim a partir de ' + i);
}
const ctx = vm.createContext({});
const avaliar = txt => vm.runInContext('(' + txt + ')', ctx);
function literal(nome){
  const m = new RegExp('\\bconst ' + nome + '\\s*=\\s*').exec(src); if (!m) return undefined;
  const i = m.index + m[0].length; return avaliar(src.slice(i, fimDoBloco(src, i) + 1));
}
// todos os Object.assign(ALVO, {...}) do código: devolve o texto de cada objeto {...}
function assigns(alvo){
  const out = [], re = new RegExp('Object\\.assign\\(' + alvo + '\\s*,\\s*\\{', 'g'); let m;
  while ((m = re.exec(src))){ const i = m.index + m[0].length - 1, f = fimDoBloco(src, i); out.push(src.slice(i, f + 1)); re.lastIndex = f; }
  return out;
}
// todos os ALVO.push(...) do código: devolve o texto dos argumentos
function pushes(alvo){
  const out = [], re = new RegExp('\\b' + alvo + '\\.push\\(', 'g'); let m;
  while ((m = re.exec(src))){ const i = m.index + m[0].length - 1, f = fimDoBloco(src, i); out.push(src.slice(i + 1, f)); re.lastIndex = f; }
  return out;
}

const dados = {};
for (const n of ['ARCH', 'CLASSES', 'KINDS', 'ZONES', 'FIELD_BOSSES', 'EXTRA_MOBS', 'DUNGEONS', 'BODY', 'LOOK', 'GROUND', 'FOLIAGE', 'PROP_SET']) dados[n] = literal(n);
for (const alvo of ['KINDS', 'LOOK', 'BODY', 'CLASSES']) for (const t of assigns(alvo)) Object.assign(dados[alvo], avaliar(t));
for (const a of pushes('DUNGEONS')) dados.DUNGEONS.push(...avaliar('[' + a + ']'));
// o jogo acrescenta um quarto monstro a cada região
for (const z of dados.ZONES) if (dados.EXTRA_MOBS && dados.EXTRA_MOBS[z.id]) z.mobs.push(dados.EXTRA_MOBS[z.id]);
// nome de cada classe, no formato antigo (nome) ou no novo, com estágios (tiers)
dados.CLASS_NAMES = {};
for (const [id, c] of Object.entries(dados.CLASSES || {})) dados.CLASS_NAMES[id] = c.nome || (c.tiers && c.tiers[0] && c.tiers[0].nome) || id;
const destino = path.join(__dirname, 'dados_jogo.json');
fs.writeFileSync(destino, JSON.stringify(dados, null, 1));
const n = k => dados[k] ? Object.keys(dados[k]).length : 0;
console.log('ok', destino, 'classes', n('CLASSES'), 'looks', n('LOOK'), 'kinds', n('KINDS'), 'zonas', dados.ZONES.length, 'masmorras', dados.DUNGEONS.length,
  'errantes', n('FIELD_BOSSES'), 'ground', n('GROUND'), 'props', n('PROP_SET'));
