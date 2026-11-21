# Fidelity check: brief for the subagent

Pass this brief to a fresh subagent together with two paths: the source (the PDF, or the original `.tex`, not the wrapped one) and the Work folder (`works/<id>`). Give it nothing of your own reading of the paper.

---

You are checking a PaperWeave Work, a paper split into Nodes (files in `nodes/`, each with a YAML header and `## Gist`, `## Summary`, `## Full` sections; Primers have no sections), against the paper it was converted from. Read the source yourself; do not trust the Work's account of it. Only read and report; edit nothing.

Expected changes, not findings: numbered equations written `$$…$$ {#eq-name}` and referred to as `[[#eq-name]]`; footnotes turned into Notes (`[^1]` in the text, `[^1]: text` at the end of the tier); "Figure 3" reworded as "the figure below"; "Section 2" turned into a link `[[node-id]]`; a pronoun at the start of a Node replaced by the noun it stood for. Images are in the Work's `figures/` folder: open the image whenever a Gist, Summary or caption claims what a figure shows.

Check, relentlessly and Node by Node:

1. **Transcription.** Every number, unit, equation, table cell and figure caption in the Work matches the source. Every reference in `references.yaml` that the Work cites matches the source's reference list (authors, year, title, venue).
2. **Full tiers.** Each Full tier carries the paper's wording. Report any sentence that is changed in meaning, any passage of the paper's body that appears in no Node, and any that appears in two.
3. **Gists and Summaries.** Each says what the paper says and nothing more: no stronger claim, no missing qualifier, no number the paper does not give, no finding attributed to the wrong case or method.
4. **Primers.** Each is correct as a standalone explanation of its Concept.
5. **Edges.** Each `uses`, `relies_on` and `supports` Edge reflects a dependency the paper actually states or relies on.
6. **The paper itself.** Contradictions within the paper (a number that differs between a table and the text, a claim the figures do not show).

Report one finding per line: the Node id (or `references` / `manifest`), the tier, what the Work says, what the source says (with its page or line), and whether the error is the Work's or the paper's. Report "no findings" for a category only after checking every Node in it.
