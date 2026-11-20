"""Work → LaTeX: write a Work as a document in the PaperWeave class (ADR 0002).

Usage: python -P scripts/work_to_latex.py works/<id> <out-dir> [--pdf] [--tier=gist|summary|full] [--noprimers]

Writes <out-dir>/main.tex, primers/<id>.tex, references.bib and figures/, plus copies of
paperweave.cls and paperweave.bst so the folder compiles on its own. Nodes come in the
Work's Paper order (ADR 0003). With --pdf, runs latexmk to build the Linear version.
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from bibtex import write_bib  # noqa: E402
from latexform import FormatError, blocks, escape, escape_url, inline  # noqa: E402
from workformat import EDGE_TYPES, Work, split_tiers  # noqa: E402

LATEX = HERE.parent / "latex"
MANIFEST_KEYS = {"id", "title", "authors", "year", "venue", "doi", "code", "keywords", "abstract", "results",
                 "conclusion", "order", "figures"}
EDGE_COMMANDS = {"uses": "uses", "relies_on": "reliesOn", "supports": "supports", "explains": "explains",
                 "discusses": "discusses", "situates": "situates", "synthesises": "synthesises"}


def node_tex(work, nid):
    meta, body = work.nodes[nid]["meta"], work.nodes[nid]["body"]
    ntype = meta["type"]
    opt = "[contribution]" if meta.get("contribution") else ""
    lines = [f"\\begin{{{ntype}}}{opt}{{{nid}}}{{{inline(meta.get('title', nid))}}}"]
    edges = meta.get("edges") or {}
    unknown = set(edges) - set(EDGE_TYPES)
    if unknown:
        raise FormatError(f"{nid}: unknown Edge types {sorted(unknown)}")
    for etype in EDGE_TYPES:
        if edges.get(etype):
            lines.append(f"\\{EDGE_COMMANDS[etype]}{{{', '.join(edges[etype])}}}")
    where = nid
    if ntype == "primer":
        lines.append(blocks(body, where))
    else:
        tiers = split_tiers(body)
        if "gist" not in tiers:
            raise FormatError(f"{nid}: no Gist")
        lines.append(f"\\gist{{{inline(tiers['gist'])}}}")
        for t in ("summary", "full"):
            if t in tiers:
                lines += [f"\\begin{{{t}}}", blocks(tiers[t], f"{nid} ({t})"), f"\\end{{{t}}}"]
    lines.append(f"\\end{{{ntype}}}")
    return "\n".join(lines) + "\n"


def main_tex(work, tier="full", noprimers=False):
    m = work.manifest
    unknown = set(m) - MANIFEST_KEYS
    if unknown:
        raise FormatError(f"manifest: no LaTeX form for {sorted(unknown)}")
    opts = [f"tier={tier}"] + (["noprimers"] if noprimers else [])
    out = [f"\\documentclass[{','.join(opts)}]{{paperweave}}", f"\\workid{{{m['id']}}}", f"\\title{{{inline(m['title'])}}}"]
    if m.get("authors"):
        out.append("\\author{" + " \\and ".join(escape(a) for a in m["authors"]) + "}")
    if m.get("year"):
        out.append(f"\\workyear{{{m['year']}}}")
    if m.get("venue"):
        out.append(f"\\venue{{{inline(m['venue'])}}}")
    for key in ("doi", "code"):
        if m.get(key):
            out.append(f"\\{key}{{{escape_url(m[key])}}}")
    if m.get("keywords"):
        out.append("\\keywords{" + ", ".join(escape(k) for k in m["keywords"]) + "}")
    if m.get("results"):
        out.append("\\results{" + ", ".join(m["results"]) + "}")
    for fid, fig in (m.get("figures") or {}).items():
        out.append(f"\\declarefigure{{{fid}}}{{{fig['file']}}}{{{inline(fig.get('caption', ''))}}}")
    if m.get("abstract"):
        out += ["\\begin{abstract}", blocks(m["abstract"], "abstract"), "\\end{abstract}"]
    out += ["", "\\begin{document}", "\\maketitle", ""]
    for nid in work.paper_order():
        out.append(f"\\includeprimer{{{nid}}}\n" if work.type_of(nid) == "primer" else node_tex(work, nid))
    out += ["\\bibliography{references}", "\\end{document}"]
    return "\n".join(out) + "\n"


def export(folder, out_dir, tier="full", noprimers=False):
    work = Work(folder)
    out = Path(out_dir)
    if out.exists():  # empty it, keeping the folder itself (it may be open elsewhere)
        for child in out.iterdir():
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    (out / "primers").mkdir(parents=True)
    write = lambda p, s: Path(p).write_text(s, encoding="utf-8", newline="\n")
    write(out / "main.tex", main_tex(work, tier, noprimers))
    for nid in work.nodes:
        if work.type_of(nid) == "primer":
            write(out / "primers" / f"{nid}.tex", node_tex(work, nid))
    write(out / "references.bib", write_bib(work.references))
    if (work.folder / "figures").exists():
        shutil.copytree(work.folder / "figures", out / "figures")
    for f in ("paperweave.cls", "paperweave.bst"):
        shutil.copy(LATEX / f, out / f)
    return out


def build_pdf(out):
    run = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
        cwd=out, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if run.returncode:
        log = Path(out, "main.log")
        tail = log.read_text(encoding="utf-8", errors="replace")[-3000:] if log.exists() else run.stdout[-3000:]
        raise SystemExit(f"latexmk failed in {out}:\n{tail}")
    return Path(out, "main.pdf")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    tier = next((f.split("=", 1)[1] for f in flags if f.startswith("--tier=")), "full")
    try:
        out = export(args[0], args[1], tier, "--noprimers" in flags)
    except FormatError as e:
        raise SystemExit(f"error: {e}")
    print(f"wrote {out}")
    if "--pdf" in flags:
        print(f"built {build_pdf(out)}")
