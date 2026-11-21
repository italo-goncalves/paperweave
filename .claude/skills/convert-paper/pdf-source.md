# PDF branch

With no source, the Work files are the master and every character is transcribed, so this branch carries the most risk of silent error. Transcribe; never paraphrase the paper's body.

1. **Read the pages.** Extract the text layer with PyMuPDF (`import pymupdf`). If a page has no text layer, or the layer garbles math, read the page as an image instead. Note page numbers as you go; `review.md` and the fidelity check refer to them.

2. **Extract the figures.** Take each figure at full resolution: embedded images with PyMuPDF where they exist, otherwise a crop of the page rendered at 200 dpi or more. Save them to `works/<id>/figures/` with descriptive names, and declare each in `manifest.yaml` with its caption transcribed. A table becomes a Markdown table in the Node that presents it, not an image, unless its layout cannot be expressed as a pipe table.

3. **Transcribe the body** into the body syntax of `docs/work-format.md`: equations as LaTeX math (labelled with `{#eq-...}` only where some Node refers to them), footnotes as Notes, citations as `[@Key]` / `@Key`, lists and tables in Markdown. Hold the text aside for the Node split of step 3; do not write Node files yet.

4. **Transcribe the references** into `references.yaml`, one structured entry per cited reference (fields and types in `docs/work-format.md`), with keys of the form `Family2020` (`Family2020a`/`b` for clashes). Write a DOI only when the PDF prints it.

5. **Write the manifest** (`id`, `title`, `authors`, `year`, `venue`, `doi`, `abstract`, `figures`; `results` and `conclusion` come in step 3). Done when the manifest, references and figures exist and the whole body text is transcribed.
