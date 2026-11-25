interface TabViewDetail {
  tab: string;
  html: string;
  scrollTop: number;
}

interface WindowEventMap {
  'brasalume:tab': CustomEvent<TabViewDetail>;
  'brasalume:affordability': CustomEvent<boolean[]>;
  'brasalume:tab-dots': CustomEvent<Record<string, boolean>>;
  'brasalume:action': CustomEvent<HTMLElement>;
  'brasalume:input': CustomEvent<HTMLElement>;
  'brasalume:change': CustomEvent<HTMLElement>;
  'brasalume:panel': CustomEvent<boolean>;
}

interface Window {
  brasalumeDebug?: {
    paintPortraits(element: HTMLElement | null): void;
    fxIcones(): void;
  };
  __ERR: string[];
  __F: number[][];
  __TK: number[];
  __D: Array<Array<[string, number]>>;
  __N: Record<'rad' | 'lin' | 'img' | 'txt' | 'path', number>;
  __PERF?: (timestamp: number, start: number, world: number, hud: number, end: number) => void;
  __hs?: { x: number; y: number };
  __view?: { ox: number; oy: number };
  __walk?: number;
  __DRAW_PHASES?: Array<[string, number]>;
}

declare module '*.css';
