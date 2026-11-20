/**
 * Equation labels: `$$…$$ {#eq-name}` numbers a display equation, `[[#eq-name]]` refers to it.
 *
 * Numbers run across the Work in Paper order and, within a Node, by first appearance in
 * Gist, Summary, then Full, so they never depend on what is open or printed. The PaperWeave
 * class numbers equations the same way in the Linear version.
 */
import type { Tier, WorkNode } from "./work";

export interface Equation {
  label: string;
  number: number;
  /** The Node that holds it. */
  node: string;
  tex: string;
  /** Detail tiers of that Node in which it appears, shortest first. */
  tiers: Tier[];
}

export const LABELLED_DISPLAY = /\$\$([\s\S]+?)\$\$[ \t]*\{#(eq-[a-z0-9-]+)\}/g;
export const EQUATION_REF = /\[\[#(eq-[a-z0-9-]+)\]\]/g;

const TIER_ORDER: Tier[] = ["gist", "summary", "full"];

export function numberEquations(nodes: Record<string, WorkNode>, paperOrder: string[]): Record<string, Equation> {
  const out: Record<string, Equation> = {};
  let n = 0;
  for (const id of paperOrder) {
    const node = nodes[id];
    if (!node) continue;
    for (const tier of TIER_ORDER) {
      const text = node.tiers[tier];
      if (!text) continue;
      for (const m of text.matchAll(LABELLED_DISPLAY)) {
        const label = m[2];
        const eq = out[label];
        if (!eq) out[label] = { label, number: ++n, node: id, tex: m[1], tiers: [tier] };
        else if (eq.node === id && !eq.tiers.includes(tier)) eq.tiers.push(tier);
      }
    }
  }
  return out;
}
