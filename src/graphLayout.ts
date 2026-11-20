/**
 * Layered (Sugiyama-style) layout of a Work for the Graph map. The layers follow the
 * Edges; the Trail uses the Paper order instead (src/paperOrder.ts, ADR 0003).
 *
 * 1. Each Edge is turned into a "comes before" pair (see `precedence`).
 * 2. Nodes get layers: Context at the top, the Conclusion alone at the bottom, and
 *    everything else as close as possible to the Nodes that come after it.
 * 3. Edges spanning several layers get dummy points, and each layer is reordered by
 *    barycentre sweeps, keeping the order with the fewest crossings.
 * 4. x positions are relaxed towards neighbours while keeping a minimum gap.
 *
 * The result is computed once per Work and never changes while reading.
 */
import type { Edge, Work } from "./work";

export interface Point {
  x: number;
  y: number;
}

export interface GraphLayout {
  pos: Record<string, Point>;
  layer: Record<string, number>;
  /** All Node ids by layer, then left to right. */
  order: string[];
  /** Index of each Node in `order`. */
  rank: Record<string, number>;
  /** Bend points (dummy positions) for each Edge, from the Edge's source to its target. */
  bends: Map<Edge, Point[]>;
  /** Total crossings between adjacent layers in the chosen order. */
  crossings: number;
}

const LAYER_GAP = 105;
const NODE_GAP = 128;
const DUMMY_GAP = 28;

/** [before, after] for an Edge, top to bottom in the Graph map. */
export function precedence(e: Edge): [string, string] {
  switch (e.type) {
    case "explains": // a Primer is read before the Concept it explains
    case "situates": // Context comes first
    case "supports": // the supporting Result comes first
      return [e.from, e.to];
    default: // uses, relies_on, discusses, synthesises: the target comes first
      return [e.to, e.from];
  }
}

interface LNode {
  id: string;
  dummy: boolean;
  layer: number;
  up: string[]; // neighbours in layer - 1
  down: string[]; // neighbours in layer + 1
}

