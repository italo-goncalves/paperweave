"""Check that latex/paperweave.bst and the app (src/references.ts) format references alike.

Usage: python -P scripts/test_references.py works/<id> [...]
Writes each Work's references as BibTeX, runs bibtex with paperweave.bst, and compares
every label and text with the app's formatter. Needs bibtex and Node 23.6 or later.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from bibtex import untex, write_bib  # noqa: E402
from workformat import Work  # noqa: E402

LATEX = HERE.parent / "latex"


def app_format(refs):
    out = subprocess.run(
        ["node", "--no-warnings", str(HERE / "format_references_cli.mjs")],
        input=json.dumps(refs), capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode:
        raise SystemExit(out.stderr)
    return json.loads(out.stdout)


def bst_format(refs):
    """{key: {label, text}} from a bibtex run with paperweave.bst."""
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "refs.bib").write_text(write_bib(refs), encoding="utf-8")
        Path(tmp, "t.aux").write_text("\\citation{*}\n\\bibdata{refs}\n\\bibstyle{paperweave}\n", encoding="utf-8")
        env = dict(os.environ, BSTINPUTS=f"{LATEX}{os.pathsep}")
        run = subprocess.run(["bibtex", "t"], cwd=tmp, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        bbl = Path(tmp, "t.bbl")
        if not bbl.exists() or "error message" in run.stdout:
            raise SystemExit(run.stdout)
        text = bbl.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"\\bibitem\[\{(.*?)\((.*?)\)(.*?)\}\]\{(.*?)\}\n(.*?)(?=\n\n|\n\\end)", text, re.S):
        short, year, _long, key, body = m.groups()
        body = re.sub(r"\\url\{(.*?)\}", r"\1", " ".join(body.split()))
        out[key] = {"label": untex(f"{short} {year}"), "text": untex(body)}
    return out


def main(folders):
    failed = False
    for folder in folders:
        refs = Work(folder).references
        app, bst = app_format(refs), bst_format(refs)
        bad = [k for k in refs if app.get(k) != bst.get(k)]
        for k in bad:
            print(f"{folder}: {k}\n  app: {app.get(k)}\n  bst: {bst.get(k)}")
        print(f"{folder}: {len(refs) - len(bad)} of {len(refs)} references alike")
        failed |= bool(bad)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
