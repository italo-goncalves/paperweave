import { useMemo } from "react";
import { useReader } from "../state";
import { renderInline, renderMarkdown } from "../render";
import { TYPE_LABELS, type WorkNode } from "../work";
import { useContentClicks } from "./useContentClicks";

export function Markdown({ src, inline, className }: { src: string; inline?: boolean; className?: string }) {
  const { work } = useReader();
  const html = useMemo(() => (inline ? renderInline(work, src) : renderMarkdown(work, src)), [work, src, inline]);
  const onClick = useContentClicks();
  const Tag = inline ? "span" : "div";
  return <Tag className={className} onClick={onClick} dangerouslySetInnerHTML={{ __html: html }} />;
}

export function TypeBadge({ node }: { node: WorkNode }) {
  return (
    <span className={`badge badge-${node.type}`}>
      {TYPE_LABELS[node.type]}
      {node.contribution && <span className="star" title="Contribution of this Work"> ★</span>}
    </span>
  );
}

export function NodeChip({ node, fresh }: { node: WorkNode; fresh?: boolean }) {
  const { state, dispatch } = useReader();
  const inTrail = state.trail.some((t) => t.id === node.id);
  return (
    <button
      className={`chip chip-${node.type}${inTrail ? " chip-in-trail" : ""}`}
      title={inTrail ? "Already in your Trail" : `Open ${node.type}`}
      onClick={(e) => {
        // Keep the enclosing card from re-focusing itself after this opens.
        e.stopPropagation();
        dispatch({ type: "open", id: node.id, fresh });
      }}
    >
      <Markdown src={node.title} inline />
    </button>
  );
}
