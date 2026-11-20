import { useEffect, useRef } from "react";
import { useReader, type TrailItem } from "../state";
import { EDGE_LABELS, EDGE_TYPES, TIERS, effectiveTier, incoming, outgoing, type Tier } from "../work";
import { Markdown, NodeChip, TypeBadge } from "./common";

const TIER_LABELS: Record<Tier, string> = { gist: "Gist", summary: "Summary", full: "Full" };

export function ReadingPanel() {
  const { state, dispatch } = useReader();
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!state.activeId || !scroller.current) return;
    const el = scroller.current.querySelector(`[data-card="${state.activeId}"]`);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
    // Only scroll when a Node is opened, not on every focus change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.scrollTick]);

  if (state.trail.length === 0) {
    return (
      <div className="empty">
        <p>Your Trail is empty.</p>
        <p>Pick a Result from the Results list to start. Every Node you open joins the Trail at its place in the Reading order.</p>
      </div>
    );
  }

  return (
    <div className="reading" ref={scroller}>
      <div className="trail-bar">
        <span>{state.trail.length} Node{state.trail.length === 1 ? "" : "s"} in Trail</span>
        <button className="link-btn" onClick={() => dispatch({ type: "clearTrail" })}>
          Clear
        </button>
      </div>
      {state.trail.map((item, i) => (
        <TrailCard key={item.id} item={item} index={i} />
      ))}
    </div>
  );
}

function TrailCard({ item, index }: { item: TrailItem; index: number }) {
  const { work, state, dispatch } = useReader();
  const node = work.nodes[item.id];
  if (!node) return null;

  const isPrimer = node.type === "primer";
  const wanted = item.tier ?? state.globalTier;
  const shown = isPrimer ? "full" : effectiveTier(node, wanted);
  const active = state.activeId === node.id;
  const out = outgoing(work, node.id);
  const inc = incoming(work, node.id);

  return (
    <article
      className={`card card-${node.type}${active ? " card-active" : ""}`}
      data-card={node.id}
      onClick={() => dispatch({ type: "focus", id: node.id })}
    >
      <header className="card-head">
        <button
          className="icon-btn"
          aria-label={item.collapsed ? "Expand" : "Collapse"}
          title={item.collapsed ? "Expand" : "Collapse"}
          onClick={(e) => {
            e.stopPropagation();
            dispatch({ type: "toggleCollapse", id: node.id });
          }}
        >
          {item.collapsed ? "▸" : "▾"}
        </button>
        <span className="card-index">{index + 1}</span>
        <TypeBadge node={node} />
        <h2 className="card-title">
          <Markdown src={node.title} inline />
        </h2>
        {!isPrimer && (
          <div className="tiers" role="group" aria-label="Detail tier">
            {TIERS.map((t) => {
              const exists = node.tiers[t] !== undefined;
              return (
                <button
                  key={t}
                  className={`tier-btn${shown === t ? " tier-on" : ""}${item.tier === t ? " tier-pinned" : ""}`}
                  disabled={!exists}
                  title={exists ? (item.tier === t ? `${TIER_LABELS[t]} (set for this Node)` : TIER_LABELS[t]) : `No ${TIER_LABELS[t]} tier`}
                  onClick={(e) => {
                    e.stopPropagation();
                    dispatch({ type: "setTier", id: node.id, tier: item.tier === t ? null : t });
                  }}
                >
                  {TIER_LABELS[t][0]}
                </button>
              );
            })}
          </div>
        )}
        <button
          className="icon-btn"
          aria-label="Remove from Trail"
          title="Remove from Trail"
          onClick={(e) => {
            e.stopPropagation();
            dispatch({ type: "close", id: node.id });
          }}
        >
          ×
        </button>
      </header>

      {item.collapsed ? (
        node.tiers.gist && <Markdown className="card-body collapsed-gist" src={node.tiers.gist} />
      ) : (
        <>
          {shown !== wanted && !isPrimer && (
            <p className="tier-note">No {TIER_LABELS[wanted]} tier for this Node; showing {TIER_LABELS[shown]}.</p>
          )}
          <Markdown className="card-body prose" src={node.tiers[shown] ?? ""} />
          {(out.length > 0 || inc.length > 0) && (
            <footer className="relations">
              {EDGE_TYPES.map((et) => {
                const targets = out.filter((e) => e.type === et).map((e) => work.nodes[e.to]);
                return targets.length ? (
                  <div className="rel" key={`o-${et}`}>
                    <span className="rel-label">{EDGE_LABELS[et].out}</span>
                    {targets.map((n) => (
                      <NodeChip key={n.id} node={n} />
                    ))}
                  </div>
                ) : null;
              })}
              {EDGE_TYPES.map((et) => {
                const sources = inc.filter((e) => e.type === et).map((e) => work.nodes[e.from]);
                return sources.length ? (
                  <div className="rel rel-in" key={`i-${et}`}>
                    <span className="rel-label">{EDGE_LABELS[et].in}</span>
                    {sources.map((n) => (
                      <NodeChip key={n.id} node={n} />
                    ))}
                  </div>
                ) : null;
              })}
            </footer>
          )}
        </>
      )}
    </article>
  );
}
