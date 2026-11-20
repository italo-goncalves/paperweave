import { useEffect, useState } from "react";
import { useReader } from "../state";
import { renderInline, renderMath } from "../render";

/** Shows a referenced equation while the pointer is over its "(3)" reference. */
export function EquationPopover() {
  const { work } = useReader();
  const [shown, setShown] = useState<{ label: string; x: number; y: number; below: boolean } | null>(null);

  useEffect(() => {
    const over = (e: MouseEvent) => {
      const ref = (e.target as HTMLElement).closest?.<HTMLElement>("a.eq-ref[data-eq]");
      if (!ref) return;
      const r = ref.getBoundingClientRect();
      const below = r.top < window.innerHeight / 2;
      setShown({ label: ref.dataset.eq!, x: r.left + r.width / 2, y: below ? r.bottom + 8 : r.top - 8, below });
    };
    const out = (e: MouseEvent) => {
      if ((e.target as HTMLElement).closest?.("a.eq-ref[data-eq]")) setShown(null);
    };
    document.addEventListener("mouseover", over);
    document.addEventListener("mouseout", out);
    return () => {
      document.removeEventListener("mouseover", over);
      document.removeEventListener("mouseout", out);
    };
  }, []);

  const eq = shown && work.equations[shown.label];
  if (!shown || !eq) return null;
  return (
    <div
      className="eq-popover"
      role="tooltip"
      style={{ left: shown.x, top: shown.y, transform: `translate(-50%, ${shown.below ? "0" : "-100%"})` }}
    >
      <div dangerouslySetInnerHTML={{ __html: renderMath(eq.tex, true) }} />
      <div
        className="eq-popover-meta"
        dangerouslySetInnerHTML={{ __html: `(${eq.number}) in ${renderInline(work, work.nodes[eq.node]?.title ?? eq.node)}` }}
      />
    </div>
  );
}
