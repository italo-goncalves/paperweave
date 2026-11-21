import { useEffect, useRef, useState } from "react";
import { useContentClicks } from "./useContentClicks";

interface Shown {
  html: string;
  x: number;
  y: number;
  below: boolean;
  pinned: boolean;
  marker: HTMLElement;
}

const MARKER = "sup.note-ref[data-note]";

function place(marker: HTMLElement, pinned: boolean): Shown {
  const r = marker.getBoundingClientRect();
  const below = r.top < window.innerHeight / 2;
  const html = marker.querySelector(".note-body")?.innerHTML ?? "";
  return { html, x: r.left + r.width / 2, y: below ? r.bottom + 6 : r.top - 6, below, pinned, marker };
}

/**
 * Shows a Note while the pointer is over its marker; clicking (or tapping, or Enter on a
 * focused marker) pins it open until a click elsewhere. Links inside a pinned Note work.
 */
export function NotePopover() {
  const [shown, setShown] = useState<Shown | null>(null);
  const box = useRef<HTMLDivElement>(null);
  const contentClicks = useContentClicks();

  useEffect(() => {
    const over = (e: MouseEvent) => {
      const marker = (e.target as HTMLElement).closest?.<HTMLElement>(MARKER);
      if (marker) setShown((s) => (s?.pinned ? s : place(marker, false)));
    };
    const out = (e: MouseEvent) => {
      if ((e.target as HTMLElement).closest?.(MARKER)) setShown((s) => (s?.pinned ? s : null));
    };
    const toggle = (marker: HTMLElement) =>
      setShown((s) => (s?.pinned && s.marker === marker ? null : place(marker, true)));
    const click = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const marker = target.closest?.<HTMLElement>(MARKER);
      if (marker) {
        e.preventDefault();
        toggle(marker);
      } else if (!box.current?.contains(target)) {
        setShown(null);
      }
    };
    const key = (e: KeyboardEvent) => {
      const marker = (e.target as HTMLElement).closest?.<HTMLElement>(MARKER);
      if (marker && (e.key === "Enter" || e.key === " ")) {
        e.preventDefault();
        toggle(marker);
      } else if (e.key === "Escape") {
        setShown(null);
      }
    };
    // Scrolling moves the marker away from a fixed popover; close it.
    const scroll = (e: Event) => {
      if (!box.current?.contains(e.target as Node)) setShown(null);
    };
    document.addEventListener("mouseover", over);
    document.addEventListener("mouseout", out);
    document.addEventListener("click", click, true);
    document.addEventListener("keydown", key);
    document.addEventListener("scroll", scroll, true);
    return () => {
      document.removeEventListener("mouseover", over);
      document.removeEventListener("mouseout", out);
      document.removeEventListener("click", click, true);
      document.removeEventListener("keydown", key);
      document.removeEventListener("scroll", scroll, true);
    };
  }, []);

  if (!shown) return null;
  return (
    <div
      ref={box}
      className={`note-popover${shown.pinned ? " note-pinned" : ""}`}
      role={shown.pinned ? "dialog" : "tooltip"}
      style={{ left: shown.x, top: shown.y, transform: `translate(-50%, ${shown.below ? "0" : "-100%"})` }}
      onClick={(e) => {
        contentClicks(e);
        if ((e.target as HTMLElement).closest("a")) setShown(null);
      }}
      dangerouslySetInnerHTML={{ __html: shown.html }}
    />
  );
}
