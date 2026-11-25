export type UiItem = {
  key?: string | number;
  id?: string;
  tag?: string;
  html?: string;
  text?: string;
  [attribute: string]: unknown;
};

export type GameUiState = {
  className?: string;
  title?: string;
  hidden?: boolean;
  ariaPressed?: string;
  style?: Record<string, string | number>;
  html?: string;
  text?: string;
  items?: UiItem[];
  canvasProps?: Record<string, string | number | boolean>;
  iconRevision?: string;
  [key: string]: unknown;
};

export type GameUiPatch = Partial<GameUiState>;

const values = new Map<string, GameUiState>();
const listeners = new Map<string, Set<() => void>>();

export function getGameUi(id: string): GameUiState | null {
  return values.get(id) || null;
}

export function subscribeGameUi(id: string, listener: () => void): () => void {
  let subscribers = listeners.get(id);
  if (!subscribers) listeners.set(id, subscribers = new Set());
  subscribers.add(listener);
  return () => {
    subscribers.delete(listener);
    if (!subscribers.size) listeners.delete(id);
  };
}

export function setGameUi(id: string, patch: GameUiPatch): void {
  const previous: GameUiState = values.get(id) || {};
  let changed = false;
  const next = { ...previous };
  for (const [key, value] of Object.entries(patch)) {
    if (key === 'style' && value && typeof value === 'object') {
      const style: Record<string, string | number> = { ...(previous.style || {}) };
      for (const [property, styleValue] of Object.entries(value)) {
        if (typeof styleValue !== 'string' && typeof styleValue !== 'number') continue;
        if (!Object.is(style[property], styleValue)) {
          style[property] = styleValue;
          changed = true;
        }
      }
      if (changed) next.style = style;
      continue;
    }
    if (!Object.is(previous[key], value)) {
      next[key] = value;
      changed = true;
    }
  }
  if (!changed) return;
  values.set(id, next);
  for (const listener of listeners.get(id) || []) listener();
}
