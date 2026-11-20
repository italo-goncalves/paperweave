import type { MouseEvent } from "react";
import { useReader } from "../state";

/** Click handler for rendered content: Inline links open Nodes, figure images open the lightbox. */
export function useContentClicks() {
  const { dispatch } = useReader();
  return (e: MouseEvent) => {
    const target = e.target as HTMLElement;
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
