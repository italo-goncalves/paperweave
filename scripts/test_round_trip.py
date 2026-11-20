"""Round trip: Work → LaTeX → Work must reproduce the Work byte for byte (ADR 0002).

Usage: python -P scripts/test_round_trip.py [--canonicalise] works/<id> [...]

For each Work: write it in canonical form, export it to LaTeX, import that back, and
compare every file. Also reports whether the Work's own files are already canonical;
with --canonicalise, rewrites them in place (once, after checking the round trip).
"""
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from latex_to_work import import_latex  # noqa: E402
from work_to_latex import export  # noqa: E402
from workformat import Work  # noqa: E402
from workwriter import canonicalise  # noqa: E402


def files(folder):
    return sorted(p.relative_to(folder).as_posix() for p in Path(folder).rglob("*") if p.is_file())


def differences(a, b):
    fa, fb = files(a), files(b)
    out = [f"only in first: {f}" for f in fa if f not in fb] + [f"only in second: {f}" for f in fb if f not in fa]
    out += [f"differs: {f}" for f in fa if f in fb and not filecmp.cmp(Path(a, f), Path(b, f), shallow=False)]
    return out


def main(args):
    write = "--canonicalise" in args
    failed = False
    for folder in [a for a in args if not a.startswith("--")]:
        with tempfile.TemporaryDirectory() as tmp:
            canon = canonicalise(Work(folder), Path(tmp, "canonical"))
            tex = export(canon, Path(tmp, "latex"))
            back = import_latex(tex, Path(tmp, "back"))
            diff = differences(canon, back)
            if diff:
                failed = True
                print(f"{folder}: round trip DIFFERS")
                for d in diff:
                    print("  ", d)
                    if d.startswith("differs: "):
                        f = d[9:]
                        a = Path(canon, f).read_text(encoding="utf-8").split("\n")
                        b = Path(back, f).read_text(encoding="utf-8").split("\n")
                        import difflib

                        print("\n".join("      " + l for l in list(difflib.unified_diff(a, b, lineterm=""))[2:14]))
                continue
            print(f"{folder}: Work → LaTeX → Work reproduces all {len(files(canon))} files")
            own = differences(folder, canon)
            if own and write:
                for f in files(folder):
                    if f.startswith(("nodes/", "manifest.yaml", "references.yaml")):
                        Path(folder, f).unlink()
                for f in files(canon):
                    if not f.startswith("figures/"):
                        Path(folder, f).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(Path(canon, f), Path(folder, f))
                print(f"  rewrote {len(own)} file(s) in canonical form")
            elif own:
                print(f"  {len(own)} file(s) are not yet in canonical form (run with --canonicalise):")
                for d in own[:8]:
                    print("    ", d)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
