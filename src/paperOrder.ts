/**
 * The Paper order of a Work (ADR 0003): one linear order of its Nodes, used by the
 * Trail, by Work → LaTeX and by the Linear version.
 *
 * Context, then Concepts (each followed by the Primers that explain it), Methods,
 * Results, Discussions and the Conclusion. Within a type, Edges put what a Node depends
 * on first. Remaining ties go by:
 *   - Results: the Results list order;
 *   - Methods: the first Result that uses them, directly or through other Methods;
 *   - Concepts: the first Result, then the first Method, that relies on them;
 *   - Discussions: the earliest Node they discuss; Contexts: the earliest Node they situate;
 *   - finally the Node id.
 * A stored `order` (from a Work written in LaTeX) replaces all of this.
 *
 * `scripts/workformat.py` implements the same rules; `scripts/test_paper_order.py`
 * checks that both give the same order.
 *
 * Self-contained (type imports only) so Node can run it without a bundler.
 */
import type { Edge, NodeType } from "./work";

export interface OrderInput {
  nodes: Record<string, { type: NodeType }>;
  edges: Edge[];
  results: string[];
  order?: string[];
}

export const PAPER_GROUPS: NodeType[][] = [["context"], ["concept", "primer"], ["method"], ["result"], ["discussion"], ["conclusion"]];

const INF = Number.MAX_SAFE_INTEGER;

type Key = (number | string)[];

function compareKeys(a: Key, b: Key): number {
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const x = a[i];
    const y = b[i];
    if (x === y) continue;
    if (typeof x === "number" && typeof y === "number") return x - y;
    return String(x) < String(y) ? -1 : 1;
  }
  return 0;
}

/** Kahn's algorithm over `ids`, where `before[id]` must precede `id`, always taking the smallest key. */
function sortWithin(ids: string[], before: Map<string, Set<string>>, key: (id: string) => Key): string[] {
  const left = new Set(ids);
  const out: string[] = [];
  while (left.size) {
    const remaining = [...left].sort((a, b) => compareKeys(key(a), key(b)));
    const ready = remaining.filter((id) => ![...(before.get(id) ?? [])].some((p) => left.has(p)));
    const next = ready[0] ?? remaining[0]; // a cycle: break it at the smallest key
    out.push(next);
    left.delete(next);
  }
  return out;
}

export function paperOrder(work: OrderInput): string[] {
  if (work.order?.length) return [...work.order];
  const ids = Object.keys(work.nodes).sort();
  const ofType = (t: NodeType) => ids.filter((id) => work.nodes[id].type === t);
  const typeOf = (id: string) => work.nodes[id]?.type;
  const edges = work.edges.filter((e) => work.nodes[e.from] && work.nodes[e.to]);

  // Within-type precedence: [before, after] for Edges between two Nodes of the same type.
  const before = new Map<string, Set<string>>(ids.map((id) => [id, new Set()]));
  for (const e of edges) {
    if (typeOf(e.from) !== typeOf(e.to) || e.from === e.to) continue;
    const [a, b] = e.type === "supports" || e.type === "situates" ? [e.from, e.to] : [e.to, e.from];
    before.get(b)!.add(a);
  }

  // Who depends on whom, through uses and relies_on, transitively.
  const users = new Map<string, Set<string>>(ids.map((id) => [id, new Set()]));
  for (const e of edges) if (e.type === "uses" || e.type === "relies_on") users.get(e.to)!.add(e.from);
  const dependents = (id: string) => {
    const seen = new Set<string>();
    const stack = [...users.get(id)!];
    while (stack.length) {
      const u = stack.pop()!;
      if (seen.has(u) || u === id) continue;
      seen.add(u);
      stack.push(...users.get(u)!);
    }
    return seen;
  };

  const positions = (list: string[]) => new Map(list.map((id, i) => [id, i]));
  const minPos = (pos: Map<string, number>, set: Iterable<string>, t?: NodeType) => {
    let m = INF;
    for (const id of set) if ((!t || typeOf(id) === t) && pos.has(id)) m = Math.min(m, pos.get(id)!);
    return m;
  };

  const resultIndex = (id: string) => {
    const i = work.results.indexOf(id);
    return i < 0 ? INF : i;
  };
  const results = sortWithin(ofType("result"), before, (id) => [resultIndex(id), id]);
  const resultPos = positions(results);
  const methods = sortWithin(ofType("method"), before, (id) => [minPos(resultPos, dependents(id)), id]);
  const methodPos = positions(methods);
  const concepts = sortWithin(ofType("concept"), before, (id) => {
    const d = dependents(id);
    return [minPos(resultPos, d), minPos(methodPos, d), id];
  });

  // Each Primer follows the first Concept it explains; Primers explaining none close the group.
  const primerHome = new Map<string, number>();
  for (const p of ofType("primer")) {
    const explained = edges.filter((e) => e.type === "explains" && e.from === p).map((e) => e.to);
    primerHome.set(p, Math.min(INF, ...explained.map((c) => concepts.indexOf(c)).filter((i) => i >= 0)));
  }
  const primers = ofType("primer").sort((a, b) => compareKeys([primerHome.get(a)!, a], [primerHome.get(b)!, b]));
  const conceptGroup: string[] = [];
  concepts.forEach((c, i) => conceptGroup.push(c, ...primers.filter((p) => primerHome.get(p) === i)));
  conceptGroup.push(...primers.filter((p) => primerHome.get(p) === INF));

  const targets = (id: string, type: Edge["type"]) => edges.filter((e) => e.type === type && e.from === id).map((e) => e.to);
  const bodyPos = positions([...conceptGroup, ...methods, ...results]);
  const discussions = sortWithin(ofType("discussion"), before, (id) => [minPos(bodyPos, targets(id, "discusses")), id]);
  const conclusions = ofType("conclusion");
  const restPos = positions([...conceptGroup, ...methods, ...results, ...discussions, ...conclusions]);
  const contexts = sortWithin(ofType("context"), before, (id) => [minPos(restPos, targets(id, "situates")), id]);

  return [...contexts, ...conceptGroup, ...methods, ...results, ...discussions, ...conclusions];
}

/** Group index of a Node type in the Paper order. */
export function paperGroup(type: NodeType): number {
  return PAPER_GROUPS.findIndex((g) => g.includes(type));
}
