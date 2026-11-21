---
name: convert-paper
description: Convert an existing paper into a PaperWeave Work, from its LaTeX source (the author's own or a third party's, such as an arXiv download) or from its PDF alone. Use when asked to convert, wrap or import a paper.
---

# Convert a paper into a Work

A conversion produces a Work a Reader can trust: the paper's own words in the Full tiers, a graph drafted around them, and a `review.md` that says exactly what was drafted and what still needs a person's eye. The person asking may be the author or a Reader of someone else's paper; either way the paper's text is not yours to improve.

Vocabulary is in `GLOSSARY.md`, the file format in `docs/work-format.md`, and the rules behind them in `docs/adr/`. Read all three before step 3; use their terms exactly.

## Fidelity

The Full tiers carry the paper's wording. Edit a sentence only where a Node boundary cuts it from what it refers to ("It works…" becomes "The DGP works…"), where a figure or section reference has no number to point to, or where the format needs a construct (a Note for a footnote, an Equation label). Typos, contradictions and doubtful numbers in the paper stay as they are and go into `review.md`. The Gists, Summaries and Primers are your words, written to say what the paper says and nothing more.

## Steps

1. **Settle the source and the place.** Find the best source the person has: the LaTeX source when there is one (ask once whether they have it before working from a PDF), else the PDF. Choose a Work id (short, kebab-case) and confirm it with the person. Everything lands in unversioned folders: the source and its wrapped `.tex` in `sources/<paper>/`, the Work in `works/<id>/`. A third party's paper stays there, for private reading; never commit, publish or upload it. Done when the source path, the Work id and the branch (LaTeX or PDF) are fixed.

2. **Bring the text into the format.** Follow the branch file to the end of its own completion criterion:
   - LaTeX source: [latex-source.md](latex-source.md)
   - PDF only: [pdf-source.md](pdf-source.md)

3. **Draft the graph.** Read [authoring.md](authoring.md), then split the text into Nodes and write every Gist, Summary, Primer and Edge by its rules. Done when every passage of the paper's body sits in exactly one Node's Full tier (or is listed in `review.md` as deliberately left out, with the reason), every tiered Node has a Gist, every Result is in the manifest's `results` list in the paper's order, and the one Conclusion synthesises the Results.

4. **Make it pass.** Run, from the repository root:
   - `python -P scripts/validate_work.py works/<id>`: errors fixed; read each note (Inline link without an Edge) and either add the Edge or leave it knowingly.
   - `python -P scripts/test_round_trip.py works/<id>`: every file reproduced byte for byte.
   - `python -P scripts/test_references.py works/<id>`: the app and the bst agree.
   Done when all three pass and, for the LaTeX branch, no `\todo` is left in the `.tex`.

5. **Check fidelity with fresh eyes.** Dispatch a subagent with the brief in [fidelity-check.md](fidelity-check.md), the source path and the Work path, and nothing of your own reading. Fix what it shows to be your error (a mistranscribed number, a Gist that overstates); record what it shows to be the paper's own problem in `review.md`. Done when every finding is either fixed or recorded.

6. **Write the review record.** Fill [review-template.md](review-template.md) into `review.md` beside the source (`sources/<paper>/review.md`), never inside the Work. Done when it lists every item the helpers asked to check, every text you wrote, every edit you made to the paper's wording, everything left out, and every problem found in the paper.

7. **Show it.** Tell the person the Work id, how to open it (`npm run dev`, then `?work=<id>`), and that `review.md` is theirs to go through: the Gists, Summaries and Primers are a draft in your words, not the author's, until someone checks them.
