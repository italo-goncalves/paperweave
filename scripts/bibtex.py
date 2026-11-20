"""Converting between BibTeX and references.yaml fields (ADR 0004).

`write_bib` is used by Work → LaTeX and is the exact inverse of `read_bib` on what it
writes. `read_bib` also accepts ordinary .bib files (for wrapping existing papers),
normalising names to "Family, Given", pages to an en dash and dropping fields that
references.yaml does not keep.
"""
import re

FIELDS = [
    "author", "editor", "year", "title", "journal", "booktitle", "volume", "number", "pages", "edition",
    "publisher", "address", "school", "institution", "kind", "note", "doi", "url",
]
BIB_TYPES = {  # references.yaml type -> BibTeX entry type
    "article": "article", "inproceedings": "inproceedings", "incollection": "incollection", "book": "book",
    "thesis": "phdthesis", "report": "techreport", "misc": "misc",
}
FROM_BIB = {v: k for k, v in BIB_TYPES.items()} | {"conference": "inproceedings", "mastersthesis": "thesis", "online": "misc"}
BIB_FIELD = {"kind": "type"}  # references.yaml field -> BibTeX field, where they differ
FROM_FIELD = {v: k for k, v in BIB_FIELD.items()}

# Accented letters written as TeX commands in names, so BibTeX takes whole letters as initials.
ACCENTS = {"\u0301": "'", "\u0300": "`", "\u0302": "^", "\u0308": '"', "\u0303": "~", "\u0327": "c", "\u030c": "v", "\u0304": "="}
PARTICLES = {"van", "von", "der", "den", "de", "da", "del", "di", "du", "la", "le", "dos", "das"}


def tex_name(s):
    import unicodedata

    out = []
    for ch in s:
        d = unicodedata.normalize("NFD", ch)
        if len(d) == 2 and d[1] in ACCENTS:
            out.append("{\\%s%s%s}" % (ACCENTS[d[1]], " " if ACCENTS[d[1]].isalpha() else "", d[0]))
        else:
            out.append(ch)
    return "".join(out)


def untex(s):
    """TeX accent commands back to Unicode, and braces removed."""
    import unicodedata

    inv = {v: k for k, v in ACCENTS.items()}

    def repl(m):
        return unicodedata.normalize("NFC", m.group(2) + inv[m.group(1)])

    s = re.sub(r"\{\\([`'^\"~=])\s*([A-Za-z])\}", repl, s)
    s = re.sub(r"\{\\([cv])\s+([A-Za-z])\}", repl, s)
    s = re.sub(r"\\([`'^\"~=])\{?([A-Za-z])\}?", repl, s)
    s = re.sub(r"\\([&%#_])", r"\1", s).replace("--", "–").replace("~", " ")
    return re.sub(r"[{}]", "", s)


def _wrapped(s):
    """True when the whole string is one {…} group, as for an organisation's name."""
    if not (s.startswith("{") and s.endswith("}")):
        return False
    depth = 0
    for i, c in enumerate(s):
        depth += {"{": 1, "}": -1}.get(c, 0)
        if depth == 0 and i < len(s) - 1:
            return False
    return True


def _person(name):
    name = " ".join(name.split())
    if _wrapped(name):
        return untex(name)  # an organisation
    name = untex(name)
    if "," in name:
        family, given = (p.strip() for p in name.split(",", 1))
        return f"{family}, {given}" if given else family
    parts = name.split(" ")
    i = len(parts) - 1
    while i > 0 and parts[i - 1].lower() in PARTICLES:
        i -= 1
    family, given = " ".join(parts[i:]), " ".join(parts[:i])
    given = re.sub(r"\b([A-Z])(?=\s|$)", r"\1.", given)  # bare initials get a dot
    return f"{family}, {given}" if given else family


