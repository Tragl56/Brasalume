# Servidor de teste do herói no mapa: entrega jogo/dist/ e páginas extras.
#  /__herois.html?de=0&ate=25   cada vocação: desenho em código (parado e estágio 5), sprite parado, 6 quadros do passo, golpe,
#                               sprite no estágio 5 e os dois sobrepostos; embaixo, o quadro que o jogo usou (lido no drawImage)
#  /__mundo.html?z=0&cls=guerreiro&path=baluarte&lv=40   joga numa região com a vocação escolhida e conta os quadros do herói
import http.server, socketserver, sys, functools, json, os
# Uso (na raiz do projeto): python -I ferramentas/servidor_herois.py [pasta_do_jogo] [porta] [pasta_fontes]
AQUI = os.path.dirname(os.path.abspath(__file__))
PROJETO = os.path.dirname(AQUI)   # E:\RPGjogo
RAIZ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJETO, 'jogo', 'dist')
PORTA = int(sys.argv[2]) if len(sys.argv) > 2 else 8773
FONTES = sys.argv[3] if len(sys.argv) > 3 else os.path.join(PROJETO, 'arte', 'blender', 'fontes')
D = json.load(open(os.path.join(FONTES, 'dados_jogo.json'), encoding='utf-8'))
IDS = ['none'] + list(D['CLASSES'])
HEROIS = ("""<!doctype html><meta charset=utf-8><style>body{margin:0;background:#101a15}</style>
<canvas id=c width=1250 height=100></canvas>
<iframe id=f src="jogar_local.html" width=40 height=40 style="position:absolute;left:-60px;top:0"></iframe>
<pre id=r style="color:#ccc;font:12px monospace"></pre>
<script>
const IDS = %s, P = new URLSearchParams(location.search), LISTA = IDS.slice(+(P.get('de') || 0), +(P.get('ate') || IDS.length));
const f = document.getElementById('f'), cv = document.getElementById('c'), c = cv.getContext('2d');
const cw = 100, ch = 128, COLS = ['código', 'código e5', 'sprite', 'passo 0', 'passo 1', 'passo 2', 'passo 3', 'passo 4', 'passo 5', 'golpe', 'sprite e5', 'juntos'];
cv.height = LISTA.length * ch + 30;
let ult = null; const orig = c.drawImage.bind(c);
c.drawImage = function(img, sx, sy, sw){ if (arguments.length === 9 && /heroi_mapa_/.test(img.src || '')) ult = Math.round(sx / sw); return orig.apply(null, arguments); };
function desenha(dbg){
  c.fillStyle = '#1b2b25'; c.fillRect(0, 0, cv.width, cv.height);
  c.fillStyle = '#f0a23f'; c.font = '11px sans-serif'; c.textAlign = 'center';
  COLS.forEach((t, j) => c.fillText(t, 130 + j * cw + cw / 2, 14));
  const erros = []; let comArte = 0;
  LISTA.forEach((id, r) => {
    const L = dbg.LOOK[id] || dbg.LOOK.none, rec = dbg.heroSprite(id), y = 30 + r * ch + ch - 16, s = 1;
    c.fillStyle = '#e6dcc4'; c.textAlign = 'left'; c.fillText(id, 6, y - 50); c.fillStyle = rec ? '#9fd39a' : '#ff7b6b'; c.fillText(rec ? 'com arte' : 'sem arte', 6, y - 36);
    if (rec) comArte++;
    for (let j = 0; j < COLS.length; j++){
      const x = 130 + j * cw + cw / 2; c.save(); c.translate(x, y); ult = null;
      const o = {tier: (j === 1 || j === 10) ? 5 : 0, walkAmp: 0, walkPh: 0, lunge: 0};
      let esperado = null;
      if (j >= 3 && j <= 8){ o.walkAmp = 1; o.walkPh = (j - 3 + .5) / 6 * Math.PI * 2; esperado = j - 3; }
      if (j === 9){ o.lunge = 1; esperado = 6; }
      if (j === 2 || j === 10) esperado = 0;
      if (j <= 1) dbg.drawHeroLook(c, L, s, 1.2, o);
      else if (j === 11){ dbg.drawHeroLook(c, L, s, 1.2, o); if (rec){ c.globalAlpha = .55; dbg.drawHeroSprite(c, L, rec, s, 1.2, o); } }
      else if (rec) dbg.drawHeroSprite(c, L, rec, s, 1.2, o);
      c.restore();
      if (rec && esperado !== null){
        c.fillStyle = ult === esperado ? '#9fd39a' : '#ff7b6b'; c.textAlign = 'center'; c.fillText('q=' + ult, x, y + 12);
        if (ult !== esperado) erros.push(id + ' ' + COLS[j] + ' q=' + ult + ' esperado ' + esperado);
      }
    }
  });
  return [comArte, erros];
}
f.addEventListener('load', () => {
  const dbg = f.contentWindow.brasalumeDebug;
  desenha(dbg);
  setTimeout(() => { const [n, er] = desenha(dbg); document.getElementById('r').textContent = 'vocações ' + LISTA.length + ' | com arte ' + n + ' | divergências: ' + er.length + String.fromCharCode(10) + er.join(String.fromCharCode(10)); }, 5000);
});
</script>""" % json.dumps(IDS)).encode('utf-8')
MUNDO = b"""<!doctype html><meta charset=utf-8><body style="margin:0;background:#000">
<pre id=r style="position:absolute;left:0;top:0;z-index:2;margin:0;padding:6px;background:rgba(0,0,0,.72);color:#e6dcc4;font:13px monospace"></pre>
<script>
const P = new URLSearchParams(location.search), z = +(P.get('z') || 0), agora = Date.now(), cls = P.get('cls') || 'guerreiro', path = P.get('path') || null;
localStorage.setItem('brasalume.save.v1', JSON.stringify({v: 1, created: agora, hero: {lv: +(P.get('lv') || 40), xp: 0, pts: 0,
  stats: {FOR: 260, VIG: 260, INT: 60, ESP: 60, DES: 60}, arch: cls, classes: path ? [cls, path] : [cls], path: path},
  gold: 0, cinzas: 0, perks: {}, zone: z, unlocked: 12, cleared: [0,1,2,3,4,5,6,7,8,9,10,11], kills: {}, inv: [], equip: {},
  auto: {dist: true, equip: true, sell: 0, boss: false, advance: false, dungeon: false}, stats: {}, log: [], savedAt: agora, lastSeen: agora}));
localStorage.setItem('brasalume.opts', JSON.stringify({zoom: +(P.get('zoom') || 1), mute: true}));
const f = document.createElement('iframe'); f.src = 'jogar_local.html'; f.width = 1280; f.height = 860; f.style.border = '0'; document.body.appendChild(f);
setInterval(() => { try { f.contentWindow.brasalumeDebug.run.cam = null; } catch (e) {} }, 200);
const vistos = {};
window.vistos = vistos;
f.addEventListener('load', () => {
  const W = f.contentWindow, proto = W.CanvasRenderingContext2D.prototype, orig = proto.drawImage;
  proto.drawImage = function(img, sx, sy, sw){
    if (arguments.length === 9 && img && /heroi_mapa_|inimigo_/.test(img.src || '')){
      const nome = img.src.split('/').pop().replace('.png', ''), q = Math.round(sx / sw), v = vistos[nome] || (vistos[nome] = {});
      v[q] = (v[q] || 0) + 1;
    }
    return orig.apply(this, arguments);
  };
});
</script>"""
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        pag = HEROIS if self.path.startswith('/__herois.html') else MUNDO if self.path.startswith('/__mundo.html') else None
        if pag is not None:
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers(); self.wfile.write(pag); return
        return super().do_GET()
    def log_message(self, *a):
        pass
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORTA), functools.partial(H, directory=RAIZ)) as s:
    s.serve_forever()
