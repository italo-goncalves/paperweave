"""Check that the app (src/paperOrder.ts) and the Python tools give the same Paper order.

Usage: python -P scripts/test_paper_order.py works/<id> [...]
Needs Node 23.6 or later, which runs TypeScript directly.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from workformat import Work  # noqa: E402

CLI = Path(__file__).parent / "paper_order_cli.mjs"


def main(folders):
    failed = False
    for folder in folders:
        w = Work(folder)
        py = w.paper_order()
        payload = {
            "nodes": {nid: {"type": w.type_of(nid)} for nid in w.nodes},
            "edges": [{"type": t, "from": a, "to": b} for t, a, b in w.edges],
            "results": w.manifest.get("results") or [],
            "order": w.manifest.get("order"),
        }
        out = subprocess.run(
            ["node", "--no-warnings", str(CLI)], input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8"
        )
        if out.returncode:
            print(out.stderr)
            sys.exit(2)
        ts = json.loads(out.stdout)
        if ts == py:
            print(f"{folder}: same Paper order ({len(py)} Nodes)")
        else:
            failed = True
            print(f"{folder}: DIFFERENT\n  python: {py}\n  app:    {ts}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
