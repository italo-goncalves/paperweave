"""LaTeX → Work: read a document in the PaperWeave class back into the Work format (ADR 0002).

Usage: python -P scripts/latex_to_work.py <latex-dir> <work-dir>

Reads <latex-dir>/main.tex, primers/<id>.tex, references.bib and figures/, and writes the
Work in canonical form. Only what the class defines is accepted; anything else is an
error with its file and line, never dropped. The written order of Nodes is kept in the
manifest's `order` when it differs from the computed Paper order (ADR 0003).
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import latexread  # noqa: E402
from bibtex import read_bib  # noqa: E402
from latexform import FormatError  # noqa: E402
from workformat import EDGE_TYPES, TYPES, paper_order  # noqa: E402
from workwriter import write_work  # noqa: E402

EDGE_KEYS = {"uses": "uses", "reliesOn": "relies_on", "supports": "supports", "explains": "explains",
             "discusses": "discusses", "situates": "situates", "synthesises": "synthesises"}
NODE_ENVS = [t for t in TYPES if t != "primer"]


class Source:
    """A .tex file read with positions, for error messages with line numbers."""

    def __init__(self, path):
        self.path = Path(path)
        self.text = self.path.read_text(encoding="utf-8").replace("\r\n", "\n")
        self.i = 0

    def where(self, i=None):
        line = self.text.count("\n", 0, self.i if i is None else i) + 1
        return f"{self.path.name}:{line}"

    def skip_space(self):
        while True:
            m = re.compile(r"\s+|%[^\n]*").match(self.text, self.i)
            if not m or not m.group(0):
                return
            self.i = m.end()

    def at_end(self):
        self.skip_space()
        return self.i >= len(self.text)

    def command(self):
        self.skip_space()
        m = re.compile(r"\\([A-Za-z]+\*?)").match(self.text, self.i)
        if not m:
            raise FormatError(f"{self.where()}: expected a command, found {self.text[self.i:self.i + 40]!r}")
        self.i = m.end()
        return m.group(1)

    def arg(self):
        value, self.i = latexread.group(self.text, self.i, self.where())
        return value

    def opt(self):
        value, self.i = latexread.optional(self.text, self.i, self.where())
        return value

    def until(self, end):
        j = self.text.find(end, self.i)
        if j < 0:
            raise FormatError(f"{self.where()}: missing {end!r}")
        value, self.i = self.text[self.i:j], j + len(end)
        return value


def split_list(s):
    return [x.strip() for x in s.split(",") if x.strip()]


def read_node(src, env, where):
    """(id, meta, body) of a Node environment whose \\begin{env} was just read."""
    options = src.opt()
    nid = src.arg()
    title = latexread.inline(src.arg(), f"{where} title")
    if options not in (None, "contribution"):
        raise FormatError(f"{where}: unknown option [{options}]")
    content = src.until(f"\\end{{{env}}}")
    meta = {"id": nid, "type": env, "title": title}
    if options == "contribution":
        meta["contribution"] = True
    edges = {}
    rest = content.lstrip("\n")
    while True:
        m = re.match(r"\\(" + "|".join(EDGE_KEYS) + r")\{([^}]*)\}\n?", rest)
        if not m:
            break
        edges.setdefault(EDGE_KEYS[m.group(1)], []).extend(split_list(m.group(2)))
        rest = rest[m.end():]
    if edges:
        meta["edges"] = {k: edges[k] for k in EDGE_TYPES if k in edges}

    if env == "primer":
        return nid, meta, "\n" + latexread.blocks(rest, nid) + "\n"

    m = re.match(r"\\gist\{", rest)
    if not m:
        raise FormatError(f"{where}: Node {nid} needs \\gist{{…}} after its Edges")
    gist, j = latexread.group(rest, m.end() - 1, nid)
    tiers = {"gist": latexread.inline(gist, f"{nid} gist")}
    rest = rest[j:]
    for tier in ("summary", "full"):
        m = re.match(r"\s*\\begin\{" + tier + r"\}\n(.*?)\n\\end\{" + tier + r"\}", rest, re.S)
        if m:
            tiers[tier] = latexread.blocks(m.group(1), f"{nid} ({tier})")
            rest = rest[m.end():]
    if rest.strip():
        raise FormatError(f"{where}: unexpected content in Node {nid}: {rest.strip()[:60]!r}")
    body = "\n" + "\n\n".join(f"## {t.capitalize()}\n{tiers[t]}" for t in ("gist", "summary", "full") if t in tiers) + "\n"
    return nid, meta, body


def read_document(folder):
    folder = Path(folder)
    src = Source(folder / "main.tex")
    manifest, figures = {}, {}

    if src.command() != "documentclass":
        raise FormatError(f"{src.where()}: the document must start with \\documentclass{{paperweave}}")
    src.opt()
    if src.arg() != "paperweave":
        raise FormatError(f"{src.where()}: the class must be paperweave")

    # Preamble: the Work's metadata.
    while True:
        where = src.where()
        cmd = src.command()
        if cmd == "begin":
            env = src.arg()
            if env == "document":
                break
            if env != "abstract":
                raise FormatError(f"{where}: only the abstract environment is allowed in the preamble")
            manifest["abstract"] = latexread.blocks(src.until("\\end{abstract}"), "abstract") + "\n"
        elif cmd == "workid":
            manifest["id"] = src.arg()
        elif cmd == "title":
            manifest["title"] = latexread.inline(src.arg(), "title")
        elif cmd == "author":
            manifest["authors"] = [latexread.inline(a.strip(), "author") for a in src.arg().split("\\and")]
        elif cmd == "workyear":
            y = src.arg()
            manifest["year"] = int(y) if y.isdigit() else y
        elif cmd == "venue":
            manifest["venue"] = latexread.inline(src.arg(), "venue")
        elif cmd in ("doi", "code"):
            manifest[cmd] = latexread.unescape_url(src.arg())
        elif cmd == "keywords":
            manifest["keywords"] = [latexread.inline(k.strip(), "keywords") for k in src.arg().split(", ")]
        elif cmd == "results":
            manifest["results"] = split_list(src.arg())
        elif cmd == "declarefigure":
            fid, file, caption = src.arg(), src.arg(), src.arg()
            figures[fid] = {"file": file, **({"caption": latexread.inline(caption, f"caption of {fid}")} if caption else {})}
        else:
            raise FormatError(f"{where}: \\{cmd} is not part of the PaperWeave class")

    # Document: Nodes in written order.
    nodes, written, bib = {}, [], None
    while True:
        where = src.where()
        cmd = src.command()
        if cmd == "maketitle":
            continue
        if cmd == "end":
            if src.arg() != "document":
                raise FormatError(f"{where}: unexpected \\end")
            break
        if cmd == "begin":
            env = src.arg()
            if env not in NODE_ENVS:
                raise FormatError(f"{where}: \\begin{{{env}}} is not a Node type")
            nid, meta, body = read_node(src, env, where)
        elif cmd == "includeprimer":
            pid = src.arg()
            psrc = Source(folder / "primers" / f"{pid}.tex")
            if psrc.command() != "begin" or psrc.arg() != "primer":
                raise FormatError(f"{psrc.where()}: a Primer file holds one primer environment")
            nid, meta, body = read_node(psrc, "primer", psrc.where())
            if nid != pid or not psrc.at_end():
                raise FormatError(f"{psrc.where()}: expected only Primer {pid} in this file")
        elif cmd == "bibliography":
            bib = src.arg()
            continue
        else:
            raise FormatError(f"{where}: \\{cmd} is not part of the PaperWeave class")
        if nid in nodes:
            raise FormatError(f"{where}: Node {nid} appears twice")
        nodes[nid] = (meta, body)
        written.append(nid)
    if not src.at_end():
        raise FormatError(f"{src.where()}: content after \\end{{document}}")

    conclusions = [n for n in written if nodes[n][0]["type"] == "conclusion"]
    if len(conclusions) == 1:
        manifest["conclusion"] = conclusions[0]
    types = {n: nodes[n][0]["type"] for n in written}
    edges = [(t, n, to) for n in written for t, tos in (nodes[n][0].get("edges") or {}).items() for to in tos]
    if written != paper_order(types, edges, manifest.get("results") or []):
        manifest["order"] = written
    if figures:
        manifest["figures"] = figures
    references = read_bib((folder / f"{bib}.bib").read_text(encoding="utf-8")) if bib else {}
    return manifest, references, nodes


def import_latex(latex_dir, work_dir):
    manifest, references, nodes = read_document(latex_dir)
    return write_work(work_dir, manifest, references, nodes, figures_from=latex_dir)


if __name__ == "__main__":
    try:
        out = import_latex(sys.argv[1], sys.argv[2])
    except FormatError as e:
        raise SystemExit(f"error: {e}")
    print(f"wrote {out}")
