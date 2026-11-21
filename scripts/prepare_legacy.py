"""Prepare an existing LaTeX paper for wrapping in the PaperWeave class (one way).

Usage: python -P scripts/prepare_legacy.py <paper.tex> <out-dir> [--bib <file.bib>] [--id <work-id>]

Writes <out-dir>/main.tex in the PaperWeave class, with the paper's figures, references
and the class files beside it. Constructs with one obvious form in the class are rewritten
mechanically; whatever needs a person's decision is marked \\todo{...}, which the class
shows in red and LaTeX → Work rejects, so no marker can be missed. The person then splits
the text into Node environments, writes Gists, Summaries and Edges, and resolves each
\\todo (scripts/latex_to_work.py reports any that remain).

Rewritten mechanically:
  equation / multline with a \\label      \\begin{equation}\\label{eq-...} (the label first)
  unlabelled display math                 \\[ ... \\]
  align with one label or none            one display with aligned
  align with several labels               one display per row, each keeping its label
  \\ref to an equation, "Eq.~(1)-(3)"     \\eqref, "Equation (1)" / "Equations (1)–(3)"
  figure / figure*                        \\declarefigure in the preamble, \\showfigure in place
  \\cite, \\textit, \\textsl, \\url{http...}  \\citep, \\emph, \\emph, \\autolink
  \\pmb, \\DeclareMathOperator names       \\boldsymbol, \\operatorname{...}
  ~, \\, (outside math), \\noindent, --    space, space, dropped, en dash
  title, authors, abstract, keywords,     the class's metadata commands
  \\journalname
Marked \\todo:
  \\section, \\subsection                  where Nodes probably begin
  \\ref to a figure or section            no numbers in a Work: reword, or \\nodelink
  \\citep[...][...]{...}, \\citeauthor     no citation prefixes or parts in a Work
  \\url without http(s)                   needs a full address
References: the paper's .bib (or --bib) goes through scripts/import_bib.py, which keeps
the cited entries, repairs reference-manager quirks and lists what to check.
Dropped, and listed in the report: comments, \\thanks, \\institute, \\date, \\newpage,
acknowledgements and everything after them.
"""
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from bibtex import write_bib  # noqa: E402
from import_bib import cited_keys, import_bib  # noqa: E402
from latexread import group, optional  # noqa: E402

IMAGE_EXTS = ["", ".pdf", ".png", ".jpg", ".jpeg", ".eps"]


def strip_comments(text):
    """Remove % comments; a line holding only a comment goes entirely."""
    out = []
    for line in text.split("\n"):
        m = re.search(r"(?<!\\)%", line)
        if m:
            if not line[:m.start()].strip():
                continue
            line = line[:m.start()].rstrip()
        out.append(line)
    return "\n".join(out)


def take_command(text, name, report=None):
    """(argument, text without the command) for the first \\name{...}, or (None, text)."""
    m = re.search(r"\\" + name + r"(?![A-Za-z])\s*", text)
    if not m:
        return None, text
    arg, end = group(text, m.end(), name)
    if report is not None:
        report.append(f"dropped \\{name}{{{arg[:50].strip()}...}}")
    return arg, text[:m.start()] + text[end:]


def slug(label, prefix):
    name = re.sub(r"^(eq|fig|sec|tab)[:._-]", "", label)
    name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{prefix}-{name}"


