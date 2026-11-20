import { useReader } from "../state";
import { figureOwners } from "../work";
import { Markdown, NodeChip } from "./common";

export function FigurePanel() {
  const { work, state, dispatch } = useReader();

  const ids =
    state.figureMode === "all"
      ? Object.keys(work.figures)
      : [...new Set(state.trail.flatMap((t) => work.nodes[t.id]?.figures ?? []))];

  return (
    <div className="figures">
      <div className="seg" role="group" aria-label="Which Figures">
        <button className={state.figureMode === "trail" ? "seg-on" : ""} onClick={() => dispatch({ type: "setFigureMode", mode: "trail" })}>
          In Trail
        </button>
        <button className={state.figureMode === "all" ? "seg-on" : ""} onClick={() => dispatch({ type: "setFigureMode", mode: "all" })}>
          All Figures ({Object.keys(work.figures).length})
        </button>
      </div>

      {ids.length === 0 && <p className="empty">No Figures in the Trail yet.</p>}

      {ids.map((id) => {
        const fig = work.figures[id];
        if (!fig) return null;
        const owners = figureOwners(work, id);
        return (
          <figure key={id} className="figure fig-card">
            <img src={fig.url} alt="" loading="lazy" onClick={() => dispatch({ type: "lightbox", id })} title="Enlarge" />
            <Markdown className="fig-caption" src={fig.caption} />
            <div className="chips">
              <span className="rel-label">Shown in</span>
              {owners.map((n) => (
                <NodeChip key={n.id} node={n} />
              ))}
            </div>
          </figure>
        );
      })}
    </div>
  );
}

export function Lightbox() {
  const { work, state, dispatch } = useReader();
  if (!state.lightbox) return null;
  const fig = work.figures[state.lightbox];
  if (!fig) return null;
  return (
    <div className="lightbox" role="dialog" aria-modal="true" onClick={() => dispatch({ type: "lightbox", id: null })}>
      <figure onClick={(e) => e.stopPropagation()}>
        <img src={fig.url} alt="" />
        <Markdown className="fig-caption" src={fig.caption} />
        <button className="icon-btn lightbox-close" aria-label="Close" onClick={() => dispatch({ type: "lightbox", id: null })}>
          ×
        </button>
      </figure>
    </div>
  );
}
