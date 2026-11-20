import { useCallback, useEffect, useRef, useState, type DragEvent, type PointerEvent as RPointerEvent, type ReactNode } from "react";

export type PanelId = "results" | "reading" | "graph" | "figures";

export const PANEL_TITLES: Record<PanelId, string> = {
  results: "Results list",
  reading: "Reading panel",
  graph: "Graph map",
  figures: "Figure panel",
};

export interface LayoutModel {
  columns: PanelId[][];
  /** Relative width of each column. */
  widths: number[];
  /** Relative height of each Panel within its column. */
  grow: Record<PanelId, number>;
  hidden: PanelId[];
}

export const DEFAULT_LAYOUT: LayoutModel = {
  columns: [["results"], ["reading"], ["graph", "figures"]],
  widths: [0.2, 0.42, 0.38],
  grow: { results: 1, reading: 1, graph: 1.1, figures: 0.9 },
  hidden: [],
};

const STORAGE_KEY = "graph-doc-layout-v1";

function isValid(m: unknown): m is LayoutModel {
  const l = m as LayoutModel;
  if (!l || !Array.isArray(l.columns) || l.columns.length !== 3 || !Array.isArray(l.widths) || !l.grow || !Array.isArray(l.hidden)) return false;
  const all = l.columns.flat().sort().join(",");
  return all === Object.keys(PANEL_TITLES).sort().join(",");
}

export function useLayout() {
  const [layout, setLayout] = useState<LayoutModel>(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "null");
      if (isValid(saved)) return saved;
    } catch {
      /* storage unavailable or corrupt: fall back to default */
    }
    return DEFAULT_LAYOUT;
  });
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(layout));
    } catch {
      /* ignore */
    }
  }, [layout]);
  return [layout, setLayout] as const;
}

interface Props {
  layout: LayoutModel;
  setLayout: (f: (l: LayoutModel) => LayoutModel) => void;
  render: (id: PanelId) => ReactNode;
  headerExtras?: Partial<Record<PanelId, ReactNode>>;
}

