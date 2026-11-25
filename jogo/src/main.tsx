import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { htmlToReact, Ui } from './legacyUiAdapter';
import { installPerformanceProbe } from './perfProbe';
import './styles.css';

const tabs: Array<[string, string]> = [
  ['heroi', 'Herói'],
  ['voc', 'Vocações'],
  ['equip', 'Equipamento'],
  ['forja', 'Forja'],
  ['oficio', 'Ofício'],
  ['ceu', 'Constelação'],
  ['era', 'Era'],
  ['vila', 'Vila'],
  ['reg', 'Regiões'],
  ['masm', 'Masmorras'],
  ['colecao', 'Coleção'],
  ['reac', 'Reacender'],
  ['diario', 'Diário'],
];

function ResourceChips() {
  return (
      <div className="res">
        <span className="chip gold" title="Ouro"><svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1l6 7-6 7-6-7z" /></svg>Ouro <Ui as="b" id="r-gold">0</Ui></span>
        <span className="chip ash" title="Cinzas, ganhas ao reacender a lanterna"><svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1c1 3 5 4.5 5 8.5a5 5 0 0 1-10 0c0-2.3 1.4-3.8 2.3-5.3.2 1.6 1 2.4 1.8 2.4C7.1 4.5 7.3 2.8 8 1z" /></svg>Cinzas <Ui as="b" id="r-ash">0</Ui></span>
        <span className="chip ins" title="Insígnias da vila, ganhas nas missões"><svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1l2 4.2 4.6.6-3.4 3.2.9 4.6L8 11.4 3.9 13.6l.9-4.6L1.4 5.8 6 5.2z" /></svg>Insígnias <Ui as="b" id="r-ins">0</Ui></span>
        <Ui as="span" className="chip save" id="r-save" title="Onde o progresso está salvo">Salvo neste navegador</Ui>
      </div>
  );
}

function StageHud() {
  return (
    <section className="stage" id="stagebox" aria-label="Mapa e combate">
      <canvas id="stage" title="Clique no chão para andar, num monstro para atacar, num portal ou numa masmorra para entrar" aria-label="Mapa: clique no chão para andar, num monstro para atacar, num portal ou numa masmorra para entrar" />
      <div className="hud">
        <Ui as="div" className="hud-vig" id="hud-vig" />
        <Ui as="div" className="hud-me glass" id="hud-me">
          <span className="hud-pwrap"><Ui className="hud-portrait" id="hud-emb" /><Ui className="hud-lvb" id="hud-lv" title="Nível">1</Ui></span>
          <div className="hud-col">
            <div className="hud-line"><b>Portador</b><Ui className="hud-voc" id="hud-voc">sem vocação</Ui></div>
            <div className="bar hp hudbar"><Ui as="i" className="lag" id="hud-hplag" /><Ui as="i" id="hud-hp" /><Ui as="span" className="bt" id="hud-hpt" /></div>
            <div className="hud-xprow" title="Experiência até o próximo nível"><div className="bar xp thin"><Ui as="i" id="hud-xp" /></div><Ui as="span" id="hud-xpt">0%</Ui></div>
            <Ui as="div" className="hud-buffs" id="hud-buffs" />
          </div>
        </Ui>
        <Ui as="div" className="hud-target glass idle" id="hud-target">
          <canvas className="hud-mon" id="ht-icon" aria-hidden="true" />
          <div className="hud-col">
            <div className="hud-line"><Ui as="b" id="ht-name">Explorando…</Ui></div>
            <div className="bar hp hudbar"><Ui as="i" className="lag" id="ht-hplag" /><Ui as="i" id="ht-hp" /><Ui as="span" className="bt" id="ht-hpt" /></div>
            <div className="hud-sub"><span className="hud-sl"><Ui className="htag" id="ht-tag" hidden /><Ui id="ht-lv" /></span><Ui className="ht-fx" id="ht-fx" /></div>
          </div>
        </Ui>
        <div className="hud-map glass">
          <div className="hud-zone"><Ui id="hud-zone">Clareira das Cinzas</Ui><Ui as="small" id="hud-zlv" /></div>
          <canvas id="minimap" aria-hidden="true" />
          <Ui as="ul" className="hud-track" id="hud-track" />
          <div className="hud-tools">
            <Ui as="button" type="button" className="btn sm hud-btn icon" id="btn-mute" data-act="mute" title="Som (M)" aria-label="Som" aria-pressed="true" />
            <button type="button" className="btn sm hud-btn icon" data-act="zoomout" title="Afastar a câmera (−)" aria-label="Afastar a câmera"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="4.6" fill="none" stroke="currentColor" strokeWidth="1.6" /><path stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" d="M10.5 10.5 14 14M5 7h4" /></svg></button>
            <button type="button" className="btn sm hud-btn icon" data-act="zoomin" title="Aproximar a câmera (+)" aria-label="Aproximar a câmera"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="4.6" fill="none" stroke="currentColor" strokeWidth="1.6" /><path stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" d="M10.5 10.5 14 14M5 7h4M7 5v4" /></svg></button>
            <button type="button" className="btn sm hud-btn icon" id="btn-full" data-act="fullscreen" title="Tela cheia (F)" aria-label="Tela cheia"><svg viewBox="0 0 16 16" aria-hidden="true"><path fill="none" stroke="currentColor" strokeWidth="1.8" d="M2 6V2h4M10 2h4v4M14 10v4h-4M6 14H2v-4" /></svg></button>
          </div>
        </div>
        <Ui as="div" className="hud-skills glass" id="hud-skills" />
        <div className="hud-actions" id="hud-actions">
          <Ui as="ul" className="hud-feed" id="hud-feed" aria-hidden="true" />
          <Ui as="button" type="button" className="btn sm hud-btn boss" id="btn-boss" data-act="boss" title="Atalho: B" hidden><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 8l4.5 3L12 4l4.5 7L21 8l-2 11H5z" /></svg>Desafiar chefe</Ui>
          <Ui as="button" type="button" className="btn sm hud-btn dg" id="btn-dg" data-act="gatenow" hidden>Entrar na masmorra</Ui>
          <Ui as="button" type="button" className="btn sm hud-btn" id="btn-leave" data-act="leavedg" hidden>Sair da masmorra</Ui>
        </div>
      </div>
      <Ui as="div" className="banner" id="banner" />
    </section>
  );
}

