"""Import a paper's own .bib file into PaperWeave's references (one way, ADR 0004).

Usage: python -P scripts/import_bib.py <library.bib> <out> [--cited=<main.tex or Work folder>]

<out> ending in .yaml gets references.yaml; anything else gets a canonical references.bib
for a document in the PaperWeave class. With --cited, only the entries cited there are
kept (from \\citep/\\citet in a .tex file, or @Key in a Work's Nodes, manifest and
captions).

Reference managers export entries that read as BibTeX but are often wrong in ways a
style then prints. The helper fixes what has one obvious repair and lists what needs a
person to check, in the same spirit as prepare_legacy.py:

  fixed     an article whose "journal" is a conference -> inproceedings with a booktitle
            an article whose "journal" says Thesis -> thesis, its institution as the school
            "issue" -> number, unless it holds a date ("May", "July 2021"); a url that
            only repeats the DOI; HTML entities such as &amp; in addresses
            fields references.yaml does not keep (abstract, isbn, issn, pmid, keywords,
            file, ...) dropped
  to check  DOIs, above all on conference papers, books and theses (managers often attach
            a journal paper's DOI to them), given names that look
            like run-together initials or affiliations ("Nd", "Uk"), abbreviated booktitles
            ("NIPS"), addresses without http(s)://, entries missing a field their type
            needs, and cited keys with no entry
"""
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from bibtex import _entries, _fields, dump_references, read_bib, write_bib  # noqa: E402

CONFERENCE = re.compile(r"conference|proceedings|workshop|symposium|advances in neural information|"
                        r"uncertainty in artificial intelligence|artificial intelligence and statistics|\bicml\b|\bneurips\b|\bnips\b",
                        re.I)
MONTH = re.compile(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?", re.I)
NEEDS = {"article": ["journal"], "inproceedings": ["booktitle"], "incollection": ["booktitle"],
         "book": ["publisher"], "thesis": ["school"], "report": ["institution"]}
KEY = r"[A-Za-z][A-Za-z0-9_:.-]*[A-Za-z0-9]"


def cited_keys(path):
    """Keys cited in a .tex file or a Work folder."""
    path = Path(path)
    keys = set()
    if path.is_dir():
        texts = [p.read_text(encoding="utf-8") for p in [*(path / "nodes").glob("*.md"), path / "manifest.yaml"]]
        for t in texts:
            keys |= set(re.findall(r"(?:^|[\s(\[;])@(" + KEY + r")", t))
    else:
        for m in re.finditer(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}", path.read_text(encoding="utf-8")):
            keys |= {k.strip() for k in m.group(1).split(",") if k.strip()}
    return keys


def import_bib(text, cited=None):
    """(references.yaml fields, fixes made, things to check) for a .bib text."""
    raw = {key: (etype, _fields(body)) for etype, key, body in _entries(text)}
    # Fields read_bib does not know under these names.
    text = re.sub(r"(?m)^(\s*)issue(\s*=)", r"\1number\2", text)
    refs = read_bib(text)
    fixed, check = [], []
    if cited is not None:
        missing = sorted(cited - set(refs))
        if missing:
            check.append(f"cited but not in the .bib: {', '.join(missing)}")
        dropped = len(refs) - len(cited & set(refs))
        refs = {k: v for k, v in refs.items() if k in cited}
        if dropped:
            fixed.append(f"left out {dropped} entries that are never cited")

    dropped_fields, article_dois = {}, []
    for key, r in refs.items():
        etype, fields = raw[key]
        journal = r.get("journal", "")
        if r["type"] == "article" and re.search(r"\bthesis\b|dissertation", journal, re.I):
            r.pop("journal")
            r["type"] = "thesis"
            if "institution" in r and "school" not in r:
                r["school"] = r.pop("institution")
            r.pop("pages", None)
            fixed.append(f"{key}: an article in the journal '{journal}' made a thesis")
        elif r["type"] == "article" and CONFERENCE.search(journal):
            r["type"] = "inproceedings"
            r["booktitle"] = r.pop("journal")
            fixed.append(f"{key}: an article in '{journal}' made a conference paper (booktitle)")
        number = str(r.get("number", ""))
        if number and not re.fullmatch(r"[0-9A-Za-z]{1,6}(?:[-–/][0-9A-Za-z]{1,6})?", number) or MONTH.fullmatch(number):
            r.pop("number")
            fixed.append(f"{key}: dropped number '{number}', a date rather than an issue")
        url = r.get("url", "")
        if url and "doi" in r and re.sub(r"^https?://(dx\.)?doi\.org/", "", url) == r["doi"]:
            r.pop("url")
            fixed.append(f"{key}: dropped the url, which only repeats the DOI")
        elif url and not re.match(r"https?://", url):
            check.append(f"{key}: url '{url}' has no http(s)://")
        book = r.get("booktitle", "")
        if book and (len(book) <= 10 or book.isupper()):
            check.append(f"{key}: booktitle '{book}' looks abbreviated; write the full proceedings title")
        if "url" in r and html.unescape(r["url"]) != r["url"]:
            r["url"] = html.unescape(r["url"])
            fixed.append(f"{key}: HTML entities removed from the url")
        if "doi" in r and r["type"] == "article":
            article_dois.append(key)
        elif "doi" in r:
            kind = {"inproceedings": "conference paper", "incollection": "chapter"}.get(r["type"], r["type"])
            check.append(f"{key}: doi {r['doi']} on a {kind}: often another paper's DOI, check or remove it")
        for person in r.get("author", []) + r.get("editor", []):
            given = person.split(", ", 1)[1] if ", " in person else ""
            for part in given.split():
                if re.fullmatch(r"[A-Z][a-z]", part) and part[1] not in "aeiou" or part in ("Uk", "Us", "Usa"):
                    check.append(f"{key}: author '{person}': is '{part}' initials or an affiliation?")
        for f in NEEDS.get(r["type"], []):
            if f not in r:
                check.append(f"{key}: a {r['type']} with no {f}")
        dropped = sorted(set(fields) - {"author", "editor", "year", "title", "journal", "booktitle", "volume",
                                         "number", "issue", "pages", "edition", "publisher", "address", "school",
                                         "institution", "type", "note", "doi", "url"})
        for f in dropped:
            dropped_fields[f] = dropped_fields.get(f, 0) + 1
        order = ["type", "author", "editor", "year", "title", "journal", "booktitle", "volume", "number", "pages",
                 "edition", "publisher", "address", "school", "institution", "kind", "note", "doi", "url"]
        refs[key] = {k: r[k] for k in order if k in r}
    if dropped_fields:
        fixed.append("dropped fields references.yaml does not keep: "
                     + ", ".join(f"{f} ({n})" for f, n in sorted(dropped_fields.items(), key=lambda x: -x[1])))
    if article_dois:
        check.append(f"DOIs kept on {len(article_dois)} articles; spot-check them: {', '.join(article_dois)}")
    return refs, fixed, check


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in argv if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    cited = cited_keys(opts["cited"]) if "cited" in opts else None
    refs, fixed, check = import_bib(Path(args[0]).read_text(encoding="utf-8"), cited)
    out = Path(args[1])
    out.write_text(dump_references(refs) if out.suffix == ".yaml" else write_bib(refs), encoding="utf-8", newline="\n")
    print(f"wrote {out}: {len(refs)} references")
    print(f"fixed ({len(fixed)}):" + "".join(f"\n  {f}" for f in fixed))
    print(f"to check ({len(check)}):" + "".join(f"\n  {c}" for c in check))


if __name__ == "__main__":
    main(sys.argv[1:])
