"""Check that the Linear version numbers equations as the app does, at every Detail tier.

Usage: python -P scripts/test_equations.py works/<id> [...]
Builds the Work with the PaperWeave class at tier=gist, summary and full, with and without
Primers, and compares the numbers the class assigns (from the .aux file) with the app's
(src/equations.ts). Needs latexmk and Node 23.6 or later.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from work_to_latex import build_pdf, export  # noqa: E402
from workformat import Work, split_tiers  # noqa: E402


def app_numbers(work):
    nodes = {}
    for nid, n in work.nodes.items():
        tiers = {"full": n["body"].strip()} if work.type_of(nid) == "primer" else split_tiers(n["body"])
        nodes[nid] = {"tiers": tiers}
    out = subprocess.run(
        ["node", "--no-warnings", str(HERE / "equation_numbers_cli.mjs")],
        input=json.dumps({"nodes": nodes, "order": work.paper_order()}), capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode:
        raise SystemExit(out.stderr)
    return json.loads(out.stdout)


def main(folders):
    failed = False
    for folder in folders:
        app = app_numbers(Work(folder))
        for tier in ("gist", "summary", "full"):
            for noprimers in (False, True):
                with tempfile.TemporaryDirectory() as tmp:
                    out = export(folder, tmp, tier, noprimers)
                    build_pdf(out)
                    aux = (out / "main.aux").read_text(encoding="utf-8", errors="replace")
                latex = {m[0]: int(m[1]) for m in re.findall(r"\\pw@seteq\s*\{(eq-[a-z0-9-]+)\}\{(\d+)\}", aux)}
                ok = latex == app
                failed |= not ok
                label = f"tier={tier}{', noprimers' if noprimers else ''}"
                print(f"{folder} [{label}]: {'same' if ok else 'DIFFERENT'} numbers for {len(app)} equations")
                if not ok:
                    print(f"  app:   {app}\n  latex: {latex}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
