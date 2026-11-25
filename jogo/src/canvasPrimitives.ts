export const TW = 64;
export const TH = 32;

export function shade(hex: string, factor: number): string {
  const value = Number.parseInt(hex.slice(1), 16);
  let red = value >> 16;
  let green = value >> 8 & 255;
  let blue = value & 255;
  if (factor < 0) {
    red *= 1 + factor;
    green *= 1 + factor;
    blue *= 1 + factor;
  } else {
    red += (255 - red) * factor;
    green += (255 - green) * factor;
    blue += (255 - blue) * factor;
  }
  return `rgb(${red | 0},${green | 0},${blue | 0})`;
}

export function mixHex(first: string, second: string, amount: number): string {
  const a = Number.parseInt(first.slice(1), 16);
  const b = Number.parseInt(second.slice(1), 16);
  const channel = (shift: number) => ((a >> shift & 255) + ((b >> shift & 255) - (a >> shift & 255)) * amount) | 0;
  return `rgb(${channel(16)},${channel(8)},${channel(0)})`;
}

export function ell(context: CanvasRenderingContext2D, x: number, y: number, radiusX: number, radiusY: number): void {
  context.beginPath();
  context.ellipse(x, y, Math.max(.1, radiusX), Math.max(.1, radiusY), 0, 0, Math.PI * 2);
  context.fill();
}

export function circ(context: CanvasRenderingContext2D, x: number, y: number, radius: number): void {
  ell(context, x, y, radius, radius);
}

export function rrect(context: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, radius: number): void {
  context.beginPath();
  if (context.roundRect) context.roundRect(x, y, width, height, radius);
  else context.rect(x, y, width, height);
  context.fill();
}

export function iso(x: number, y: number): { x: number; y: number } {
  return { x: (x - y) * TW / 2, y: (x + y) * TH / 2 };
}

export function hexA(hex: string, alpha: number): string {
  const value = Number.parseInt(hex.slice(1), 16);
  return `rgba(${value >> 16},${value >> 8 & 255},${value & 255},${alpha})`;
}
