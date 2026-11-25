// Abre o jogo num Edge sem janela (porta de depuração), com um save antigo (v1) semeado, clica em cada aba e guarda o texto
// e uma captura de cada uma; junta os erros de script. uso: node conferir_abas.js <origem> <pasta_saida> [porta]
const [origem, pasta, porta = '9333'] = process.argv.slice(2);
const fs = require('fs'), path = require('path');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const tabs = await (await fetch('http://127.0.0.1:' + porta + '/json')).json();
  const pg = tabs.find(t => t.type === 'page');
  const ws = new WebSocket(pg.webSocketDebuggerUrl);
  let id = 0; const pend = new Map(), erros = [];
  const send = (method, params = {}) => new Promise(res => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({id: i, method, params})); });
  ws.onmessage = ev => { const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)){ pend.get(m.id)(m.result || m.error); pend.delete(m.id); }
    if (m.method === 'Runtime.exceptionThrown') erros.push((m.params.exceptionDetails.exception || {}).description || m.params.exceptionDetails.text);
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') erros.push('console: ' + m.params.args.map(a => a.value || a.description).join(' ')); };
  await new Promise(r => { ws.onopen = r; });
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', {width: 1300, height: 900, deviceScaleFactor: 1, mobile: false});
  const ev = async expr => { const r = await send('Runtime.evaluate', {expression: expr, returnByValue: true, awaitPromise: true}); return r && r.result ? r.result.value : r; };
  const foto = async nome => { const r = await send('Page.captureScreenshot', {format: 'png'}); fs.writeFileSync(path.join(pasta, nome), Buffer.from(r.data, 'base64')); };
  await send('Page.navigate', {url: origem + '/__vazio_' + Date.now()}); await sleep(800);
  const agora = Date.now();
  await ev(`localStorage.clear(); localStorage.setItem('brasalume.save.v1', JSON.stringify({v: 1, created: ${agora}, hero: {lv: 60, xp: 0, pts: 0,
    stats: {FOR: 300, VIG: 300, INT: 60, ESP: 60, DES: 60}, arch: 'guerreiro', classes: ['guerreiro', 'ceifador'], path: 'ceifador'},
    gold: 50000, cinzas: 20, perks: {}, zone: 5, unlocked: 13, cleared: [0,1,2,3,4,5,6,7,8,9,10,11,12], kills: {}, inv: [], equip: {},
    auto: {dist: true, equip: true, sell: 0, boss: false, advance: false, dungeon: false}, stats: {}, log: [], savedAt: ${agora}, lastSeen: ${agora}}));
    localStorage.setItem('brasalume.opts', JSON.stringify({zoom: 1.3, mute: true})); 'ok'`);
  await send('Page.navigate', {url: origem + '/jogar_local.html'}); await sleep(3500);
  const out = [];
  const abas = await ev(`[...document.querySelectorAll('[data-tab]')].map(b => b.dataset.tab + '=' + b.textContent.trim()).join(' | ')`);
  out.push('ABAS: ' + abas);
  out.push('REGISTRO: ' + await ev(`(document.querySelector('#log, .log, [id*=log]') || {}).innerText?.slice(0, 400) || ''`));
  const lista = (abas || '').split(' | ').map(s => s.split('=')[0]).filter(Boolean);
  for (const a of lista){
    await ev(`(document.querySelector('[data-tab="${a}"]') || {}).click?.(); 'ok'`); await sleep(700);
    const txt = await ev(`(document.querySelector('#tabbody') || document.body).innerText.replace(/\\s+/g, ' ').slice(0, 500)`);
    out.push('--- ' + a + ': ' + txt);
    await foto('aba_' + a + '.png');
  }
  out.push('ERROS: ' + (erros.length ? erros.slice(0, 8).join(' ; ') : 'nenhum'));
  fs.writeFileSync(path.join(pasta, 'abas.txt'), out.join('\n'));
  console.log(out.join('\n').slice(0, 6000));
  ws.close(); process.exit(0);
})();
