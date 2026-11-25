type CanvasCounter = 'rad' | 'lin' | 'img' | 'txt' | 'path';

const methods: Record<string, CanvasCounter> = {
  createRadialGradient: 'rad',
  createLinearGradient: 'lin',
  drawImage: 'img',
  fillText: 'txt',
  strokeText: 'txt',
  fill: 'path',
  stroke: 'path',
};

export function installPerformanceProbe(): void {
  if (!new URLSearchParams(location.search).has('__perf')) return;

  window.__ERR = [];
  window.__F = [];
  window.__TK = [];
  window.__D = [];
  window.__N = { rad: 0, lin: 0, img: 0, txt: 0, path: 0 };
  window.addEventListener('error', event => {
    window.__ERR.push(`${event.message} @${event.lineno}`);
  });
  window.addEventListener('unhandledrejection', event => {
    window.__ERR.push(`promessa: ${String(event.reason)}`);
  });

  const prototype = CanvasRenderingContext2D.prototype as unknown as Record<string, (this: CanvasRenderingContext2D, ...args: unknown[]) => unknown>;
  for (const [method, counter] of Object.entries(methods)) {
    const original = prototype[method];
    prototype[method] = function (this: CanvasRenderingContext2D, ...args: unknown[]) {
      window.__N[counter]++;
      return original.apply(this, args);
    };
  }
  window.__PERF = (timestamp: number, start: number, world: number, hud: number, end: number) => {
    const hero = window.__hs || { x: 0, y: 0 };
    const view = window.__view || { ox: 0, oy: 0 };
    window.__F.push([
      timestamp, world - start, hud - world, end - hud,
      window.__N.rad, window.__N.img, window.__N.path,
      hero.x, hero.y, window.__walk || 0, view.ox, view.oy,
    ]);
    window.__D.push(window.__DRAW_PHASES || []);
    window.__N.rad = window.__N.lin = window.__N.img = window.__N.txt = window.__N.path = 0;
  };
}
