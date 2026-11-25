# Servidor de teste da animação dos monstros: entrega jogo/dist/ e duas páginas extras.
#  /__quadros.html     um monstro de cada família: os 6 quadros do ciclo (tempos escolhidos), parado e golpe,
#                      desenhados pelo drawMonster do próprio jogo; embaixo de cada um, o quadro que o jogo usou (lido no drawImage)
#  /__anim.html?z=0    joga numa região e conta quais quadros de cada monstro o jogo desenhou (andando, parado, golpe)
import http.server, socketserver, sys, functools, json, os
# Uso (na raiz do projeto): python -I ferramentas/servidor_anim.py [pasta_do_jogo] [porta] [pasta_fontes]
AQUI = os.path.dirname(os.path.abspath(__file__))
PROJETO = os.path.dirname(AQUI)   # E:\RPGjogo
RAIZ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJETO, 'jogo', 'dist')
PORTA = int(sys.argv[2]) if len(sys.argv) > 2 else 8772
FONTES = sys.argv[3] if len(sys.argv) > 3 else os.path.join(PROJETO, 'arte', 'blender', 'fontes')
sys.path.insert(0, FONTES)
import montar_folhas as MF
lista = [{'nome': n, 'kind': k, 'cor': c, 'papel': p or 'comum'} for (s, n, k, c, p), _ in MF.lista_inimigos()]
lista.sort(key=lambda e: (e['kind'], e['papel'] != 'comum', e['nome']))
um = {}
for e in lista:
    um.setdefault(e['kind'], e)
