"""LaTeX → Markdown: the exact inverse of latexform.py, for Node bodies in the PaperWeave class.

Only the constructs latexform.py writes are accepted; anything else raises FormatError
naming where it was found, so nothing is dropped silently (ADR 0002).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from latexform import FormatError, _restore_math  # noqa: E402

UNESCAPE = {"{": "{", "}": "}", "%": "%", "&": "&", "#": "#", "_": "_", "$": "$"}
WORD_ESCAPES = {"textbackslash": "\\", "textasciitilde": "~", "textasciicircum": "^"}


def group(s, i, where):
    """(contents, index after) of the {…} group starting at s[i]."""
    if i >= len(s) or s[i] != "{":
        raise FormatError(f"{where}: expected '{{' near {s[max(0, i - 30):i + 30]!r}")
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        depth += {"{": 1, "}": -1}.get(c, 0)
        if depth == 0:
            return s[i + 1:j], j + 1
        j += 1
    raise FormatError(f"{where}: unbalanced braces near {s[i:i + 40]!r}")


def optional(s, i, where):
    """(contents or None, index after) of an optional […] argument at s[i]."""
    if i >= len(s) or s[i] != "[":
        return None, i
    depth, j = 0, i + 1
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "]" and depth == 0:
            return s[i + 1:j], j + 1
        j += 1
    raise FormatError(f"{where}: unclosed '[' near {s[i:i + 40]!r}")


def unescape_url(s):
    for a, b in ((r"\textbackslash{}", "\\"), (r"\%", "%"), (r"\#", "#"), (r"\{", "{"), (r"\}", "}")):
        s = s.replace(a, b)
    return s


def _inline(s, where, notes=None):
    """`notes` collects the text of each \\footnote as a Note, numbered in order, where Notes
    are allowed; it is None elsewhere."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            m = re.match(r"[A-Za-z]+", s[i + 1:])
            if not m:
                nxt = s[i + 1:i + 2]
                if nxt not in UNESCAPE:
                    raise FormatError(f"{where}: unsupported '\\{nxt}' near {s[max(0, i - 30):i + 30]!r}")
                out.append(UNESCAPE[nxt])
                i += 2
                continue
            name, i = m.group(0), i + 1 + len(m.group(0))
            if name in WORD_ESCAPES:
                if s[i:i + 2] != "{}":
                    raise FormatError(f"{where}: write \\{name}{{}}")
                out.append(WORD_ESCAPES[name])
                i += 2
            elif name == "nodelink":
                text, i = optional(s, i, where)
                nid, i = group(s, i, where)
                out.append(f"[[{nid}]]" if text is None else f"[[{nid}|{_inline(text, where)}]]")
            elif name == "footnote":
                if notes is None:
                    raise FormatError(f"{where}: Notes (\\footnote) are allowed only in a Summary, a Full tier or a Primer")
                text, i = group(s, i, where)
                notes.append(_inline(text, where))
                out.append(f"[^{len(notes)}]")
            elif name == "eqref":
                label, i = group(s, i, where)
                out.append(f"[[#{label}]]")
            elif name == "citep":
                keys, i = group(s, i, where)
                out.append("[" + "; ".join("@" + k.strip() for k in keys.split(",")) + "]")
            elif name == "citet":
                key, i = group(s, i, where)
                out.append("@" + key.strip())
            elif name == "autolink":
                url, i = group(s, i, where)
                out.append(f"<{unescape_url(url)}>")
            elif name == "href":
                url, i = group(s, i, where)
                text, i = group(s, i, where)
                out.append(f"[{_inline(text, where)}]({unescape_url(url)})")
            elif name in ("textbf", "emph"):
                inner, i = group(s, i, where)
                mark = "**" if name == "textbf" else "*"
                out.append(mark + _inline(inner, where, notes) + mark)
            else:
                raise FormatError(f"{where}: \\{name} is not allowed here (near {s[max(0, i - 40):i + 20]!r})")
            continue
        if s.startswith("``", i) or s.startswith("''", i):
            out.append('"')
            i += 2
            continue
        if c in "{}~":
            raise FormatError(f"{where}: unexpected '{c}' near {s[max(0, i - 30):i + 30]!r}")
        out.append(c)
        i += 1
    return "".join(out)