class Preparer:
    def __init__(self, tex_path):
        self.tex_path = Path(tex_path)
        self.report = []
        self.todos = Counter()
        self.equations = {}  # old label -> eq-...
        self.figures = {}  # id -> (file, caption)
        self.figure_labels = {}  # old label -> id
        self.operators = []
        self.bib_report = None

    # ---- math -------------------------------------------------------------
    def fix_math(self, tex):
        tex = re.sub(r"\\pmb(?![A-Za-z])", r"\\boldsymbol", tex)
        for op in self.operators:
            tex = re.sub(r"\\" + op + r"(?![A-Za-z])\s*", r"\\operatorname{" + op + "}", tex)
        return tex

    def eq_label(self, old):
        new = slug(old, "eq")
        if new in self.equations.values() and self.equations.get(old) != new:
            new = f"{new}-{len(self.equations)}"
        self.equations[old] = new
        return new

    def display(self, body, label=None):
        lines = [l.strip() for l in body.strip().split("\n") if l.strip()]
        body = self.fix_math("\n".join(lines))
        if label:
            return f"\\begin{{equation}}\\label{{{self.eq_label(label)}}}\n{body}\n\\end{{equation}}"
        return f"\\[\n{body}\n\\]"

    def display_env(self, m):
        env, body = m.group(1), m.group(2)
        labels = re.findall(r"\\label\{([^}]*)\}", body)
        body = re.sub(r"\s*\\label\{[^}]*\}", "", body)
        if env.rstrip("*") in ("equation", "multline", "gather") and len(labels) <= 1:
            inner = body if env.startswith("equation") or "\\begin{" in body else f"\\begin{{gathered}}\n{body}\n\\end{{gathered}}"
            return self.display(inner, labels[0] if labels else None)
        if len(labels) <= 1:
            return self.display(f"\\begin{{aligned}}\n{body.strip()}\n\\end{{aligned}}", labels[0] if labels else None)
        # Several labels: one display per row, each keeping its own label (KaTeX allows one
        # \tag per display). Alignment points are dropped.
        rows = [r for r in re.split(r"\\\\(?:\[[^\]]*\])?\s*\n", m.group(2)) if r.strip()]
        out = []
        for row in rows:
            label = re.search(r"\\label\{([^}]*)\}", row)
            row = re.sub(r"\s*\\label\{[^}]*\}", "", row).replace("&", "").strip().rstrip("\\").strip()
            out.append(self.display(row, label.group(1) if label else None))
        self.report.append(f"split {env} with labels {', '.join(labels)} into {len(out)} displays")
        return "\n".join(out)

    # ---- text -------------------------------------------------------------
    def todo(self, kind, text):
        self.todos[kind] += 1
        return f"\\todo{{{text}}}"

    def figure_env(self, m):
        body = m.group(2)
        file = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", body)
        cap = re.search(r"\\caption\{", body)
        caption = group(body, cap.end() - 1, "caption")[0] if cap else ""
        label = re.search(r"\\label\{([^}]*)\}", body)
        fid = slug(label.group(1), "fig") if label else f"fig-{len(self.figures) + 1}"
        if label:
            self.figure_labels[label.group(1)] = fid
        self.figures[fid] = (file.group(1) if file else "", caption)
        return f"\n\\showfigure{{{fid}}}\n"

    def references(self, text):
        def eqref(m):
            old = m.group(1)
            return f"\\eqref{{{self.equations[old]}}}" if old in self.equations else m.group(0)

        text = re.sub(r"\\ref\{([^}]*)\}", eqref, text)
        text = re.sub(r"\\eqref\{([^}]*)\}", lambda m: f"\\eqref{{{self.equations.get(m.group(1), m.group(1))}}}", text)
        eq = r"\\eqref\{[^}]*\}"
        dash = r"\s*(?:-|--|–)\s*"
        # "Eqs. (1-3)" and "Eqs. (1)-(3)" lose their brackets, since \eqref brings its own;
        # a bracket that is not part of the reference, as in "(Eqs. 1-3)", stays.
        text = re.sub(r"Eqs?\.?[~ ]*\((" + eq + r")" + dash + r"(" + eq + r")\)", r"Equations \1–\2", text)
        text = re.sub(r"Eqs?\.?[~ ]*\((" + eq + r")\)" + dash + r"\((" + eq + r")\)", r"Equations \1–\2", text)
        text = re.sub(r"Eqs?\.?[~ ]*(" + eq + r")" + dash + r"(" + eq + r")", r"Equations \1–\2", text)
        text = re.sub(r"Eqs\.?[~ ]*(" + eq + r")", r"Equations \1", text)
        text = re.sub(r"Eq\.?[~ ]*\((" + eq + r")\)", r"Equation \1", text)
        text = re.sub(r"Eq\.?[~ ]*(" + eq + r")", r"Equation \1", text)
        ref = r"\\ref\{[^}]*\}"
        run = r"(?:(?:Figures?|Figs?\.|Sections?|Secs?\.|Tables?|Appendix)~?\s*)?" + ref + \
              r"(?:\s*(?:-|--|–|,|and)\s*~?(?:and~?)?\s*" + ref + r")*"
        return re.sub(run, lambda m: self.todo("figure or section reference", m.group(0)), text)

    def citations(self, text):
        out, i = [], 0
        for m in re.finditer(r"\\(cite[a-zA-Z]*)\*?", text):
            if m.start() < i:
                continue
            j = m.end()
            pre, j = optional(text, j, "citation")
            post, j = optional(text, j, "citation")
            keys, j = group(text, j, "citation")
            name = m.group(1)
            out.append(text[i:m.start()])
            if name in ("citep", "citet", "cite") and pre is None:
                out.append(f"\\{'citet' if name == 'citet' else 'citep'}{{{','.join(k.strip() for k in keys.split(','))}}}")
            else:
                out.append(self.todo("citation with prefix or of another kind", text[m.start():j]))
            i = j
        out.append(text[i:])
        return "".join(out)

    def text(self, text):
        """Body or caption text, math protected."""
        spans = []

        def keep(s):
            spans.append(s)
            return f"\x01{len(spans) - 1}\x01"

        text = re.sub(r"\\begin\{(figure\*?)\}(.*?)\\end\{\1\}", lambda m: keep(self.figure_env(m)), text, flags=re.S)
        text = re.sub(r"\\begin\{(equation\*?|align\*?|multline\*?|gather\*?)\}(.*?)\\end\{\1\}",
                      lambda m: keep(self.display_env(m)), text, flags=re.S)
        text = re.sub(r"\\\[(.*?)\\\]", lambda m: keep(self.display(m.group(1))), text, flags=re.S)
        text = re.sub(r"(?<!\\)\$(.+?)(?<!\\)\$", lambda m: keep("$" + self.fix_math(m.group(1)) + "$"), text, flags=re.S)
        return text, spans

    def finish_text(self, text, spans):
        text = self.references(text)
        text = self.citations(text)

        def heading(m):
            level, title, label = m.group(1), m.group(3), m.group(4)
            if level == "subsub":
                return f"\\subsubsection*{{{title}}}"
            return self.todo("section (a Node boundary?)", f"\\{level}section{{{title}}}" + (f"\\label{{{label}}}" if label else ""))

        text = re.sub(r"\\((?:sub)*)section(\*?)\{([^}]*)\}(?:\s*\\label\{([^}]*)\})?", heading, text)
        text = re.sub(r"\\url\{(https?://[^}]*)\}", r"\\autolink{\1}", text)
        text = re.sub(r"\\url\{([^}]*)\}", lambda m: self.todo("address without http(s)", m.group(0)), text)
        text = re.sub(r"\\text(?:it|sl)\{", r"\\emph{", text)
        text = re.sub(r"\\noindent\s*", "", text)
        text = re.sub(r"\\newpage\s*", "", text)
        text = re.sub(r"\\(?:ldots|dots)(?:\{\})?", "…", text)
        text = text.replace("---", "—").replace("--", "–")
        text = re.sub(r"\\,|~", " ", text)
        text = re.sub(r"\\label\{[^}]*\}", "", text)

        # Line-based clean-up: no indentation, single-line list items, at most one blank line.
        lines, in_list = [], False
        for line in text.split("\n"):
            line = line.strip()
            if line == r"\begin{itemize}":
                in_list = True
            elif line == r"\end{itemize}":
                in_list = False
            if in_list and not line:
                continue
            if not line and (not lines or not lines[-1]):
                continue
            lines.append(line)
        text = "\n".join(lines).strip("\n")
        while "\x01" in text:
            text = re.sub(r"\x01(\d+)\x01", lambda m: spans[int(m.group(1))], text)
        return re.sub(r"\n{3,}", "\n\n", text)

    def convert(self, text):
        t, spans = self.text(text)
        return self.finish_text(t, spans)

    # ---- the document -----------------------------------------------------
    def run(self, out_dir, bib=None, work_id=None):
        out = Path(out_dir)
        src = strip_comments(self.tex_path.read_text(encoding="utf-8").replace("\r\n", "\n"))
        pre, rest = src.split("\\begin{document}", 1)
        body = rest.split("\\end{document}", 1)[0]
        self.operators = re.findall(r"\\DeclareMathOperator\*?\{\\([A-Za-z]+)\}", pre)
        venue = re.search(r"\\journalname\{([^}]*)\}", pre)

        title, body = take_command(body, "title")
        title = take_command(title or "", "thanks", self.report)[1].strip()
        authors, body = take_command(body, "author")
        for name in ("institute", "date"):
            body = take_command(body, name, self.report)[1]
        body = body.replace("\\maketitle", "")
        abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S)
        body = body.replace(abstract.group(0), "") if abstract else body
        abstract = abstract.group(1) if abstract else ""
        keywords, abstract = take_command(abstract, "keywords")

        tail = re.search(r"\\begin\{acknowledgements\}|\\bibliographystyle|\\bibliography\{|\{\\footnotesize\s*\\bibliography", body)
        bibname = re.search(r"\\bibliography\{([^}]*)\}", body)
        if tail:
            dropped = body[tail.start():].strip()
            self.report.append(f"dropped {dropped.count(chr(10)) + 1} lines from {dropped[:30]!r} on (acknowledgements, declarations, bibliography)")
            body = body[:tail.start()]

        text = self.convert(body)
        abstract_tex = self.convert(abstract)
        title_tex = self.convert(title)
        author_list = [self.convert(a).strip() for a in re.split(r"\\and", authors or "") if a.strip()]
        keyword_list = [self.convert(k).strip() for k in re.split(r"\\and", keywords or "") if k.strip()]
        fig_lines = []
        for fid, (file, caption) in self.figures.items():
            cap = self.convert(caption).replace("\n", " ")
            fig_lines.append((fid, file, cap))

        # Files: figures, references, the class.
        if out.exists():
            for child in out.iterdir():
                shutil.rmtree(child) if child.is_dir() else child.unlink()
        (out / "figures").mkdir(parents=True, exist_ok=True)
        declared = []
        for fid, file, cap in fig_lines:
            found = next((self.tex_path.parent / (file + e) for e in IMAGE_EXTS
                          if (self.tex_path.parent / (file + e)).is_file()), None)
            if found is None:
                self.report.append(f"figure file not found for {fid}: {file}")
                declared.append(f"\\declarefigure{{{fid}}}{{figures/{file}}}{{{cap}}}")
                continue
            shutil.copy2(found, out / "figures" / found.name)
            declared.append(f"\\declarefigure{{{fid}}}{{figures/{found.name}}}{{{cap}}}")
        for f in ("paperweave.cls", "paperweave.bst"):
            shutil.copy2(HERE.parent / "latex" / f, out / f)

        head = ["\\documentclass{paperweave}", f"\\workid{{{work_id or out.name}}}", f"\\title{{{title_tex}}}"]
        if author_list:
            head.append(f"\\author{{{' \\and '.join(author_list)}}}")
        if venue:
            head.append(f"\\venue{{{venue.group(1)}}}")
        if keyword_list:
            head.append(f"\\keywords{{{', '.join(keyword_list)}}}")
        head += declared
        if abstract_tex:
            head += ["\\begin{abstract}", abstract_tex, "\\end{abstract}"]
        doc = "\n".join(head) + "\n\n\\begin{document}\n\\maketitle\n\n" + text + "\n\n\\bibliography{references}\n\\end{document}\n"
        (out / "main.tex").write_text(doc, encoding="utf-8", newline="\n")

        # References: the paper's .bib, cleaned by import_bib, keeping only what is cited.
        bib_path = Path(bib) if bib else (self.tex_path.parent / f"{bibname.group(1)}.bib" if bibname else None)
        if bib_path and bib_path.is_file():
            refs, fixed, check = import_bib(bib_path.read_text(encoding="utf-8"), cited_keys(out / "main.tex"))
            (out / "references.bib").write_text(write_bib(refs), encoding="utf-8", newline="\n")
            self.bib_report = (len(refs), fixed, check)
        else:
            self.report.append("no .bib file found: add references.bib")
        return out

    def summary(self):
        lines = [f"equations labelled: {len(self.equations)} ({', '.join(f'{a} -> {b}' for a, b in self.equations.items())})",
                 f"figures declared: {len(self.figures)}"]
        lines += self.report
        if self.bib_report:
            n, fixed, check = self.bib_report
            lines.append(f"references: {n} cited entries written to references.bib (scripts/import_bib.py)")
            lines += [f"  fixed: {f}" for f in fixed]
            lines += [f"  to check: {c}" for c in check]
        total = sum(self.todos.values())
        lines.append(f"\\todo markers: {total}" + "".join(f"\n  {n} {k}" for k, n in self.todos.most_common()))
        return "\n".join(lines)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in argv if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    p = Preparer(args[0])
    out = p.run(args[1], bib=opts.get("bib"), work_id=opts.get("id"))
    print(f"wrote {out / 'main.tex'}")
    print(p.summary())


if __name__ == "__main__":
    main(sys.argv[1:])