export function PanelLayout({ layout, setLayout, render, headerExtras }: Props) {
  const root = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState<PanelId | null>(null);
  const [dropHint, setDropHint] = useState<{ col: number; index: number } | null>(null);

  const shown = (col: PanelId[]) => col.filter((p) => !layout.hidden.includes(p));
  const visibleCols = layout.columns.map((c, i) => ({ i, panels: shown(c) })).filter((c) => dragging || c.panels.length > 0);

  const move = useCallback(
    (id: PanelId, col: number, index: number) =>
      setLayout((l) => {
        const columns = l.columns.map((c) => [...c]);
        const fromCol = columns.findIndex((c) => c.includes(id));
        const fromIdx = columns[fromCol].indexOf(id);
        columns[fromCol].splice(fromIdx, 1);
        // `index` counts visible Panels; map it to a position in the full column.
        const target = columns[col];
        const visibleInTarget = target.filter((p) => !l.hidden.includes(p));
        let at = target.length;
        if (index < visibleInTarget.length) at = target.indexOf(visibleInTarget[index]);
        target.splice(at, 0, id);
        return { ...l, columns };
      }),
    [setLayout],
  );

  const onDragOverPanel = (e: DragEvent, col: number, index: number) => {
    if (!dragging) return;
    e.preventDefault();
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const after = e.clientY > rect.top + rect.height / 2;
    setDropHint({ col, index: index + (after ? 1 : 0) });
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    if (dragging && dropHint) {
      // Dropping a Panel just after itself would otherwise shift it by one.
      const col = layout.columns[dropHint.col];
      const vis = shown(col);
      const self = vis.indexOf(dragging);
      const index = self >= 0 && dropHint.index > self ? dropHint.index - 1 : dropHint.index;
      move(dragging, dropHint.col, index);
    }
    setDragging(null);
    setDropHint(null);
  };

  // Splitters
  const startColResize = (e: RPointerEvent, leftCol: number, rightCol: number) => {
    e.preventDefault();
    const total = root.current?.getBoundingClientRect().width ?? 1;
    const startX = e.clientX;
    const sumVisible = visibleCols.reduce((s, c) => s + layout.widths[c.i], 0);
    const [w0, w1] = [layout.widths[leftCol], layout.widths[rightCol]];
    const onMove = (ev: PointerEvent) => {
      const delta = ((ev.clientX - startX) / total) * sumVisible;
      const a = Math.max(0.08 * sumVisible, Math.min(w0 + w1 - 0.08 * sumVisible, w0 + delta));
      setLayout((l) => {
        const widths = [...l.widths];
        widths[leftCol] = a;
        widths[rightCol] = w0 + w1 - a;
        return { ...l, widths };
      });
    };
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  };

  const startRowResize = (e: RPointerEvent, colEl: HTMLElement | null, top: PanelId, bottom: PanelId, panels: PanelId[]) => {
    e.preventDefault();
    const total = colEl?.getBoundingClientRect().height ?? 1;
    const startY = e.clientY;
    const sum = panels.reduce((s, p) => s + layout.grow[p], 0);
    const [g0, g1] = [layout.grow[top], layout.grow[bottom]];
    const onMove = (ev: PointerEvent) => {
      const delta = ((ev.clientY - startY) / total) * sum;
      const a = Math.max(0.1 * sum, Math.min(g0 + g1 - 0.1 * sum, g0 + delta));
      setLayout((l) => ({ ...l, grow: { ...l.grow, [top]: a, [bottom]: g0 + g1 - a } }));
    };
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  };

  return (
    <div className={`layout${dragging ? " is-dragging" : ""}`} ref={root} onDragEnd={() => { setDragging(null); setDropHint(null); }}>
      {visibleCols.map((c, vi) => {
        const colRef = { current: null as HTMLElement | null };
        return (
          <FragmentCol key={c.i}>
            {vi > 0 && <div className="splitter splitter-v" onPointerDown={(e) => startColResize(e, visibleCols[vi - 1].i, c.i)} />}
            <div
              className="column"
              ref={(el) => {
                colRef.current = el;
              }}
              style={{ flexGrow: c.panels.length ? layout.widths[c.i] : 0.06 }}
              onDragOver={(e) => {
                if (dragging && c.panels.length === 0) {
                  e.preventDefault();
                  setDropHint({ col: c.i, index: 0 });
                }
              }}
              onDrop={onDrop}
            >
              {c.panels.length === 0 && <div className={`drop-empty${dropHint?.col === c.i ? " drop-target" : ""}`}>Drop here</div>}
              {c.panels.map((p, pi) => (
                <FragmentCol key={p}>
                  {pi > 0 && <div className="splitter splitter-h" onPointerDown={(e) => startRowResize(e, colRef.current, c.panels[pi - 1], p, c.panels)} />}
                  <section
                    className={`panel panel-${p}${dragging === p ? " panel-dragging" : ""}${dropHint?.col === c.i && dropHint.index === pi ? " drop-before" : ""}${dropHint?.col === c.i && dropHint.index === pi + 1 && pi === c.panels.length - 1 ? " drop-after" : ""}`}
                    style={{ flexGrow: layout.grow[p] }}
                    onDragOver={(e) => onDragOverPanel(e, c.i, pi)}
                    onDrop={onDrop}
                    aria-label={PANEL_TITLES[p]}
                  >
                    <header
                      className="panel-head"
                      draggable
                      onDragStart={(e) => {
                        e.dataTransfer.effectAllowed = "move";
                        e.dataTransfer.setData("text/plain", p);
                        setDragging(p);
                      }}
                      title="Drag to move this Panel"
                    >
                      <span className="grip" aria-hidden>⠿</span>
                      <span className="panel-title">{PANEL_TITLES[p]}</span>
                      <span className="panel-extras">{headerExtras?.[p]}</span>
                      <button
                        className="icon-btn"
                        aria-label={`Hide ${PANEL_TITLES[p]}`}
                        title="Hide Panel"
                        onClick={() => setLayout((l) => ({ ...l, hidden: [...l.hidden, p] }))}
                      >
                        ×
                      </button>
                    </header>
                    <div className="panel-body">{render(p)}</div>
                  </section>
                </FragmentCol>
              ))}
            </div>
          </FragmentCol>
        );
      })}
    </div>
  );
}

function FragmentCol({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
