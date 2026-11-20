import { createContext, useContext, useReducer, type Dispatch, type ReactNode } from "react";
import type { Tier, Work } from "./work";

export interface TrailItem {
  id: string;
  /** A tier chosen for this Node only; null follows the global Detail tier. */
  tier: Tier | null;
  collapsed: boolean;
}

export interface ReaderState {
  trail: TrailItem[];
  globalTier: Tier;
  /** The most recently opened Node; the Graph map highlights its Neighbourhood. */
  activeId: string | null;
  /** Incremented to ask the Reading panel to scroll to `activeId`. */
  scrollTick: number;
  /** An Equation label inside `activeId` to scroll to and highlight, if any. */
  anchor: string | null;
  figureMode: "trail" | "all";
  lightbox: string | null;
}

export type Action =
  | { type: "open"; id: string; fresh?: boolean; tier?: Tier; anchor?: string }
  | { type: "close"; id: string }
  | { type: "focus"; id: string }
  | { type: "setTier"; id: string; tier: Tier | null }
  | { type: "toggleCollapse"; id: string }
  | { type: "setGlobalTier"; tier: Tier }
  | { type: "setFigureMode"; mode: "trail" | "all" }
  | { type: "lightbox"; id: string | null }
  | { type: "clearTrail" };

function reducer(s: ReaderState, a: Action, rank: Record<string, number>): ReaderState {
  switch (a.type) {
    case "open": {
      const existing = s.trail.findIndex((t) => t.id === a.id);
      const moved = { activeId: a.id, scrollTick: s.scrollTick + 1, anchor: a.anchor ?? null };
      if (a.fresh) {
        return { ...s, ...moved, trail: [{ id: a.id, tier: a.tier ?? null, collapsed: false }] };
      }
      if (existing >= 0) {
        const trail = s.trail.map((t, i) => (i === existing ? { ...t, tier: a.tier ?? t.tier, collapsed: false } : t));
        return { ...s, ...moved, trail };
      }
      // The Trail is kept in Paper order, so a new Node lands where it sits in the Work.
      const item: TrailItem = { id: a.id, tier: a.tier ?? null, collapsed: false };
      const trail = [...s.trail, item].sort((p, q) => (rank[p.id] ?? 0) - (rank[q.id] ?? 0));
      return { ...s, ...moved, trail };
    }
    case "close": {
      const idx = s.trail.findIndex((t) => t.id === a.id);
      const trail = s.trail.filter((t) => t.id !== a.id);
      const activeId =
        s.activeId === a.id ? (trail[Math.min(idx, trail.length - 1)]?.id ?? null) : s.activeId;
      return { ...s, trail, activeId };
    }
    case "focus":
      return s.activeId === a.id ? s : { ...s, activeId: a.id };
    case "setTier":
      return { ...s, trail: s.trail.map((t) => (t.id === a.id ? { ...t, tier: a.tier, collapsed: false } : t)) };
    case "toggleCollapse":
      return { ...s, trail: s.trail.map((t) => (t.id === a.id ? { ...t, collapsed: !t.collapsed } : t)) };
    case "setGlobalTier":
      return { ...s, globalTier: a.tier };
    case "setFigureMode":
      return { ...s, figureMode: a.mode };
    case "lightbox":
      return { ...s, lightbox: a.id };
    case "clearTrail":
      return { ...s, trail: [], activeId: null };
  }
}

const initial: ReaderState = {
  trail: [],
  globalTier: "summary",
  activeId: null,
  scrollTick: 0,
  anchor: null,
  figureMode: "trail",
  lightbox: null,
};

const Ctx = createContext<{ work: Work; state: ReaderState; dispatch: Dispatch<Action> } | null>(null);

export function ReaderProvider({ work, children }: { work: Work; children: ReactNode }) {
  const [state, dispatch] = useReducer((s: ReaderState, a: Action) => reducer(s, a, work.paperRank), initial);
  return <Ctx.Provider value={{ work, state, dispatch }}>{children}</Ctx.Provider>;
}

export function useReader() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useReader outside ReaderProvider");
  return v;
}
