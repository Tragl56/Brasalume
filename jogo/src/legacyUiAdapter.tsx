import { createElement, useCallback, useLayoutEffect, useRef, useSyncExternalStore, type CSSProperties, type ElementType, type ReactNode } from 'react';
import { getGameUi, subscribeGameUi } from './uiBridge';

const reactAttributes: Record<string, string> = {
  class: 'className', for: 'htmlFor', tabindex: 'tabIndex', readonly: 'readOnly', autofocus: 'autoFocus',
  maxlength: 'maxLength', minlength: 'minLength', colspan: 'colSpan', rowspan: 'rowSpan',
  cellpadding: 'cellPadding', cellspacing: 'cellSpacing', viewbox: 'viewBox', preserveaspectratio: 'preserveAspectRatio',
  'stroke-width': 'strokeWidth', 'stroke-linecap': 'strokeLinecap', 'stroke-linejoin': 'strokeLinejoin',
  'fill-rule': 'fillRule', 'clip-rule': 'clipRule', 'fill-opacity': 'fillOpacity',
  'stroke-opacity': 'strokeOpacity', 'stroke-dasharray': 'strokeDasharray', 'stroke-dashoffset': 'strokeDashoffset',
  'stroke-miterlimit': 'strokeMiterlimit', 'font-size': 'fontSize', 'font-family': 'fontFamily',
  'font-weight': 'fontWeight', 'text-anchor': 'textAnchor', 'dominant-baseline': 'dominantBaseline',
  'vector-effect': 'vectorEffect', 'xlink:href': 'xlinkHref', 'xml:space': 'xmlSpace',
};
const booleanAttributes = new Set(['disabled', 'multiple', 'required', 'autofocus', 'hidden', 'controls', 'loop', 'muted', 'open']);
const ignoredElements = new Set(['script', 'iframe', 'object', 'embed', 'link', 'meta', 'base']);

function htmlNodeToReact(node: Node, affordability: boolean[], counters: { cost: number; key: number }, keyPrefix: string): ReactNode {
  if (node.nodeType === Node.TEXT_NODE) return node.nodeValue;
  if (node.nodeType !== Node.ELEMENT_NODE) return null;

  const element = node as Element;
  const tag = element.localName, props: Record<string, unknown> = {};
  if (ignoredElements.has(tag.toLowerCase())) return null;
  for (const attribute of element.attributes) {
    const name = attribute.name.toLowerCase();
    if (/^on[a-z]/.test(name) || name === 'selected' || name === 'srcdoc') continue;
    if (name === 'style') {
      const style: Record<string, string> = {};
      const elementStyle = (element as HTMLElement).style;
      for (let i = 0; i < elementStyle.length; i++) {
        const property = elementStyle.item(i);
        const reactProperty = property.startsWith('--') ? property : property.replace(/-([a-z])/g, (_match: string, letter: string) => letter.toUpperCase());
        style[reactProperty] = elementStyle.getPropertyValue(property).trim();
      }
      props.style = style as CSSProperties;
    } else if (name === 'checked') props.defaultChecked = true;
    else if (name === 'value' && (tag === 'input' || tag === 'textarea')) props.defaultValue = attribute.value;
    else if (booleanAttributes.has(name)) props[reactAttributes[name] || name] = true;
    else {
      if (['href', 'xlink:href', 'src', 'action', 'formaction'].includes(name)) {
        const url = attribute.value.replace(/[\u0000-\u0020]+/g, '').toLowerCase();
        if (url.startsWith('javascript:') || url.startsWith('vbscript:') || url.startsWith('data:text/html')) continue;
      }
      props[reactAttributes[name] || name] = attribute.value;
    }
  }

  if (tag === 'select') {
    const select = element as HTMLSelectElement;
    const selected = Array.from(select.options).filter(option => option.hasAttribute('selected')).map(option => option.value);
    if (selected.length) props.defaultValue = select.multiple ? selected : selected[0];
  }
  if (element.hasAttribute('data-cost')) {
    const index = counters.cost++;
    if (index < affordability.length) props.disabled = affordability[index];
  }

  const children = tag === 'textarea' ? [] : Array.from(element.childNodes)
    .map(child => htmlNodeToReact(child, affordability, counters, keyPrefix))
    .filter((child): child is ReactNode => child !== null);
  if (tag === 'textarea') props.defaultValue = element.textContent;
  return createElement(tag, { ...props, key: keyPrefix + ':' + counters.key++ } as React.Attributes, ...children);
}

export function htmlToReact(html: string, affordability: boolean[] = [], keyPrefix = ''): ReactNode[] {
  const parsed = new DOMParser().parseFromString(`<body>${html || ''}</body>`, 'text/html');
  const counters = { cost: 0, key: 0 };
  return Array.from(parsed.body.childNodes)
    .map(child => htmlNodeToReact(child, affordability, counters, keyPrefix))
    .filter((child): child is ReactNode => child !== null);
}

type UiProps = {
  id: string;
  as?: ElementType;
  children?: ReactNode;
  className?: string;
  title?: string;
  hidden?: boolean;
  style?: CSSProperties;
  [attribute: string]: unknown;
};

export function Ui({ id, as = 'span', children, ...props }: UiProps) {
  const subscribe = useCallback((listener: () => void) => subscribeGameUi(id, listener), [id]);
  const getSnapshot = useCallback(() => getGameUi(id), [id]);
  const state = useSyncExternalStore(subscribe, getSnapshot, () => null);
  const elementRef = useRef<HTMLElement | null>(null);
  const paintedIcons = useRef<string | null | undefined>(null);
  const attributes: Record<string, unknown> = { ...props, id };
  if (state) {
    if ('className' in state) attributes.className = state.className;
    if ('title' in state) attributes.title = state.title;
    if ('hidden' in state) attributes.hidden = state.hidden;
    if ('ariaPressed' in state) attributes['aria-pressed'] = state.ariaPressed;
    if (state.style) attributes.style = { ...props.style, ...state.style };
  }
  useLayoutEffect(() => {
    const game = window.brasalumeDebug;
    if (!game || !state) return;
    if (id === 'hud-emb' && state.canvasProps) game.paintPortraits(elementRef.current);
    if (id === 'hud-skills' && state.iconRevision !== paintedIcons.current) {
      paintedIcons.current = state.iconRevision;
      game.fxIcones();
    }
  }, [id, state]);
  attributes.ref = elementRef;
  if (state && state.canvasProps) {
    return createElement(as, attributes as React.Attributes, createElement('canvas', state.canvasProps as React.CanvasHTMLAttributes<HTMLCanvasElement>));
  }
  if (state && Array.isArray(state.items)) {
    return createElement(as, attributes as React.Attributes, state.items.map((item, index) => {
      const itemProps = { ...item, key: item.key || item.id || index };
      delete itemProps.tag;
      delete itemProps.html;
      delete itemProps.text;
      if (item.html != null) return createElement(item.tag || 'span', itemProps as React.Attributes, ...htmlToReact(item.html));
      return createElement(item.tag || 'span', itemProps as React.Attributes, item.text);
    }));
  }
  if (state && Object.prototype.hasOwnProperty.call(state, 'html')) {
    return createElement(as, attributes as React.Attributes, ...htmlToReact(String(state.html)));
  }
  return createElement(as, attributes as React.Attributes, state && Object.prototype.hasOwnProperty.call(state, 'text') ? String(state.text) : children);
}