function HeroPanel() {
  return (
    <section className="card hero" aria-label="Herói">
      <div className="heroline"><span className="heroname">Portador</span><Ui className="lv" id="h-lv">Nv. 1</Ui><Ui className="heroclass" id="h-class">sem vocação</Ui></div>
      <div className="pair"><span>Exp.</span><div className="bar xp"><Ui as="i" id="h-xpbar" /></div><Ui as="span" className="num" id="h-xp">0</Ui></div>
      <div className="quick">
        <span>Poder <Ui as="b" id="q-pow">0</Ui></span>
        <span>Dano/s aprox. <Ui as="b" id="q-dps">0</Ui></span>
        <span>Vida máx. <Ui as="b" id="q-hp">0</Ui></span>
        <span>Pontos livres <Ui as="b" id="q-pts">0</Ui></span>
      </div>
      <Ui as="div" className="nudge" id="h-nudge" hidden><Ui id="h-nudge-t" /><button type="button" className="btn sm primary" data-act="tab" data-tab="voc">Ver vocações</button></Ui>
    </section>
  );
}

function Journal() {
  const [tabView, setTabView] = useState<{ tab: string; html: string; scrollTop: number; affordability: boolean[]; version: number }>({ tab: 'heroi', html: '', scrollTop: 0, affordability: [], version: 0 });
  const [dots, setDots] = useState<Record<string, boolean>>({});
  const bodyRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const showTab = (event: WindowEventMap['brasalume:tab']) => setTabView(current => ({ ...event.detail, affordability: [], version: current.version + 1 }));
    const updateAffordability = (event: WindowEventMap['brasalume:affordability']) => setTabView(current => ({ ...current, affordability: event.detail }));
    const showDots = (event: WindowEventMap['brasalume:tab-dots']) => setDots(event.detail);
    window.addEventListener('brasalume:tab', showTab);
    window.addEventListener('brasalume:affordability', updateAffordability);
    window.addEventListener('brasalume:tab-dots', showDots);
    return () => {
      window.removeEventListener('brasalume:tab', showTab);
      window.removeEventListener('brasalume:affordability', updateAffordability);
      window.removeEventListener('brasalume:tab-dots', showDots);
    };
  }, []);

  useLayoutEffect(() => {
    if (!bodyRef.current) return;
    bodyRef.current.scrollTop = tabView.scrollTop;
    const game = window.brasalumeDebug;
    if (game) game.paintPortraits(bodyRef.current);
  }, [tabView]);

  return (
    <section className="card journal" aria-label="Diário">
      <div className="painel-top">
        <ResourceChips />
        <button type="button" className="btn sm" data-act="painelx" aria-label="Fechar o diário">Fechar ✕</button>
      </div>
      <nav className="tabs" role="tablist" id="tabs">
        {tabs.map(([id, label]) => (
          <button key={id} type="button" className="tab" role="tab" aria-selected={tabView.tab === id} data-act="tab" data-tab={id} id={`t-${id}`}>
            {label}{dots[id] && <span className="dot" aria-label="novidade" />}
          </button>
        ))}
      </nav>
      <div
        ref={bodyRef}
        className="tabbody"
        id="tabbody"
        role="tabpanel"
        aria-labelledby={`t-${tabView.tab}`}
      >{htmlToReact(tabView.html, tabView.affordability, String(tabView.version))}</div>
      <section className="card logbox" aria-label="Registro">
        <h3 className="faint" style={{ margin: 0, fontSize: '.74rem', letterSpacing: '.1em', textTransform: 'uppercase', fontWeight: 800 }}>Registro</h3>
        <Ui as="ul" className="log" id="log" />
      </section>
    </section>
  );
}

