// Mede a página de fluidez num Edge sem janela, em tempo real (sem tempo virtual), pelo protocolo de depuração.
// uso: node medir.js <url> <segundos> [porta]
const [url, segs = '15', porta = '9333'] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  let tabs = null;
  for (let i = 0; i < 60 && !tabs; i++){ try { tabs = await (await fetch('http://127.0.0.1:' + porta + '/json')).json(); } catch (e) { await sleep(250); } }
  if (!tabs){ console.log('sem navegador na porta ' + porta); process.exit(1); }
  const pg = tabs.find(t => t.type === 'page');
  const ws = new WebSocket(pg.webSocketDebuggerUrl);
  let id = 0; const pend = new Map();
  const send = (method, params = {}) => new Promise(res => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({id: i, method, params})); });
  ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)){ pend.get(m.id)(m.result || m.error); pend.delete(m.id); } };
  await new Promise(r => { ws.onopen = r; });
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', {width: 1300, height: 900, deviceScaleFactor: +(process.env.BRASALUME_TEST_DPR || 1), mobile: false});
  await send('Page.navigate', {url});
  let rel = null;
  for (let i = 0; i < (+segs + 30) * 2 && !rel; i++){
    await sleep(500);
    const r = await send('Runtime.evaluate', {expression: 'JSON.stringify(window.__rel || null)', returnByValue: true});
    rel = r && r.result && JSON.parse(r.result.value || 'null');
  }
  console.log(rel ? rel.join('\n') : 'sem relatório');
  const foto = process.argv[5];
  if (foto){ const r = await send('Page.captureScreenshot', {format: 'png'}); require('fs').writeFileSync(foto, Buffer.from(r.data, 'base64')); console.log('captura: ' + foto); }
  ws.close(); process.exit(0);
})();