FAMILIAS = list(um.values())
QUADROS = ("""<!doctype html><meta charset=utf-8><style>body{margin:0;background:#101a15}</style>
<canvas id=c width=1250 height=%d></canvas>
<iframe id=f src="jogar_local.html" width=40 height=40 style="position:absolute;left:-60px;top:0"></iframe>
<pre id=r style="color:#ccc;font:12px monospace"></pre>
<script>
const LISTA = %s;
const CICLO = {flyer: .55, imp: .5, wisp: 1.4, jelly: 1.7, eye: 1.5, tome: .9, maw: 1.1, blob: 1.3, plant: 1.8, worm: 1.8, serpent: 1.6, treant: 2.4, mushroom: .9};
const f = document.getElementById('f'), cv = document.getElementById('c'), c = cv.getContext('2d');
let ult = null; const orig = c.drawImage.bind(c);
c.drawImage = function(img, sx, sy, sw){ if (arguments.length === 9 && /inimigo_/.test(img.src || '')) ult = Math.round(sx / sw); return orig.apply(null, arguments); };
function desenha(dbg){
  c.fillStyle = '#1b2b25'; c.fillRect(0, 0, cv.width, cv.height);
  const cw = 118, ch = 112; const erros = [];
  LISTA.forEach((e, r) => {
    const y = r * ch + ch - 22, ciclo = CICLO[e.kind];
    c.fillStyle = '#e6dcc4'; c.font = '11px sans-serif'; c.textAlign = 'left'; c.fillText(e.nome.slice(0, 20), 4, y - 30); c.fillStyle = '#f0a23f'; c.fillText(e.kind + (ciclo ? ' (sempre)' : ' (ao andar)'), 4, y - 16);
    for (let j = 0; j < 8; j++){
      const m = {nome: e.nome, kind: e.kind, cor: e.cor, boss: false, appear: 1, face: 1, walkPh: 0, wa: j < 6 ? 1 : 0, mv: j < 6 ? 1 : 0, kb: 0,
        slowT: 0, markT: 0, stunT: 0, dots: [], hp: 1, mhp: 1, awake: true, ph: 1};
      const T = j < 6 ? (ciclo || .8) * (j + .5) / 6 : .3, golpe = j === 7;
      dbg.run.monLunge = golpe ? 1 : 0; ult = null;
      const x = 150 + j * cw + cw / 2;
      dbg.drawMonster(c, m, x, y, .5, T, 0, golpe);
      const esperado = j < 6 ? (j + 1) %% 6 : j === 6 ? (ciclo ? Math.floor(.3 / ciclo * 6 + 1) %% 6 : 0) : 6;
      c.fillStyle = ult === esperado ? '#9fd39a' : '#ff7b6b'; c.textAlign = 'center';
      c.fillText((j < 6 ? 'ciclo' : j === 6 ? 'parado' : 'golpe') + ' q=' + ult, x, y + 14);
      if (ult !== esperado) erros.push(e.nome + ' j' + j + ' q=' + ult + ' esperado ' + esperado);
    }
  });
  dbg.run.monLunge = 0;
  return erros;
}
f.addEventListener('load', () => {
  const dbg = f.contentWindow.brasalumeDebug;
  desenha(dbg);
  setTimeout(() => { const er = desenha(dbg); document.getElementById('r').textContent = 'familias ' + LISTA.length + ' | divergencias: ' + er.length + '\\n' + er.join('\\n'); }, 5000);
});
</script>""" % (len(FAMILIAS) * 112 + 10, json.dumps(FAMILIAS, ensure_ascii=False))).encode('utf-8')
ANIM = b"""<!doctype html><meta charset=utf-8><body style="margin:0;background:#000">
<pre id=r style="position:absolute;left:0;top:0;z-index:2;margin:0;padding:6px;background:rgba(0,0,0,.72);color:#e6dcc4;font:13px monospace"></pre>
<script>
const P = new URLSearchParams(location.search), z = +(P.get('z') || 0), agora = Date.now();
localStorage.setItem('brasalume.save.v1', JSON.stringify({v: 1, created: agora, hero: {lv: +(P.get('lv') || 40), xp: 0, pts: 0,
  stats: {FOR: 260, VIG: 260, INT: 5, ESP: 5, DES: 60}, arch: 'guerreiro', classes: ['guerreiro', 'baluarte'], path: 'baluarte'},
  gold: 0, cinzas: 0, perks: {}, zone: z, unlocked: 12, cleared: [0,1,2,3,4,5,6,7,8,9,10,11], kills: {}, inv: [], equip: {},
  auto: {dist: true, equip: true, sell: 0, boss: false, advance: false, dungeon: P.get('dg') === '1'}, stats: {}, log: [], savedAt: agora, lastSeen: agora}));
localStorage.setItem('brasalume.opts', JSON.stringify({zoom: +(P.get('zoom') || 1), mute: true}));
const f = document.createElement('iframe'); f.src = 'jogar_local.html'; f.width = 1280; f.height = 860; f.style.border = '0'; document.body.appendChild(f);
setInterval(() => { try { f.contentWindow.brasalumeDebug.run.cam = null; } catch (e) {} }, 200);
const vistos = {}, trocas = {};
f.addEventListener('load', () => {
  const W = f.contentWindow, proto = W.CanvasRenderingContext2D.prototype, orig = proto.drawImage;
  proto.drawImage = function(img, sx, sy, sw){
    if (arguments.length === 9 && img && /inimigo_/.test(img.src || '')){
      const nome = img.src.split('/').pop().replace('.png', ''), q = Math.round(sx / sw), v = vistos[nome] || (vistos[nome] = {});
      v[q] = (v[q] || 0) + 1;
    }
    return orig.apply(this, arguments);
  };
  const fim = +(P.get('ms') || 9000);
  setTimeout(() => {
    const linhas = Object.keys(vistos).sort().map(n => n.padEnd(34) + Object.keys(vistos[n]).map(q => (q == 6 ? 'GOLPE' : 'q' + q) + ':' + vistos[n][q]).join(' '));
    document.getElementById('r').textContent = 'regiao ' + z + ' | sprites de monstro desenhados: ' + linhas.length + '\\n' + linhas.join('\\n');
  }, fim);
});
</script>"""
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        pag = QUADROS if self.path.startswith('/__quadros.html') else ANIM if self.path.startswith('/__anim.html') else None
        if pag is not None:
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers(); self.wfile.write(pag); return
        return super().do_GET()
    def log_message(self, *a):
        pass
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORTA), functools.partial(H, directory=RAIZ)) as s:
    s.serve_forever()
