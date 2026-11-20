"""Validate a Work folder against docs/work-format.md.

Usage: python -P scripts/validate_work.py works/<work-id>
Exit code 1 if any error is found; notes are informational.
"""
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from workformat import paper_group  # noqa: E402

TYPES = {"result", "method", "concept", "primer", "context", "discussion", "conclusion"}
ANY = TYPES
EDGE_RULES = {
    "uses": ({"result", "method"}, {"method"}),
    "relies_on": ({"result", "method", "concept"}, {"concept"}),
    "supports": ({"result"}, {"result"}),
    "explains": ({"primer"}, {"concept"}),
    "discusses": ({"discussion"}, ANY),
    "situates": ({"context"}, ANY),
    "synthesises": ({"conclusion"}, {"result"}),
}
TIERS = ["Gist", "Summary", "Full"]

INLINE = re.compile(r"(?<!!)\[\[([a-z0-9-]+)(?:\|[^\]]*)?\]\]")
FIGURE = re.compile(r"!\[\[([a-z0-9-]+)\]\]")
CITE = re.compile(r"@([A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9])")


def load_node(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("missing YAML header")
    return yaml.safe_load(m.group(1)), m.group(2)


def main(work_dir):
    work = Path(work_dir)
    errors, notes = [], []
    manifest = yaml.safe_load((work / "manifest.yaml").read_text(encoding="utf-8"))
    refs = yaml.safe_load((work / "references.yaml").read_text(encoding="utf-8")) or {}
    figures = manifest.get("figures", {})

    nodes = {}
    for path in sorted((work / "nodes").glob("*.md")):
        try:
            meta, body = load_node(path)
        except ValueError as e:
            errors.append(f"{path.name}: {e}")
            continue
        if meta.get("id") != path.stem:
            errors.append(f"{path.name}: id '{meta.get('id')}' does not match filename")
        if meta.get("type") not in TYPES:
            errors.append(f"{path.name}: unknown type '{meta.get('type')}'")
        nodes[path.stem] = (meta, body)

    used_figures, used_refs, incoming = set(), set(), {n: 0 for n in nodes}

    for nid, (meta, body) in nodes.items():
        ntype = meta.get("type")
        headings = re.findall(r"^## (.+)$", body, re.M)
        if ntype == "primer":
            if headings:
                errors.append(f"{nid}: primers have no tier headings, found {headings}")
        else:
            if headings[:1] != ["Gist"]:
                errors.append(f"{nid}: first tier must be '## Gist'")
            bad = [h for h in headings if h not in TIERS]
            if bad:
                errors.append(f"{nid}: unknown level-2 headings {bad}")
            if [h for h in TIERS if h in headings] != headings:
                errors.append(f"{nid}: tiers out of order or repeated: {headings}")

        edge_targets = set()
        for key, targets in (meta.get("edges") or {}).items():
            if key not in EDGE_RULES:
                errors.append(f"{nid}: unknown edge type '{key}'")
                continue
            sources, dests = EDGE_RULES[key]
            if ntype not in sources:
                errors.append(f"{nid}: a {ntype} cannot declare '{key}'")
            for t in targets:
                if t not in nodes:
                    errors.append(f"{nid}: {key} → '{t}' does not exist")
                    continue
                if nodes[t][0].get("type") not in dests:
                    errors.append(f"{nid}: {key} → {t} ({nodes[t][0].get('type')}) not allowed")
                if t == nid:
                    errors.append(f"{nid}: edge to itself")
                edge_targets.add(t)
                incoming[t] += 1

        for link in sorted(set(INLINE.findall(body))):
            if link not in nodes:
                errors.append(f"{nid}: inline link to missing node '{link}'")
            elif link != nid and link not in edge_targets:
                reverse = any(nid in ts for ts in (nodes[link][0].get("edges") or {}).values())
                if not reverse:
                    notes.append(f"{nid}: inline link to {link} has no Edge in either direction")
        for fig in FIGURE.findall(body):
            if fig not in figures:
                errors.append(f"{nid}: figure '{fig}' not in manifest")
            used_figures.add(fig)
        for key in CITE.findall(body):
            if key not in refs:
                errors.append(f"{nid}: citation '{key}' not in references.yaml")
            used_refs.add(key)

    for fid, fig in figures.items():
        if not (work / fig["file"]).exists():
            errors.append(f"manifest: figure file missing for {fid}: {fig['file']}")
        if fid not in used_figures:
            notes.append(f"manifest: figure {fid} is not shown by any node")
        for key in CITE.findall(fig.get("caption", "")):
            if key not in refs:
                errors.append(f"manifest: citation '{key}' in caption of {fid} not in references.yaml")
            used_refs.add(key)

    for r in manifest.get("results", []):
        if nodes.get(r, ({},))[0].get("type") != "result":
            errors.append(f"manifest: results entry '{r}' is not a result node")
    listed = set(manifest.get("results", []))
    for nid, (meta, _) in nodes.items():
        if meta.get("type") == "result" and nid not in listed:
            errors.append(f"manifest: result {nid} missing from results list")
    conc = manifest.get("conclusion")
    if nodes.get(conc, ({},))[0].get("type") != "conclusion":
        errors.append(f"manifest: conclusion '{conc}' is not a conclusion node")
    if sum(1 for m, _ in nodes.values() if m.get("type") == "conclusion") != 1:
        errors.append("work must have exactly one conclusion node")

    order = manifest.get("order")
    if order is not None:
        # ADR 0003: every Node once, grouped by type in Paper order.
        if not isinstance(order, list):
            errors.append("manifest: order must be a list of Node ids")
            order = []
        for nid in sorted(set(order) - set(nodes)):
            errors.append(f"manifest: order lists '{nid}', which does not exist")
        for nid in sorted(set(nodes) - set(order)):
            errors.append(f"manifest: order is missing {nid}")
        for nid in sorted({n for n in order if order.count(n) > 1}):
            errors.append(f"manifest: order lists {nid} more than once")
        groups = [paper_group(nodes[n][0].get("type")) for n in order if n in nodes and nodes[n][0].get("type") in TYPES]
        known = [n for n in order if n in nodes and nodes[n][0].get("type") in TYPES]
        for i in range(1, len(groups)):
            if groups[i] < groups[i - 1]:
                errors.append(f"manifest: order puts {known[i]} ({nodes[known[i]][0].get('type')}) after {known[i - 1]} ({nodes[known[i - 1]][0].get('type')})")

    for nid, (meta, _) in nodes.items():
        if not meta.get("edges") and incoming[nid] == 0:
            errors.append(f"{nid}: isolated node (no edges in or out)")
    ref_types = {"article", "inproceedings", "incollection", "book", "thesis", "report", "misc"}
    for key, r in refs.items():
        # ADR 0004: structured fields, formatted by PaperWeave's style.
        if not isinstance(r, dict) or "text" in r or "label" in r:
            errors.append(f"references: {key} must hold fields, not a formatted label and text")
            continue
        if r.get("type") not in ref_types:
            errors.append(f"references: {key} has unknown type '{r.get('type')}'")
        if not isinstance(r.get("author"), list) or not r["author"]:
            errors.append(f"references: {key} needs an author list")
        for f in ("year", "title"):
            if not r.get(f):
                errors.append(f"references: {key} has no {f}")
        if str(r.get("doi", "")).startswith("http"):
            errors.append(f"references: {key} doi must be bare (10.xxxx/...), not a URL")
    for key in sorted(set(refs) - used_refs):
        notes.append(f"references: {key} is never cited")

    counts = {}
    for meta, _ in nodes.values():
        counts[meta.get("type")] = counts.get(meta.get("type"), 0) + 1
    print(f"{len(nodes)} nodes: " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    print(f"{sum(incoming.values())} edges, {len(figures)} figures, {len(used_refs)} references cited")
    for n in notes:
        print("note:", n)
    for e in errors:
        print("ERROR:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
