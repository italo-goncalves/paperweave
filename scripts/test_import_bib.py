"""Check scripts/import_bib.py on the quirks reference managers export.

Usage: python -P scripts/test_import_bib.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bibtex import read_bib, write_bib  # noqa: E402
from import_bib import import_bib  # noqa: E402

BIB = r"""
@article{Conf2013,
   abstract = {Long text.},
   author = {Andreas C Damianou and Neil D. Lawrence},
   doi = {10.1002/wrong.1},
   journal = {International Conference on Artificial Intelligence and Statistics},
   pages = {207-215},
   title = {Deep {Gaussian} Processes},
   volume = {31},
   year = {2013},
}
@article{Thesis2003,
   author = {Christopher Joseph Paciorek},
   institution = {Carnegie Mellon University},
   journal = {Thesis},
   pages = {258},
   title = {Nonstationary Gaussian processes},
   url = {http://example.org/download?doi=1&amp;type=pdf},
   year = {2003},
}
@article{Journal2017,
   author = {{\'I}talo Gon{\c c}alves and Felipe Kumaira},
   doi = {10.1016/j.cageo.2017.03.015},
   issn = {0098-3004},
   issue = {March 2017},
   journal = {Computers {\&} Geosciences},
   title = {A geostatistical method},
   url = {https://doi.org/10.1016/j.cageo.2017.03.015},
   volume = {103},
   year = {2017},
}
@inproceedings{Short1996,
   author = {Christopher Williams and Uk Sheffield and Nd Lawrence},
   booktitle = {NIPS},
   title = {Computing with infinite networks},
   year = {1996},
}
@book{Uncited2006,
   author = {Carl Edward Rasmussen},
   title = {Gaussian processes for machine learning},
   year = {2006},
}
"""

refs, fixed, check = import_bib(BIB, cited={"Conf2013", "Thesis2003", "Journal2017", "Short1996", "Missing2020"})
fails = []


def expect(cond, what):
    if not cond:
        fails.append(what)


c = refs["Conf2013"]
expect(c["type"] == "inproceedings" and c["booktitle"].startswith("International") and "journal" not in c, "conference retyped")
expect(c["volume"] == "31" and c["pages"] == "207–215", "volume kept, pages with an en dash")
expect(c["author"] == ["Damianou, Andreas C.", "Lawrence, Neil D."], "names normalised")
expect(c["title"] == "Deep Gaussian Processes" and "abstract" not in c, "braces and abstract removed")
t = refs["Thesis2003"]
expect(t["type"] == "thesis" and t["school"] == "Carnegie Mellon University" and "pages" not in t, "thesis retyped")
expect(t["url"] == "http://example.org/download?doi=1&type=pdf", "HTML entity removed")
j = refs["Journal2017"]
expect("number" not in j and "url" not in j and "issn" not in j, "date in issue, DOI url and issn dropped")
expect(j["author"][0] == "Gonçalves, Ítalo" and j["journal"] == "Computers & Geosciences", "TeX accents decoded")
expect("Uncited2006" not in refs, "uncited entry left out")
text = "\n".join(check)
for needle in ("Missing2020", "10.1002/wrong.1", "'Uk'", "'Nd'", "'NIPS'", "spot-check them: Journal2017"):
    expect(needle in text, f"to check mentions {needle}")
expect(read_bib(write_bib(refs)) == refs, "written .bib reads back the same")

if fails:
    print("FAILED:\n  " + "\n  ".join(fails))
    sys.exit(1)
print(f"import_bib: {len(refs)} references, {len(fixed)} fixes, {len(check)} items to check, all as expected")
