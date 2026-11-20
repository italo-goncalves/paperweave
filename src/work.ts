import yaml from "js-yaml";
import { layoutWork, type GraphLayout } from "./graphLayout";

export const NODE_TYPES = ["result", "method", "concept", "primer", "context", "discussion", "conclusion"] as const;
export type NodeType = (typeof NODE_TYPES)[number];

export const TIERS = ["gist", "summary", "full"] as const;
export type Tier = (typeof TIERS)[number];

export const EDGE_TYPES = ["uses", "relies_on", "supports", "explains", "discusses", "situates", "synthesises"] as const;
export type EdgeType = (typeof EDGE_TYPES)[number];

/** How an Edge reads from each end, for relation lists in the Reading panel. */
export const EDGE_LABELS: Record<EdgeType, { out: string; in: string }> = {
  uses: { out: "Uses", in: "Used by" },
  relies_on: { out: "Relies on", in: "Relied on by" },
  supports: { out: "Supports", in: "Supported by" },
  explains: { out: "Explains", in: "Primer" },
  discusses: { out: "Discusses", in: "Discussed in" },
  situates: { out: "Situates", in: "Context" },
  synthesises: { out: "Synthesises", in: "Synthesised in" },
};

export const TYPE_LABELS: Record<NodeType, string> = {
  result: "Result",
  method: "Method",
  concept: "Concept",
  primer: "Primer",
  context: "Context",
  discussion: "Discussion",
  conclusion: "Conclusion",
};

export interface Edge {
  type: EdgeType;
  from: string;
  to: string;
}

export interface WorkNode {
  id: string;
  type: NodeType;
  title: string;
  contribution: boolean;
  /** Raw Markdown per Detail tier. Primers store their single level as `full`. */
  tiers: Partial<Record<Tier, string>>;
  /** Figure ids referenced anywhere in the Node, in order of appearance. */
  figures: string[];
}

export interface Figure {
  id: string;
  url: string;
  caption: string;
}

export interface Reference {
  label: string;
  text: string;
}

export interface Work {
  id: string;
  title: string;
  authors: string[];
  year?: number;
  venue?: string;
  doi?: string;
  code?: string;
  abstract: string;
  results: string[];
  conclusion: string;
  figures: Record<string, Figure>;
  references: Record<string, Reference>;
  nodes: Record<string, WorkNode>;
  edges: Edge[];
  /** Fixed Graph map positions and the Reading order. */
  layout: GraphLayout;
}

const manifests = import.meta.glob("/works/*/manifest.yaml", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const referenceFiles = import.meta.glob("/works/*/references.yaml", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const nodeFiles = import.meta.glob("/works/*/nodes/*.md", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const figureFiles = import.meta.glob("/works/*/figures/*", { query: "?url", import: "default", eager: true }) as Record<string, string>;

const FIGURE_REF = /!\[\[([a-z0-9-]+)\]\]/g;

function parseNode(id: string, text: string): { node: WorkNode; edges: Edge[] } {
  const m = text.replace(/\r\n/g, "\n").match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!m) throw new Error(`Node ${id} has no YAML header`);
  const meta = yaml.load(m[1]) as Record<string, unknown>;
  const body = m[2];
  const type = meta.type as NodeType;

  const tiers: Partial<Record<Tier, string>> = {};
  if (type === "primer") {
    tiers.full = body.trim();
  } else {
    const parts = body.split(/^## (Gist|Summary|Full)\s*$/m);
    for (let i = 1; i < parts.length; i += 2) {
      tiers[parts[i].toLowerCase() as Tier] = parts[i + 1].trim();
    }
  }

  const figures = [...new Set([...body.matchAll(FIGURE_REF)].map((f) => f[1]))];
  const edges: Edge[] = [];
  for (const [key, targets] of Object.entries((meta.edges as Record<string, string[]>) ?? {})) {
    for (const to of targets) edges.push({ type: key as EdgeType, from: id, to });
  }

  return {
    node: { id, type, title: String(meta.title ?? id), contribution: meta.contribution === true, tiers, figures },
    edges,
  };
}

function loadWork(dir: string): Work {
  const manifest = yaml.load(manifests[`${dir}/manifest.yaml`]) as Record<string, any>;
  const references = (yaml.load(referenceFiles[`${dir}/references.yaml`] ?? "{}") ?? {}) as Record<string, Reference>;

  const nodes: Record<string, WorkNode> = {};
  const edges: Edge[] = [];
  for (const [path, text] of Object.entries(nodeFiles)) {
    if (!path.startsWith(`${dir}/nodes/`)) continue;
    const id = path.slice(path.lastIndexOf("/") + 1, -3);
    const parsed = parseNode(id, text);
    nodes[id] = parsed.node;
    edges.push(...parsed.edges);
  }

  const figures: Record<string, Figure> = {};
  for (const [id, f] of Object.entries((manifest.figures ?? {}) as Record<string, { file: string; caption: string }>)) {
    figures[id] = { id, url: figureFiles[`${dir}/${f.file}`] ?? "", caption: f.caption ?? "" };
  }

  const work: Omit<Work, "layout"> = {
    id: manifest.id,
    title: manifest.title,
    authors: manifest.authors ?? [],
    year: manifest.year,
    venue: manifest.venue,
    doi: manifest.doi,
    code: manifest.code,
    abstract: manifest.abstract ?? "",
    results: manifest.results ?? [],
    conclusion: manifest.conclusion,
    figures,
    references,
    nodes,
    edges: edges.filter((e) => nodes[e.to]),
  };
  return { ...work, layout: layoutWork(work as Work) };
}

export const works: Work[] = Object.keys(manifests)
  .map((p) => p.slice(0, -"/manifest.yaml".length))
  .sort()
  .map(loadWork);

/** The tier actually shown: the requested one, or the next shorter one that exists. */
export function effectiveTier(node: WorkNode, wanted: Tier): Tier {
  const order = TIERS.slice(0, TIERS.indexOf(wanted) + 1).reverse();
  for (const t of order) if (node.tiers[t] !== undefined) return t;
  return TIERS.find((t) => node.tiers[t] !== undefined) ?? "gist";
}

export function outgoing(work: Work, id: string): Edge[] {
  return work.edges.filter((e) => e.from === id);
}

export function incoming(work: Work, id: string): Edge[] {
  return work.edges.filter((e) => e.to === id);
}

/** The Neighbourhood: a Node and every Node one Edge away from it, in either direction. */
export function neighbourhood(work: Work, id: string): Set<string> {
  const out = new Set([id]);
  for (const e of work.edges) {
    if (e.from === id) out.add(e.to);
    if (e.to === id) out.add(e.from);
  }
  return out;
}

/** Nodes whose content shows a Figure. */
export function figureOwners(work: Work, figureId: string): WorkNode[] {
  return Object.values(work.nodes).filter((n) => n.figures.includes(figureId));
}
