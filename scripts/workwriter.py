"""Writing a Work folder in canonical form (ADR 0002).

The same content always gives the same bytes, so round trips can be compared file by
file: Work → LaTeX → Work, and later loading and saving in the app. Canonical form:

- manifest.yaml: keys in MANIFEST_KEYS order; authors as a block list; keywords, results
  and order as flow lists; the Abstract as a literal block; a blank line before figures.
- references.yaml: keys sorted, fields in a fixed order (bibtex.dump_references).
- nodes/<id>.md: id, type, title, contribution (only when true), then Edges in
  EDGE_TYPES order; a blank line; tiers as `## Gist`, `## Summary`, `## Full` separated by
  one blank line; Primers have their body only. Every file ends with one newline.
"""
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from bibtex import dump_references  # noqa: E402
from workformat import EDGE_TYPES, split_tiers  # noqa: E402
import latexform  # noqa: E402
import latexread  # noqa: E402

MANIFEST_KEYS = ["id", "title", "authors", "year", "venue", "doi", "code", "keywords", "abstract", "results",
                 "conclusion", "order", "figures"]
FLOW_LISTS = {"keywords", "results", "order"}


class WriteError(ValueError):
    pass


def canonical_markdown(text, where):
    """Body Markdown in its one canonical spelling: the form LaTeX → Work gives back
    (for example `|---|` for a left-aligned table column, `| |` for an empty cell)."""
    return latexread.blocks(latexform.blocks(text, where), where)


def scalar(v):
    """A YAML scalar on one line, quoted only when YAML needs it."""
    text = yaml.safe_dump(v, allow_unicode=True, width=10**9, default_flow_style=True)
    return text.removesuffix("\n...\n").rstrip("\n")


def flow(items):
    return "[" + ", ".join(scalar(i) for i in items) + "]"


def literal(key, text, indent=""):
    lines = text.rstrip("\n").split("\n")
    body = "\n".join(f"{indent}  {l}" if l else "" for l in lines)
    return f"{indent}{key}: |\n{body}"


def manifest_text(m):
    unknown = set(m) - set(MANIFEST_KEYS)
    if unknown:
        raise WriteError(f"manifest: unknown keys {sorted(unknown)}")
    out = []
    for key in MANIFEST_KEYS:
        if key not in m or m[key] in (None, "", []):
            continue
        v = m[key]
        if key == "authors":
            out.append("authors:\n" + "\n".join(f"  - {scalar(a)}" for a in v))
        elif key in FLOW_LISTS:
            out.append(f"{key}: {flow(v)}")
        elif key == "abstract":
            out.append(literal("abstract", canonical_markdown(v, "abstract")))
        elif key == "figures":
            figs = ["", "figures:"]
            for fid, f in v.items():
                figs.append(f"  {fid}:\n    file: {scalar(f['file'])}")
                if f.get("caption"):
                    figs.append(f"    caption: {scalar(f['caption'])}")
            out.append("\n".join(figs))
        else:
            out.append(f"{key}: {scalar(v)}")
    return "\n".join(out) + "\n"


def node_text(nid, meta, body):
    """Canonical Node file from its header fields and Markdown body."""
    head = [f"id: {scalar(nid)}", f"type: {meta['type']}", f"title: {scalar(meta.get('title', nid))}"]
    if meta.get("contribution"):
        head.append("contribution: true")
    edges = meta.get("edges") or {}
    unknown = set(edges) - set(EDGE_TYPES) or set(meta) - {"id", "type", "title", "contribution", "edges"}
    if unknown:
        raise WriteError(f"{nid}: unknown header keys or Edge types {sorted(unknown)}")
    lines = [f"  {e}: {flow(edges[e])}" for e in EDGE_TYPES if edges.get(e)]
    if lines:
        head += ["edges:", *lines]
    if meta["type"] == "primer":
        text = canonical_markdown(body.strip("\n"), nid)
    else:
        before = body.split("## Gist", 1)[0] if "## Gist" in body else body
        if before.strip():
            raise WriteError(f"{nid}: text before '## Gist' would be lost")
        tiers = split_tiers(body)
        text = "\n\n".join(
            f"## {t.capitalize()}\n{canonical_markdown(tiers[t], nid)}" for t in ("gist", "summary", "full") if t in tiers
        )
    return "---\n" + "\n".join(head) + "\n---\n\n" + text + "\n"


def write_work(folder, manifest, references, nodes, figures_from=None):
    """Write a Work in canonical form. `nodes` maps id -> (meta, body). Figures are copied
    from `figures_from` (a folder holding the files named in the manifest)."""
    out = Path(folder)
    if out.exists():
        for child in out.iterdir():
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    (out / "nodes").mkdir(parents=True)
    write = lambda p, s: Path(p).write_text(s, encoding="utf-8", newline="\n")
    write(out / "manifest.yaml", manifest_text(manifest))
    write(out / "references.yaml", dump_references(references))
    for nid in sorted(nodes):
        meta, body = nodes[nid]
        write(out / "nodes" / f"{nid}.md", node_text(nid, meta, body))
    if figures_from:
        for f in (manifest.get("figures") or {}).values():
            dest = out / f["file"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(figures_from) / f["file"], dest)
    return out


def canonicalise(work, folder):
    """Write a loaded workformat.Work to `folder` in canonical form."""
    nodes = {nid: (n["meta"], n["body"]) for nid, n in work.nodes.items()}
    return write_work(folder, work.manifest, work.references, nodes, figures_from=work.folder)
