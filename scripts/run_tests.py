"""Run every check on the sample Work (and any Work folders given).

Usage: python -P scripts/run_tests.py [works/<id> ...]   (also: npm test)

Needs Node 23.6 or later, bibtex and latexmk, besides Python and PyYAML.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
PER_WORK = ["validate_work.py", "test_paper_order.py", "test_references.py", "test_equations.py", "test_round_trip.py"]


def main(folders):
    folders = folders or ["fixtures/sample-work"]
    runs = [[s, f] for f in folders for s in PER_WORK] + [["test_import_bib.py"]]
    failed = []
    for script, *args in runs:
        print(f"== {script} {' '.join(args)}", flush=True)
        if subprocess.run([sys.executable, "-P", str(HERE / script), *args]).returncode:
            failed.append(" ".join([script, *args]))
    print("\n" + ("FAILED:\n  " + "\n  ".join(failed) if failed else f"all {len(runs)} checks passed"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
