"""The Markdown body syntax (docs/work-format.md) written as LaTeX in the PaperWeave class.

Each construct has exactly one LaTeX form, so LaTeX → Work can invert it (ADR 0002):

  paragraph line          the same line, special characters escaped
  ### / #### heading      \\subsection*{…} / \\subsubsection*{…}
  - item lines            itemize, one \\item per line
  pipe table              pwtable with a column spec (l, c, r) from the separator row
  ![[fig]] line           \\showfigure{fig}
  [[id]] / [[id|text]]    \\nodelink{id} / \\nodelink[text]{id}
  [@A; @B] / @A           \\citep{A,B} / \\citet{A}
  **b** / *e*             \\textbf{b} / \\emph{e}
  <url> / [text](url)     \\autolink{url} / \\href{url}{text}
  $…$ / $$…$$             $…$ / \\[…\\], contents untouched
  $$…$$ {#eq-x}           \\begin{equation}\\label{eq-x}…\\end{equation}
  [[#eq-x]]               \\eqref{eq-x}
  [^n] and `[^n]: text`   \\footnote{text}, a Note (definitions close their tier)

Anything else in a body is an error, never dropped silently.
"""
import re

KEY = r"[A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9]"
SPECIALS = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "%": r"\%", "&": r"\&", "#": r"\#",
            "_": r"\_", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "$": r"\$"}
URL_SPECIALS = {"%": r"\%", "#": r"\#", "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}"}

NOTE_DEF = re.compile(r"\[\^(\d+)\]: (.+)")
INLINE = re.compile(
    r"(?P<note>\[\^(?P<nnum>\d+)\])"
    r"|(?P<eqref>\[\[#(?P<eqlabel>eq-[a-z0-9-]+)\]\])"
    r"|(?P<link>\[\[(?P<lid>[a-z0-9-]+)(?:\|(?P<ltext>[^\]]*))?\]\])"
    r"|(?P<citep>\[(?P<ckeys>@" + KEY + r"(?:;\s*@" + KEY + r")*)\])"
    r"|(?P<citet>(?:(?<=^)|(?<=[\s(]))@(?P<tkey>" + KEY + r"))"
    r"|(?P<auto><(?P<aurl>https?://[^>\s]+)>)"
    r"|(?P<href>\[(?P<htext>[^\]]+)\]\((?P<hurl>https?://[^)\s]+)\))"
    r"|(?P<bold>\*\*(?P<btext>.+?)\*\*)"
    r"|(?P<em>(?<![*\w])\*(?P<etext>[^*\s](?:[^*]*?[^*\s])?)\*(?![*\w]))"
)
MATH = re.compile(r"\$\$(?P<d>.+?)\$\$(?:[ \t]*\{#(?P<label>eq-[a-z0-9-]+)\})?|\$(?P<i>[^$\n]+?)\$", re.S)


class FormatError(ValueError):
    pass


def escape(text):
    """Plain text as LaTeX. Straight double quotes become `` and '' (opening after a space,
    bracket or the start), which LaTeX → Work turns back into "."""
    out = []
    for i, c in enumerate(text):
        if c == '"':
            out.append("``" if i == 0 or text[i - 1] in " \t([{" else "''")
        else:
            out.append(SPECIALS.get(c, c))
    return "".join(out)


def escape_url(url):
    return "".join(URL_SPECIALS.get(c, c) for c in url)


def _inline(text, notes=None):
    """`notes` maps Note numbers to their text where Notes are allowed (None elsewhere);
    each used Note is set to None so a second use is caught."""
    out, i = [], 0
    for m in INLINE.finditer(text):
        out.append(escape(text[i:m.start()]))
        i = m.end()
        if m["note"]:
            n = m["nnum"]
            if notes is None:
                raise FormatError(f"Notes are allowed only in a Summary, a Full tier or a Primer: {text[:60]!r}")
            if n not in notes:
                raise FormatError(f"Note [^{n}] has no definition '[^{n}]: …'")
            if notes[n] is None:
                raise FormatError(f"Note [^{n}] is used twice")
            out.append(f"\\footnote{{{_inline(notes[n])}}}")
            notes[n] = None
        elif m["eqref"]:
            out.append(f"\\eqref{{{m['eqlabel']}}}")
        elif m["link"]:
            t = m["ltext"]
            out.append(f"\\nodelink{{{m['lid']}}}" if t is None else f"\\nodelink[{_inline(t)}]{{{m['lid']}}}")
        elif m["citep"]:
            keys = [k.strip()[1:] for k in m["ckeys"].split(";")]
            out.append(f"\\citep{{{','.join(keys)}}}")
        elif m["citet"]:
            out.append(f"\\citet{{{m['tkey']}}}")
        elif m["auto"]:
            out.append(f"\\autolink{{{escape_url(m['aurl'])}}}")
        elif m["href"]:
            out.append(f"\\href{{{escape_url(m['hurl'])}}}{{{_inline(m['htext'])}}}")
        elif m["bold"]:
            out.append(f"\\textbf{{{_inline(m['btext'], notes)}}}")
        elif m["em"]:
            out.append(f"\\emph{{{_inline(m['etext'], notes)}}}")
    out.append(escape(text[i:]))
    return "".join(out)


