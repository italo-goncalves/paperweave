# LaTeX source branch

The wrapped `.tex` in `sources/<paper>/paperweave/main.tex` becomes the master: later corrections go into it and are imported again. The class accepts only its own subset (ADR 0002); anything else is an error with its location, so the importer is the check that nothing was lost.

1. **Make one file.** If the paper is split across files (`\input`, `\include`, `\subfile`), inline them into one `.tex` in place, in the copy under `sources/`. If it defines macros (`\newcommand`, `\def`, `\renewcommand`), expand each use by hand in the copy: math in a Work is rendered by KaTeX, which knows none of them (`\DeclareMathOperator` names are handled by the helper). Done when one file holds the whole paper and defines no macros the body uses.

2. **Run the helper.**
   `python -P scripts/prepare_legacy.py <paper.tex> "sources/<paper>/paperweave" --id=<id>` (add `--bib=<file.bib>` when the `.bib` is not named by `\bibliography`).
   It rewrites what has one obvious form, imports the cited references through `scripts/import_bib.py`, and prints a report: equations relabelled, align blocks split, things dropped, references fixed and to check, and the `\todo` markers it left. Keep the printed report; it feeds `review.md`. Copy `main.tex` to `prepared.tex` before editing, so the mechanical output stays on record.

   **No `.bib`, only a `.bbl`** (common on arXiv): the helper finds no references. Write `references.bib` by hand from the `.bbl`, one structured entry per cited key (fields as in `docs/work-format.md`), and list in `review.md` that references were transcribed.

3. **Wrap in Nodes.** In `main.tex`, put each passage inside a Node environment (`\begin{result}[contribution]{id}{Title}` …), with Edge commands, `\gist{}`, and `summary` / `full` environments, following [authoring.md](authoring.md). Nodes must be written in Paper order by type. Primers go in `primers/<id>.tex`, pulled in with `\includeprimer{id}`. The manifest-level commands (`\workyear`, `\code`, `\doi`, `\results`) go in the preamble; see an exported Work for the exact layout: `python -P scripts/work_to_latex.py fixtures/sample-work build/latex/sample`.

4. **Resolve every `\todo`.** Section headings become Node boundaries. A reference to a figure becomes wording such as "the figure below", with the `\showfigure` where the Node needs it. A reference to a section becomes `\nodelink{id}`. A citation with a prefix (`\citep[DGP;][]{…}`) becomes ordinary text plus `\citep`. An address without `https://` gets one, if you can confirm it.

5. **Import.** `python -P scripts/latex_to_work.py "sources/<paper>/paperweave" works/<id>`. Each error names a file and line or a Node and tier; fix it in `main.tex` and import again. Done when the import succeeds.
