# References are structured fields formatted by one PaperWeave author-year style

`references.yaml` held each reference as a finished `label` and `text`. That text cannot be carried through LaTeX deterministically: BibTeX would regenerate it from a `.bib` file through whatever style the document loads, and the result would differ from what was stored. We decided that references are stored as structured, BibTeX-like fields (entry type, authors, year, title, venue, volume, pages, DOI and so on), and that PaperWeave owns one author-year style that formats them. The app formats references with it, and the PaperWeave class ships a `paperweave.bst` that produces the same text in the Linear version. `.bib` ↔ `references.yaml` is then a field-by-field conversion with no formatting step.

## Considered options

- **Keep formatted text and carry it verbatim in LaTeX**, in a `thebibliography`-like block. Rejected: references could not be restyled, searched by field, or shared between Works in a library, and authors would not write their references that way.
- **Use BibTeX output as the stored text.** Rejected: the text would depend on the chosen style and toolchain, which breaks deterministic round trips.

## Consequences

- The app needs a reference formatter, and `paperweave.bst` must be kept identical to it. A test compares the two on every sample Work.
- Citation labels (such as "Damianou and Lawrence 2013") are derived from the fields, not stored.
- Existing Works are migrated once. A Work whose references were transcribed from a PDF needs them split into fields and checked by hand, as with any converted content.