def _protect_math(text):
    """Text with math replaced by placeholders, and the LaTeX for each placeholder."""
    spans = []

    def repl(m):
        if m["label"]:
            spans.append(f"\\begin{{equation}}\\label{{{m['label']}}}{m['d']}\\end{{equation}}")
        elif m["d"] is not None:
            spans.append(f"\\[{m['d']}\\]")
        else:
            spans.append(f"${m['i']}$")
        return f"\x00{len(spans) - 1}\x00"

    return MATH.sub(repl, text), spans


def _restore_math(text, spans):
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)


def inline(text):
    """One line of Markdown inline syntax as LaTeX."""
    if "\n" in text.strip():
        raise FormatError(f"expected a single line: {text[:60]!r}")
    protected, spans = _protect_math(text)
    return _restore_math(_inline(protected), spans)



def _table(lines, where, notes=None):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    if len(rows) < 2 or not all(re.fullmatch(r":?-{3,}:?", c) for c in rows[1]):
        raise FormatError(f"{where}: a table needs a header row and a separator row")
    spec = "".join("c" if c.startswith(":") and c.endswith(":") else "r" if c.endswith(":") else "l" for c in rows[1])
    body = [" & ".join(_inline(c, notes) for c in rows[0]) + r" \\", r"\midrule"]
    for r in rows[2:]:
        if len(r) != len(spec):
            raise FormatError(f"{where}: table row has {len(r)} cells, expected {len(spec)}")
        body.append(" & ".join(_inline(c, notes) for c in r) + r" \\")
    return [f"\\begin{{pwtable}}{{{spec}}}", *body, r"\end{pwtable}"]


def blocks(text, where="body", notes=True):
    """A Detail tier (or Primer, Abstract) of Markdown as LaTeX lines, line for line. With
    `notes`, lines `[^n]: text` define Notes, each written as \\footnote where `[^n]` is used."""
    protected, spans = _protect_math(text.strip("\n"))
    lines = protected.split("\n")
    defs = None
    if notes:
        defs, kept = {}, []
        for line in lines:
            m = NOTE_DEF.fullmatch(line)
            if not m:
                kept.append(line)
            elif m.group(1) in defs:
                raise FormatError(f"{where}: Note [^{m.group(1)}] is defined twice")
            else:
                defs[m.group(1)] = m.group(2)
        while kept and not kept[-1].strip():
            kept.pop()
        lines = kept
    out, i = [], 0
    try:
        while i < len(lines):
            line = lines[i]
            if line.startswith("|"):
                j = i
                while j < len(lines) and lines[j].startswith("|"):
                    j += 1
                out += _table(lines[i:j], where, defs)
                i = j
                continue
            if line.startswith("- "):
                out.append(r"\begin{itemize}")
                while i < len(lines) and lines[i].startswith("- "):
                    out.append(r"\item " + _inline(lines[i][2:], defs))
                    i += 1
                out.append(r"\end{itemize}")
                continue
            m = re.fullmatch(r"!\[\[([a-z0-9-]+)\]\]\s*", line)
            if m:
                out.append(f"\\showfigure{{{m.group(1)}}}")
            elif line.startswith("#### "):
                out.append(f"\\subsubsection*{{{_inline(line[5:], defs)}}}")
            elif line.startswith("### "):
                out.append(f"\\subsection*{{{_inline(line[4:], defs)}}}")
            elif re.match(r"(#{1,2}|#{5,}) |\d+\. |\* |> |    |\t|```", line):
                raise FormatError(f"{where}: unsupported Markdown line {line[:60]!r}")
            else:
                out.append(_inline(line, defs))
            i += 1
    except FormatError as e:
        if str(e).startswith(where):
            raise
        raise FormatError(f"{where}: {e}") from None
    unused = [n for n, d in (defs or {}).items() if d is not None]
    if unused:
        raise FormatError(f"{where}: Note definitions never used: {', '.join(unused)}")
    return _restore_math("\n".join(out), spans)
