# Servidor de medição de fluidez: entrega o build de jogo/ e duas páginas extras.
#  /__jogo_perf.html   abre o app React em modo de diagnóstico (?__perf=1)
#  /__perf.html?z=0&cls=guerreiro&path=baluarte&dg=0&s=12   joga e mostra o relatório depois de s segundos
# Uso (na raiz do projeto): python -I ferramentas/servidor_teste.py [pasta_do_build] [porta]   (padrão: jogo/dist e 8774)
import http.server, socketserver, sys, functools, os
AQUI = os.path.dirname(os.path.abspath(__file__))
PROJETO = os.path.dirname(AQUI)   # E:\RPGjogo
RAIZ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJETO, 'jogo', 'dist')
PORTA = int(sys.argv[2]) if len(sys.argv) > 2 else 8774

def jogo_perf():
    with open(os.path.join(RAIZ, 'index.html'), 'rb') as f:
        return f.read()


PERF = r"""<!doctype html><meta charset=utf-8><body style="margin:0;background:#000">
<pre id=r style="position:absolute;left:0;top:0;z-index:2;margin:0;padding:8px;background:rgba(0,0,0,.8);color:#e6dcc4;font:13px monospace"></pre>
<script>
const P = new URLSearchParams(location.search), z = +(P.get('z') || 0), agora = Date.now(), cls = P.get('cls') || 'guerreiro', path = P.get('path') || null, dg = P.get('dg') === '1';
localStorage.setItem('brasalume.save.v1', JSON.stringify({v: 1, created: agora, hero: {lv: +(P.get('lv') || 40), xp: 0, pts: 0,
  stats: {FOR: +(P.get('st') || 260), VIG: +(P.get('st') || 260), INT: 60, ESP: 60, DES: 60}, arch: cls, classes: path ? [cls, path] : [cls], path: path},
  gold: 0, cinzas: 0, perks: {}, zone: z, unlocked: 12, cleared: [0,1,2,3,4,5,6,7,8,9,10,11], kills: {}, inv: [], equip: {},
  auto: {dist: true, equip: true, sell: 0, boss: false, advance: false, dungeon: dg}, stats: {}, log: [], savedAt: agora, lastSeen: agora}));
localStorage.setItem('brasalume.opts', JSON.stringify({zoom: +(P.get('zoom') || 1), mute: true}));
const f = document.createElement('iframe'); f.src = '__jogo_perf.html?__perf=1'; f.width = 1280; f.height = 860; f.style.border = '0'; document.body.appendChild(f);
const q = (a, p) => { if (!a.length) return 0; const b = a.slice().sort((x, y) => x - y); return b[Math.min(b.length - 1, Math.floor(p * b.length))]; };
const med = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0;
function relatorio(){
  const W = f.contentWindow, F = W.__F.slice(30), TK = W.__TK.slice(5), D = (W.__D || []).slice(30);
  const iv = []; for (let i = 1; i < F.length; i++) iv.push(F[i][0] - F[i - 1][0]);
  // passo do herói na tela (descontando a câmera) a cada quadro, só enquanto anda
  const mov = []; let parado = 0, andando = 0;
  for (let i = 1; i < F.length; i++){ if (F[i][9] < .8) continue; andando++;
    const dx = (F[i][7] - F[i][10]) - (F[i - 1][7] - F[i - 1][10]), dy = (F[i][8] - F[i][11]) - (F[i - 1][8] - F[i - 1][11]), d = Math.hypot(dx, dy);
    mov.push(d); if (d < .05) parado++; }
  const L = [];
  L.push('quadros ' + F.length + ' | intervalo médio ' + med(iv).toFixed(1) + ' ms (' + (1000 / med(iv)).toFixed(0) + ' fps) | p95 ' + q(iv, .95).toFixed(1) + ' | p99 ' + q(iv, .99).toFixed(1) + ' | máx ' + Math.max(...iv).toFixed(1));
  L.push('quadros acima de 25 ms: ' + iv.filter(x => x > 25).length + ' | acima de 50 ms: ' + iv.filter(x => x > 50).length);
  L.push('drawWorld médio ' + med(F.map(x => x[1])).toFixed(2) + ' ms, p95 ' + q(F.map(x => x[1]), .95).toFixed(2));
  L.push('updateHUD médio ' + med(F.map(x => x[2])).toFixed(2) + ' ms, p95 ' + q(F.map(x => x[2]), .95).toFixed(2));
  L.push('renderTab médio ' + med(F.map(x => x[3])).toFixed(2) + ' ms, p95 ' + q(F.map(x => x[3]), .95).toFixed(2));
  L.push('tick (simulação) médio ' + med(TK).toFixed(2) + ' ms, p95 ' + q(TK, .95).toFixed(2) + ', máx ' + Math.max(0, ...TK).toFixed(2));
  L.push('por quadro: gradientes radiais ' + med(F.map(x => x[4])).toFixed(1) + ' | drawImage ' + med(F.map(x => x[5])).toFixed(1) + ' | fill+stroke ' + med(F.map(x => x[6])).toFixed(0));
  const fases = {};
  for (const quadro of D) for (const [nome, ms] of quadro) (fases[nome] || (fases[nome] = [])).push(ms);
  for (const nome of Object.keys(fases)) L.push(nome + ': ' + med(fases[nome]).toFixed(2) + ' ms, p95 ' + q(fases[nome], .95).toFixed(2));
  L.push('herói andando: ' + andando + ' quadros, ' + parado + ' sem sair do lugar (' + (andando ? (100 * parado / andando).toFixed(0) : 0) + '%) | passo médio ' + med(mov).toFixed(2) + ' px, p95 ' + q(mov, .95).toFixed(2));
  L.push('erros de script: ' + W.__ERR.length + (W.__ERR.length ? ' | ' + W.__ERR.slice(0, 3).join(' ; ') : ''));
  document.getElementById('r').textContent = L.join(String.fromCharCode(10));
  window.__rel = L;
}
f.addEventListener('load', () => {
  const dgid = P.get('dgid');
  if (dgid) setTimeout(() => { const D = f.contentWindow.brasalumeDebug; D.enterDungeon(D.DUNGEONS.findIndex(d => d.id === dgid)); }, 1500);
  setTimeout(relatorio, (+(P.get('s') || 12)) * 1000 + (dgid ? 1500 : 0));
});
</script>"""


class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/__jogo_perf.html'):
            pag = jogo_perf()
        elif self.path.startswith('/__perf.html'):
            pag = PERF.encode('utf-8')
        else:
            return super().do_GET()
        self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(pag)

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORTA), functools.partial(H, directory=RAIZ)) as s:
    s.serve_forever()