function Dialogs() {
  return (
    <>
      <button type="button" className="btn sm btn-painel" id="btn-painel" data-act="painel" title="Abre as abas (J)" aria-label="Abrir o diário"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M2 3h12v2H2zM2 7h12v2H2zM2 11h12v2H2z" /></svg>Diário</button>
      <Ui as="div" className="toasts" id="toasts" aria-live="polite" />
      <Ui as="div" className="modal" id="story" hidden>
        <div className="box story" role="dialog" aria-modal="true" aria-labelledby="st-title">
          <Ui as="p" className="story-ato" id="st-ato" /><Ui as="h2" id="st-title" /><Ui as="p" className="story-txt" id="st-text" />
          <button type="button" className="btn primary" data-act="closestory">Seguir</button>
        </div>
      </Ui>
      <Ui as="div" className="modal" id="offline" hidden>
        <div className="box" role="dialog" aria-modal="true" aria-labelledby="off-title">
          <h2 id="off-title">Enquanto você esteve fora</h2><Ui as="p" className="muted" id="off-sub" /><Ui as="ul" id="off-list" />
          <button type="button" className="btn primary" data-act="closeoff">Continuar</button>
        </div>
      </Ui>
    </>
  );
}

function App() {
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    installPerformanceProbe();
    const onAction = (event: MouseEvent) => {
      const target = event.target instanceof Element ? event.target.closest('[data-act]') : null;
      if (target && !target.hasAttribute('disabled')) window.dispatchEvent(new CustomEvent('brasalume:action', { detail: target as HTMLElement }));
    };
    const onInput = (event: Event) => {
      if (event.target instanceof HTMLElement) window.dispatchEvent(new CustomEvent('brasalume:input', { detail: event.target }));
    };
    const onChange = (event: Event) => {
      if (event.target instanceof HTMLElement) window.dispatchEvent(new CustomEvent('brasalume:change', { detail: event.target }));
    };
    const onPanel = (event: WindowEventMap['brasalume:panel']) => document.documentElement.classList.toggle('painel-aberto', event.detail);
    document.documentElement.classList.add('modo-jogo');
    window.addEventListener('brasalume:panel', onPanel);
    const root = document.getElementById('root');
    if (!root) throw new Error('Elemento raiz do app não encontrado.');
    root.addEventListener('click', onAction);
    root.addEventListener('input', onInput);
    root.addEventListener('change', onChange);
    import('./gameEngine.js').catch((error: unknown) => {
      setLoadError(`Não foi possível iniciar o jogo: ${error instanceof Error ? error.message : String(error)}`);
    });
    return () => {
      window.removeEventListener('brasalume:panel', onPanel);
      root.removeEventListener('click', onAction);
      root.removeEventListener('input', onInput);
      root.removeEventListener('change', onChange);
      document.documentElement.classList.remove('modo-jogo', 'painel-aberto');
    };
  }, []);

  return (
    <>
      <main className="app">
        <div className="grid">
          <div className="col">
            <StageHud />
            <HeroPanel />
          </div>
          <Journal />
        </div>
      </main>
      <Dialogs />
      {loadError && <p role="alert" className="load-error">{loadError}</p>}
    </>
  );
}

const root = document.getElementById('root');
if (!root) throw new Error('Elemento raiz do app não encontrado.');
createRoot(root).render(<App />);