/** `restarts` and `sweeps` trade start-up time for fewer crossings. */
export function layoutWork(work: Work, { restarts = 24, sweeps = 12 } = {}): GraphLayout {
  const ids = Object.keys(work.nodes).sort();
  const before = new Map<string, Set<string>>(ids.map((id) => [id, new Set()]));
  const after = new Map<string, Set<string>>(ids.map((id) => [id, new Set()]));
  for (const e of work.edges) {
    const [a, b] = precedence(e);
    if (a === b) continue;
    after.get(a)!.add(b);
    before.get(b)!.add(a);
  }

  // Topological order (Kahn), breaking any cycle at the Node with fewest remaining predecessors.
  const indeg = new Map(ids.map((id) => [id, before.get(id)!.size]));
  const done = new Set<string>();
  const topo: string[] = [];
  while (topo.length < ids.length) {
    let next = ids.find((id) => !done.has(id) && indeg.get(id) === 0);
    if (!next) {
      next = ids.filter((id) => !done.has(id)).sort((x, y) => indeg.get(x)! - indeg.get(y)!)[0];
      console.warn(`Graph layers have a cycle; breaking it at ${next}`);
    }
    done.add(next);
    topo.push(next);
    for (const s of after.get(next)!) indeg.set(s, indeg.get(s)! - 1);
  }
  const pos = new Map(topo.map((id, i) => [id, i]));
  const preds = (id: string) => [...before.get(id)!].filter((p) => pos.get(p)! < pos.get(id)!);
  const succs = (id: string) => [...after.get(id)!].filter((s) => pos.get(s)! > pos.get(id)!);

  // Layers: as early as possible first, then pull every non-Context Node down
  // to just above its earliest successor, so dependencies sit near their users.
  const layer: Record<string, number> = {};
  for (const id of topo) layer[id] = Math.max(0, ...preds(id).map((p) => layer[p] + 1));
  for (const id of [...topo].reverse()) {
    const type = work.nodes[id].type;
    const s = succs(id);
    if (type !== "context" && type !== "conclusion" && s.length) layer[id] = Math.min(...s.map((x) => layer[x])) - 1;
  }
  // All Results share one band, so the Work's findings line up side by side;
  // then push anything that must come after a Result further down.
  const resultIds = ids.filter((id) => work.nodes[id].type === "result");
  if (resultIds.length) {
    const band = Math.max(...resultIds.map((id) => layer[id]));
    for (const id of resultIds) layer[id] = band;
    for (const id of topo) for (const p of preds(id)) layer[id] = Math.max(layer[id], layer[p] + 1);
  }
  const conclusionLayer = Math.max(0, ...ids.filter((id) => work.nodes[id].type !== "conclusion").map((id) => layer[id])) + 1;
  for (const id of ids) if (work.nodes[id].type === "conclusion") layer[id] = conclusionLayer;
  // Drop empty layers.
  const used = [...new Set(Object.values(layer))].sort((a, b) => a - b);
  for (const id of ids) layer[id] = used.indexOf(layer[id]);
  const nLayers = used.length;

  // Layered graph with dummy chains for long Edges (one chain per before/after pair).
  const lnodes = new Map<string, LNode>(ids.map((id) => [id, { id, dummy: false, layer: layer[id], up: [], down: [] }]));
  const chains = new Map<string, string[]>(); // "a>b" → [a, d1, ..., b]
  for (const [a, set] of after) {
    for (const b of set) {
      const [top, bottom] = layer[a] < layer[b] ? [a, b] : [b, a];
      const key = `${a}>${b}`;
      if (chains.has(key)) continue;
      const chain = [top];
      for (let l = layer[top] + 1; l < layer[bottom]; l++) {
        const d = `__d:${key}:${l}`;
        lnodes.set(d, { id: d, dummy: true, layer: l, up: [], down: [] });
        chain.push(d);
      }
      chain.push(bottom);
      for (let i = 0; i + 1 < chain.length; i++) {
        lnodes.get(chain[i])!.down.push(chain[i + 1]);
        lnodes.get(chain[i + 1])!.up.push(chain[i]);
      }
      chains.set(key, chain);
    }
  }

  // Initial order: by type, then by first appearance in the topological order.
  const typeOrder = ["context", "primer", "concept", "method", "result", "discussion", "conclusion"];
  let layers: string[][] = Array.from({ length: nLayers }, () => []);
  for (const n of lnodes.values()) layers[n.layer].push(n.id);
  const initKey = (id: string) => {
    const n = lnodes.get(id)!;
    return n.dummy ? 1e6 : typeOrder.indexOf(work.nodes[id].type) * 1000 + pos.get(id)!;
  };
  layers = layers.map((l) => l.sort((a, b) => initKey(a) - initKey(b)));

  const crossingsBetween = (upper: string[], lower: string[]) => {
    const idx = new Map(lower.map((id, i) => [id, i]));
    const segs: [number, number][] = [];
    upper.forEach((u, i) => lnodes.get(u)!.down.forEach((d) => segs.push([i, idx.get(d)!])));
    let c = 0;
    for (let i = 0; i < segs.length; i++)
      for (let j = i + 1; j < segs.length; j++)
        if ((segs[i][0] - segs[j][0]) * (segs[i][1] - segs[j][1]) < 0) c++;
    return c;
  };
  const totalCrossings = (ls: string[][]) => ls.slice(1).reduce((s, l, i) => s + crossingsBetween(ls[i], l), 0);

  // Barycentre / median sweeps with transposition, from several starting orders
  // (the type-based one plus seeded shuffles); keep the fewest crossings found.
  const sweep = (start: string[][], useMedian: boolean) => {
    const ls = start.map((l) => [...l]);
    let localBest = ls.map((l) => [...l]);
    let localC = totalCrossings(ls);
    for (let iter = 0; iter < sweeps && localC > 0; iter++) {
      const down = iter % 2 === 0;
      const range = down ? [...Array(nLayers).keys()].slice(1) : [...Array(nLayers).keys()].slice(0, -1).reverse();
      for (const l of range) {
        const ref = new Map(ls[down ? l - 1 : l + 1].map((id, i) => [id, i]));
        const key = new Map(
          ls[l].map((id, i) => {
            const nb = (down ? lnodes.get(id)!.up : lnodes.get(id)!.down).map((v) => ref.get(v)!).sort((a, b) => a - b);
            if (!nb.length) return [id, i] as [string, number];
            const v = useMedian ? (nb.length % 2 ? nb[(nb.length - 1) / 2] : (nb[nb.length / 2 - 1] + nb[nb.length / 2]) / 2) : nb.reduce((s, q) => s + q, 0) / nb.length;
            return [id, v] as [string, number];
          }),
        );
        ls[l] = [...ls[l]].sort((a, b) => key.get(a)! - key.get(b)!);
      }
      // Transpose: swap adjacent Nodes while it reduces crossings. Only the Edges of
      // the two Nodes being swapped change, so compare just those.
      const pairCrossings = (u: string, v: string, l: number) => {
        let c = 0;
        for (const [nbs, ref] of [
          ["up", l > 0 ? ls[l - 1] : null],
          ["down", l + 1 < nLayers ? ls[l + 1] : null],
        ] as const) {
          if (!ref) continue;
          const idx = new Map(ref.map((id, i) => [id, i]));
          for (const a of lnodes.get(u)![nbs]) for (const b of lnodes.get(v)![nbs]) if (idx.get(a)! > idx.get(b)!) c++;
        }
        return c;
      };
      let improved = true;
      while (improved) {
        improved = false;
        for (let l = 0; l < nLayers; l++) {
          for (let i = 0; i + 1 < ls[l].length; i++) {
            const [u, v] = [ls[l][i], ls[l][i + 1]];
            if (pairCrossings(v, u, l) < pairCrossings(u, v, l)) {
              [ls[l][i], ls[l][i + 1]] = [v, u];
              improved = true;
            }
          }
        }
      }
      const c = totalCrossings(ls);
      if (c < localC) {
        localC = c;
        localBest = ls.map((q) => [...q]);
      }
    }
    return { order: localBest, c: localC };
  };

  let seed = 12345;
  const rand = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
  const shuffled = () =>
    layers.map((l) => {
      const a = [...l];
      for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(rand() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
      }
      return a;
    });
  let best = { order: layers, c: totalCrossings(layers) };
  const starts = [layers, ...Array.from({ length: restarts }, shuffled)];
  for (const s of starts) {
    for (const useMedian of [false, true]) {
      const r = sweep(s, useMedian);
      if (r.c < best.c) best = r;
      if (best.c === 0) break;
    }
  }
  layers = best.order;
  const bestC = best.c;

  // x coordinates: start packed, then relax towards neighbours, keeping order and gaps.
  const x = new Map<string, number>();
  const gap = (a: string, b: string) => (lnodes.get(a)!.dummy && lnodes.get(b)!.dummy ? DUMMY_GAP : lnodes.get(a)!.dummy || lnodes.get(b)!.dummy ? (NODE_GAP + DUMMY_GAP) / 2 : NODE_GAP);
  for (const l of layers) {
    let cx = 0;
    l.forEach((id, i) => {
      if (i > 0) cx += gap(l[i - 1], id);
      x.set(id, cx);
    });
    const shift = cx / 2;
    l.forEach((id) => x.set(id, x.get(id)! - shift));
  }
  for (let iter = 0; iter < 40; iter++) {
    const down = iter % 2 === 0;
    const order = down ? layers : [...layers].reverse();
    for (const l of order) {
      const want = l.map((id) => {
        const n = lnodes.get(id)!;
        const nb = [...n.up, ...n.down];
        return nb.length ? nb.reduce((s, v) => s + x.get(v)!, 0) / nb.length : x.get(id)!;
      });
      // Pack towards the wanted spots once pushing right and once pushing left, then
      // average: both satisfy the gaps, so their mean does too, without a one-sided drift.
      const right: number[] = [];
      l.forEach((id, i) => (right[i] = i === 0 ? want[i] : Math.max(want[i], right[i - 1] + gap(l[i - 1], id))));
      const left: number[] = [];
      for (let i = l.length - 1; i >= 0; i--) left[i] = i === l.length - 1 ? want[i] : Math.min(want[i], left[i + 1] - gap(l[i], l[i + 1]));
      l.forEach((id, i) => x.set(id, (left[i] + right[i]) / 2));
    }
  }

  const point = (id: string): Point => ({ x: x.get(id)!, y: lnodes.get(id)!.layer * LAYER_GAP });
  const posOut: Record<string, Point> = {};
  for (const id of ids) posOut[id] = point(id);

  const bends = new Map<Edge, Point[]>();
  for (const e of work.edges) {
    const [a, b] = precedence(e);
    const chain = chains.get(`${a}>${b}`);
    if (!chain || chain.length <= 2) continue;
    const pts = chain.slice(1, -1).map(point);
    // Chains run top to bottom; give the points from the Edge's source to its target.
    bends.set(e, chain[0] === e.from ? pts : pts.reverse());
  }

  const order = [...ids].sort((p, q) => layer[p] - layer[q] || posOut[p].x - posOut[q].x);
  const rank = Object.fromEntries(order.map((id, i) => [id, i]));
  return { pos: posOut, layer, order, rank, bends, crossings: bestC };
}
