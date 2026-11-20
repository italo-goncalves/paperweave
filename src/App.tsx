import { useEffect } from "react";
import { ReaderProvider, useReader } from "./state";
import { works, TIERS, type Tier } from "./work";
import { DEFAULT_LAYOUT, PANEL_TITLES, PanelLayout, useLayout, type PanelId } from "./Layout";
import { ResultsList } from "./panels/ResultsList";
import { ReadingPanel } from "./panels/ReadingPanel";
import { GraphMap } from "./panels/GraphMap";
import { FigurePanel, Lightbox } from "./panels/FigurePanel";

const TIER_LABELS: Record<Tier, string> = { gist: "Gist", summary: "Summary", full: "Full" };

export function App() {
  const work = works[0];
  if (!work) return <p className="empty">No Work found in /works.</p>;
  return (
    <ReaderProvider work={work}>
      <Shell />
    </ReaderProvider>
  );
}

function Shell() {
  const { work, state, dispatch } = useReader();
  const [layout, setLayout] = useLayout();

  useEffect(() => {
    document.title = `${work.title} · Graph-doc`;
  }, [work.title]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") dispatch({ type: "lightbox", id: null });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dispatch]);

  const render = (id: PanelId) => {
    switch (id) {
      case "results":
        return <ResultsList />;
      case "reading":
        return <ReadingPanel />;
      case "graph":
        return <GraphMap />;
      case "figures":
        return <FigurePanel />;
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">Graph-doc</span>
        <span className="topbar-work" title={work.title}>{work.title}</span>
        <div className="topbar-controls">
          <label className="ctl">
            <span>Detail</span>
            <span className="seg" role="group" aria-label="Global Detail tier">
              {TIERS.map((t) => (
                <button key={t} className={state.globalTier === t ? "seg-on" : ""} onClick={() => dispatch({ type: "setGlobalTier", tier: t })}>
                  {TIER_LABELS[t]}
                </button>
              ))}
            </span>
          </label>
          <span className="ctl panel-toggles" role="group" aria-label="Show or hide Panels">
            {(Object.keys(PANEL_TITLES) as PanelId[]).map((p) => {
              const hidden = layout.hidden.includes(p);
              return (
                <button
                  key={p}
                  className={`toggle${hidden ? "" : " toggle-on"}`}
                  aria-pressed={!hidden}
                  title={`${hidden ? "Show" : "Hide"} ${PANEL_TITLES[p]}`}
                  onClick={() => setLayout((l) => ({ ...l, hidden: hidden ? l.hidden.filter((h) => h !== p) : [...l.hidden, p] }))}
                >
                  {PANEL_TITLES[p].replace(/ (list|panel|map)$/, "")}
                </button>
              );
            })}
          </span>
          <button className="link-btn" onClick={() => setLayout(() => DEFAULT_LAYOUT)}>
            Reset layout
          </button>
        </div>
      </header>
      <PanelLayout layout={layout} setLayout={setLayout} render={render} />
      <Lightbox />
    </div>
  );
}
