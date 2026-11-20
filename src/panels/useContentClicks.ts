import type { MouseEvent } from "react";
import { useReader } from "../state";
import { effectiveTier } from "../work";

/**
 * Click handler for rendered content: Inline links open Nodes, equation references open the
 * Node holding the equation (at a tier that shows it) and scroll to it, figure images open
 * the lightbox.
 */
export function useContentClicks() {
  const { work, state, dispatch } = useReader();
  return (e: MouseEvent) => {
    const target = e.target as HTMLElement;
    const ref = target.closest<HTMLElement>("a[data-eq]");
    if (ref) {
      e.preventDefault();
      e.stopPropagation();
      const eq = work.equations[ref.dataset.eq!];
      const node = eq && work.nodes[eq.node];
      if (!eq || !node) return;
      const item = state.trail.find((t) => t.id === node.id);
      const shown = node.type === "primer" ? "full" : effectiveTier(node, item?.tier ?? state.globalTier);
      const tier = eq.tiers.includes(shown) ? undefined : eq.tiers[0];
      dispatch({ type: "open", id: node.id, tier, anchor: eq.label });
      return;
    }
    const link = target.closest<HTMLElement>("a[data-node]");
    if (link) {
      e.preventDefault();
      e.stopPropagation();
      dispatch({ type: "open", id: link.dataset.node! });
      return;
    }
    const img = target.closest<HTMLElement>("img[data-fig]");
    if (img) {
      e.stopPropagation();
      dispatch({ type: "lightbox", id: img.dataset.fig! });
    }
  };
}