MATH = re.compile(
    r"\\begin\{equation\}\\label\{(?P<label>eq-[a-z0-9-]+)\}(?P<e>.*?)\\end\{equation\}"
    r"|\\\[(?P<d>.*?)\\\]"
    r"|(?<!\\)\$(?P<i>[^$\n]+?)\$",
    re.S,
)


def _protect_math(text):
    spans = []

    def repl(m):
        if m["label"]:
            spans.append(f"$${m['e']}$$ {{#{m['label']}}}")
        elif m["d"] is not None:
            spans.append(f"$${m['d']}$$")
        else:
            spans.append(f"${m['i']}$")
        return f"\x00{len(spans) - 1}\x00"

    return MATH.sub(repl, text), spans


def inline(text, where="text"):
    """One line of LaTeX in the allowed subset as Markdown."""
    protected, spans = _protect_math(text)
    return _restore_math(_inline(protected, where), spans)


def _row(line, where, notes=None):
    if not line.endswith(" \\\\"):
        raise FormatError(f"{where}: a table row must end with ' \\\\': {line[:60]!r}")
    cells = re.split(r"(?<!\\)&", line[:-3])
    md = [_inline(c.strip(), where, notes) for c in cells]
    return "|" + "|".join(f" {c} " if c else " " for c in md) + "|"


def blocks(text, where="body", notes=True):
    """LaTeX lines written by latexform.blocks back to Markdown, line for line. With `notes`,
    each \\footnote becomes [^n] and its definition `[^n]: text` closes the tier."""
    defs = [] if notes else None
    protected, spans = _protect_math(text.strip("\n"))
    lines = protected.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line == r"\begin{itemize}":
            i += 1
            while i < len(lines) and lines[i] != r"\end{itemize}":
                if not lines[i].startswith("\\item "):
                    raise FormatError(f"{where}: only one-line \\item entries are allowed in a list: {lines[i][:60]!r}")
                out.append("- " + _inline(lines[i][6:], where, defs))
                i += 1
            if i == len(lines):
                raise FormatError(f"{where}: itemize is not closed")
            i += 1
            continue
        m = re.fullmatch(r"\\begin\{pwtable\}\{([lcr]+)\}", line)
        if m:
            spec, rows = m.group(1), []
            i += 1
            while i < len(lines) and lines[i] != r"\end{pwtable}":
                rows.append(lines[i])
                i += 1
            if i == len(lines) or len(rows) < 2 or rows[1] != r"\midrule":
                raise FormatError(f"{where}: a pwtable needs a header row, \\midrule and \\end{{pwtable}}")
            out.append(_row(rows[0], where, defs))
            out.append("|" + "|".join({"l": "---", "c": ":---:", "r": "---:"}[c] for c in spec) + "|")
            out += [_row(r, where, defs) for r in rows[2:]]
            i += 1
            continue
        m = re.fullmatch(r"\\showfigure\{([a-z0-9-]+)\}", line)
        if m:
            out.append(f"![[{m.group(1)}]]")
        elif line.startswith("\\subsection*{") and line.endswith("}"):
            out.append("### " + _inline(line[13:-1], where, defs))
        elif line.startswith("\\subsubsection*{") and line.endswith("}"):
            out.append("#### " + _inline(line[16:-1], where, defs))
        else:
            out.append(_inline(line, where, defs))
        i += 1
    if defs:
        out += ["", *(f"[^{n}]: {d}" for n, d in enumerate(defs, 1))]
    return _restore_math("\n".join(out), spans)
