import { useReader } from "../state";
import { NODE_TYPES, TYPE_LABELS } from "../work";
import { Markdown, NodeChip, TypeBadge } from "./common";

export function ResultsList() {
  const { work, state, dispatch } = useReader();
  const entries = [...work.results, work.conclusion].map((id) => work.nodes[id]).filter(Boolean);

  return (
    <div className="results">
      <header className="work-head">
        <h1>{work.title}</h1>
        <p className="byline">
          {work.authors.join(", ")}
          {work.venue && ` · ${work.venue}`}
          {work.year && ` · ${work.year}`}
        </p>
      </header>

      <details className="abstract" open>
        <summary>Abstract</summary>
        <Markdown className="prose" src={work.abstract} />
      </details>

      <ol className="entry-list">
        {entries.map((n) => (
          <li key={n.id}>
            <button
              className={`entry entry-${n.type}${state.trail[0]?.id === n.id ? " entry-current" : ""}`}
              onClick={() => dispatch({ type: "open", id: n.id, fresh: true })}
            >
              <span className="entry-top">
                <TypeBadge node={n} />
                <strong>
                  <Markdown src={n.title} inline />
                </strong>
              </span>
              {n.tiers.gist && <Markdown className="entry-gist" src={n.tiers.gist} inline />}
            </button>
          </li>
        ))}
      </ol>

      <details className="browse">
        <summary>Browse every Node</summary>
        {NODE_TYPES.map((t) => {
          const ofType = Object.values(work.nodes)
            .filter((n) => n.type === t)
            .sort((a, b) => a.title.localeCompare(b.title));
          return ofType.length ? (
            <div key={t} className="browse-group">
              <h3>{TYPE_LABELS[t]}</h3>
              <div className="chips">
                {ofType.map((n) => (
                  <NodeChip key={n.id} node={n} />
                ))}
              </div>
            </div>
          ) : null;
        })}
      </details>
      {work.code && (
        <p className="code-link">
          Code: <a href={work.code} target="_blank" rel="noreferrer">{work.code}</a>
        </p>
      )}
    </div>
  );
}