def _split_and(value):
    depth, parts, cur = 0, [], ""
    tokens = re.split(r"(\{|\}|\s+and\s+)", value)
    for t in tokens:
        if t == "{":
            depth += 1
        elif t == "}":
            depth -= 1
        if re.fullmatch(r"\s+and\s+", t or "") and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += t
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def _entries(text):
    i = 0
    while True:
        m = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,").search(text, i)
        if not m:
            return
        depth, j = 1, m.end()
        while depth and j < len(text):
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            j += 1
        yield m.group(1).lower(), m.group(2), text[m.end() : j - 1]
        i = j


def _fields(body):
    out, i = {}, 0
    pat = re.compile(r"\s*,?\s*([A-Za-z]+)\s*=\s*")
    while True:
        m = pat.match(body, i)
        if not m or m.end() >= len(body):
            return out
        j = m.end()
        if body[j] == "{":
            depth, k = 1, j + 1
            while depth:
                depth += {"{": 1, "}": -1}.get(body[k], 0)
                k += 1
            value = body[j + 1 : k - 1]
        elif body[j] == '"':
            k = body.index('"', j + 1) + 1
            value = body[j + 1 : k - 1]
        else:
            k = j
            while k < len(body) and body[k] not in ",\n":
                k += 1
            value = body[j:k].strip()
        out[m.group(1).lower()] = value
        i = k


def read_bib(text):
    """{key: fields} with only the fields references.yaml keeps, in FIELDS order."""
    refs = {}
    for etype, key, body in _entries(text):
        raw = _fields(body)
        r = {"type": FROM_BIB.get(etype, "misc")}
        for bf, value in raw.items():
            f = FROM_FIELD.get(bf, bf)
            if f not in FIELDS:
                continue
            value = " ".join(value.split())
            if f in ("author", "editor"):
                r[f] = [_person(p) for p in _split_and(value)]
            elif f == "year":
                r[f] = int(value) if value.isdigit() else value
            elif f == "doi":
                r[f] = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
            elif f == "url":
                r[f] = value
            elif f == "pages":
                r[f] = untex(re.sub(r"(?<=\d)\s*-{1,2}\s*(?=\d)", "–", value))
            else:
                r[f] = untex(value)
        if r["type"] in ("inproceedings", "incollection") and "journal" in r and "booktitle" not in r:
            r["booktitle"] = r.pop("journal")  # a common reference-manager quirk
        refs[key] = {k: r[k] for k in ["type", *FIELDS] if k in r}
    return refs


def _bib_value(field, value):
    if field in ("author", "editor"):
        people = []
        for p in value:
            people.append(tex_name(p) if "," in p else "{" + tex_name(p) + "}")
        return " and ".join(people)
    s = str(value)
    if field in ("url", "doi"):
        return s
    for ch in "&%#_":
        s = s.replace(ch, "\\" + ch)
    return s.replace("–", "--")


def write_bib(refs):
    """BibTeX text for references.yaml fields, entries in key order."""
    out = []
    for key in sorted(refs):
        r = refs[key]
        lines = [f"@{BIB_TYPES[r['type']]}{{{key},"]
        for f in FIELDS:
            if f in r and r[f] not in (None, "", []):
                lines.append(f"  {BIB_FIELD.get(f, f)} = {{{_bib_value(f, r[f])}}},")
        lines.append("}")
        out.append("\n".join(lines))
    return "\n\n".join(out) + "\n"


def dump_references(refs):
    """Canonical references.yaml text: keys sorted, fields in FIELDS order."""
    import yaml

    out = []
    for key in sorted(refs):
        r = refs[key]
        entry = {k: r[k] for k in ["type", *FIELDS] if k in r and r[k] not in (None, "", [])}
        for k in ("volume", "number", "pages", "edition"):  # always text, as BibTeX gives them back
            if k in entry:
                entry[k] = str(entry[k])
        out.append(yaml.safe_dump({key: entry}, allow_unicode=True, sort_keys=False, width=10**9, default_flow_style=None))
    return "".join(out)
