import { useEffect, useMemo, useRef, useState } from "react";
import cytoscape, { type Core } from "cytoscape";
import { useReader } from "../state";
import { plainTitle } from "../render";
import { EDGE_LABELS, NODE_TYPES, TYPE_LABELS, neighbourhood, type Work } from "../work";
import type { Point } from "../graphLayout";

function cssVar(name: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function useColorScheme() {
  const [dark, setDark] = useState(() => window.matchMedia("(prefers-color-scheme: dark)").matches);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const on = () => setDark(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return dark;
}

/**
 * Cytoscape's `segments` edges place bends as (weight along source→target, perpendicular distance).
 * Convert absolute bend points into those two lists.
 */
function segmentData(s: Point, t: Point, bends: Point[]) {
  const dx = t.x - s.x;
  const dy = t.y - s.y;
  const len2 = dx * dx + dy * dy || 1;
  const len = Math.sqrt(len2);
  const weights: number[] = [];
  const distances: number[] = [];
  for (const b of bends) {
    const px = b.x - s.x;
    const py = b.y - s.y;
    weights.push((px * dx + py * dy) / len2);
    // Cytoscape measures segment distances with the opposite perpendicular sign.
    distances.push((py * dx - px * dy) / len);
  }
  return { weights: weights.join(" "), distances: distances.join(" ") };
}

function elements(work: Work): cytoscape.ElementDefinition[] {
  const { pos, bends } = work.layout;
  const nodes = Object.values(work.nodes).map((n) => ({
    group: "nodes" as const,
    data: { id: n.id, label: (n.contribution ? "★ " : "") + plainTitle(n.title), type: n.type },
    position: { ...pos[n.id] },
  }));
  const edges = work.edges.map((e, i) => {
    const b = bends.get(e);
    const seg = b ? segmentData(pos[e.from], pos[e.to], b) : null;
    return {
      group: "edges" as const,
      data: {
        id: `e${i}`,
        source: e.from,
        target: e.to,
        label: EDGE_LABELS[e.type].out.toLowerCase(),
        ...(seg ? { sw: seg.weights, sd: seg.distances } : {}),
      },
      classes: seg ? "routed" : "",
    };
  });
  return [...nodes, ...edges];
}

function buildStyle(): cytoscape.StylesheetJson {
  return [
    {
      selector: "node",
      style: {
        label: "data(label)",
        "font-size": 11,
        "font-family": cssVar("--font-ui") || "system-ui, sans-serif",
        color: cssVar("--text"),
        "text-wrap": "wrap",
        "text-max-width": "112px",
        "text-valign": "bottom",
        "text-margin-y": 4,
        width: 18,
        height: 18,
        "border-width": 0,
        "text-background-color": cssVar("--bg-panel"),
        "text-background-opacity": 0.85,
        "text-background-padding": "1px",
        "transition-property": "opacity",
        "transition-duration": 150,
      },
    },
    ...NODE_TYPES.map((t) => ({ selector: `node[type = "${t}"]`, style: { "background-color": cssVar(`--type-${t}`) } })),
    { selector: 'node[type = "result"], node[type = "conclusion"]', style: { shape: "round-rectangle", width: 24, height: 24 } },
    { selector: 'node[type = "primer"]', style: { shape: "diamond" } },
    { selector: "node.in-trail", style: { "border-width": 3, "border-color": cssVar("--accent") } },
    { selector: "node.active", style: { width: 30, height: 30, "font-weight": "bold", "border-width": 4, "border-color": cssVar("--accent") } },
    {
      selector: "edge",
      style: {
        width: 1.2,
        "line-color": cssVar("--edge"),
        "target-arrow-color": cssVar("--edge"),
        "target-arrow-shape": "triangle",
        "arrow-scale": 0.8,
        "curve-style": "straight",
        label: "data(label)",
        "font-size": 9,
        color: cssVar("--text-muted"),
        "text-rotation": "autorotate",
        "text-background-color": cssVar("--bg-panel"),
        "text-background-opacity": 0.85,
        "text-opacity": 0,
        "transition-property": "opacity",
        "transition-duration": 150,
      },
    },
    {
      selector: "edge.routed",
      style: { "curve-style": "segments", "segment-weights": "data(sw)", "segment-distances": "data(sd)", "edge-distances": "node-position" },
    },
    { selector: "edge.near-active", style: { "text-opacity": 1, width: 2, "line-color": cssVar("--accent"), "target-arrow-color": cssVar("--accent") } },
    { selector: ".dimmed", style: { opacity: 0.15 } },
    { selector: "node.in-trail.dimmed", style: { opacity: 0.5 } },
  ];
}

export function GraphMap() {
  const { work, state, dispatch } = useReader();
  const container = useRef<HTMLDivElement>(null);
  const cy = useRef<Core | null>(null);
  const userMoved = useRef(false);
  const fitRef = useRef<() => void>(() => {});
  const dark = useColorScheme();

  // Built once per Work, with fixed positions; reading never moves anything.
  useEffect(() => {
    if (!container.current) return;
    const instance = cytoscape({
      container: container.current,
      elements: elements(work),
      style: buildStyle(),
      layout: { name: "preset", fit: true, padding: 24 },
      minZoom: 0.15,
      maxZoom: 3,
      autoungrabify: true,
    });
    instance.on("tap", "node", (e) => dispatch({ type: "open", id: e.target.id() }));
    cy.current = instance;
    // Refit when the Panel changes size, until the Reader pans or zooms by hand.
    const el = container.current;
    userMoved.current = false;
    let programmatic = false;
    fitRef.current = () => {
      programmatic = true;
      instance.fit(undefined, 24);
      programmatic = false;
      userMoved.current = false;
    };
    instance.on("viewport", () => {
      if (!programmatic) userMoved.current = true;
    });
    const ro = new ResizeObserver(() => {
      instance.resize();
      if (!userMoved.current) fitRef.current();
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
      instance.destroy();
      cy.current = null;
    };
  }, [work, dispatch]);

  useEffect(() => {
    cy.current?.style(buildStyle());
  }, [dark]);

  const focus = useMemo(() => (state.activeId ? neighbourhood(work, state.activeId) : null), [work, state.activeId]);

  // Highlight the Neighbourhood and the Trail; dim everything else. No panning or zooming.
  const trailKey = state.trail.map((t) => t.id).join(",");
  useEffect(() => {
    const c = cy.current;
    if (!c) return;
    const inTrail = new Set(state.trail.map((t) => t.id));
    c.batch(() => {
      c.nodes().forEach((n) => {
        n.toggleClass("in-trail", inTrail.has(n.id()));
        n.toggleClass("active", n.id() === state.activeId);
        n.toggleClass("dimmed", !!focus && !focus.has(n.id()));
      });
      c.edges().forEach((e) => {
        const near = e.source().id() === state.activeId || e.target().id() === state.activeId;
        e.toggleClass("near-active", near);
        e.toggleClass("dimmed", !!focus && !near);
      });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trailKey, state.activeId, focus]);

  const active = state.activeId ? work.nodes[state.activeId] : null;
  return (
    <div className="graph">
      <div className="graph-bar">
        <span>
          {active
            ? `“${plainTitle(active.title)}” and its ${(focus?.size ?? 1) - 1} neighbours`
            : `${Object.keys(work.nodes).length} Nodes in Reading order, from Context to Conclusion`}
        </span>
        {active && (
          <button className="link-btn" onClick={() => dispatch({ type: "clearTrail" })} title="Clear the Trail and the highlight">
            Clear
          </button>
        )}
        <button
          className="link-btn"
          onClick={() => fitRef.current()}
        >
          Fit
        </button>
      </div>
      <div className="graph-canvas" ref={container} />
      <div className="legend">
        {NODE_TYPES.map((t) => (
          <span key={t} className="legend-item">
            <span className={`dot dot-${t}`} />
            {TYPE_LABELS[t]}
          </span>
        ))}
        <span className="legend-item">
          <span className="dot dot-trail" />
          In Trail
        </span>
      </div>
    </div>
  );
}
