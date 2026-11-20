# Work format

Each Work is stored as a folder. The reading app loads the folder as-is; it is never compiled.

```
works/<work-id>/
├── manifest.yaml      # title, authors, Abstract, Result order, Conclusion, Figures
├── references.yaml    # citation key → reference fields
├── figures/           # image files that Figures point to
└── nodes/
    └── <node-id>.md   # one file per Node
```

## manifest.yaml

```yaml
id: deep-gp-networks
title: Uncertainty propagation in deep Gaussian process networks
authors: [Ítalo Gomes Gonçalves, Florian Wellmann]
year: 2023
venue: Mathematical Geosciences
doi: https://doi.org/10.1007/s11004-025-10187-4   # optional, shown as a link
abstract: |
  Markdown text.
results: [result-vein, result-gold, result-solar]   # Results list order, set by the author
conclusion: conclusion
order: [context-intro, gp-node, ...]   # optional: every Node id in Paper order (ADR 0003)
figures:
  fig-vein:
    file: figures/vein.jpg
    caption: Markdown caption.
```

- **`order`** is optional. When it is missing, the Paper order is computed: Context, Concepts (each followed by its Primers), Methods, Results, Discussions, Conclusion; within a type, what a Node depends on comes first. When present, it must list every Node once and follow that grouping. LaTeX → Work always writes it.

## references.yaml

One entry per citation key, with BibTeX-like fields (ADR 0004). The citation label and the formatted text are not stored; PaperWeave's author-year style derives them.

```yaml
Damianou2013:
  type: inproceedings        # article | inproceedings | incollection | book | thesis | report | misc
  author: ["Damianou, Andreas C.", "Lawrence, Neil D."]   # "Family, Given", in order
  year: 2013
  title: Deep Gaussian processes
  booktitle: International Conference on Artificial Intelligence and Statistics
  volume: 31
  pages: 207–215
  doi: https://doi.org/...   # optional
```

## Node files

A YAML header followed by a Markdown body.

```markdown
---
id: sde-node              # same as the filename; stable
type: method              # result | method | concept | primer | context | discussion | conclusion
title: SDE node
contribution: true        # optional, defaults to false
edges:                    # optional; only the Edge types this Node actually has
  uses: [gp-node]
  relies_on: [covariance-stationarity]
---

## Gist
One line. Required for every type except primer.

## Summary
One paragraph. Optional.

## Full
Complete content. Optional.
```

- **Detail tiers** are the `## Gist`, `## Summary` and `## Full` headings, in that order. If a tier is missing, the next shorter one is shown instead. Headings of level 3 and below are free to use inside a tier.
- **Primers** have no tier headings. The whole body is their single level.
- **Edge keys** and which Node types they may connect (the source is the Node whose file declares the Edge):

  | key           | from               | to                |
  |---------------|--------------------|-------------------|
  | `uses`        | result, method     | method            |
  | `relies_on`   | result, method, concept | concept      |
  | `supports`    | result             | result            |
  | `explains`    | primer             | concept           |
  | `discusses`   | discussion         | any               |
  | `situates`    | context            | any               |
  | `synthesises` | conclusion         | result            |

## Body syntax

- **Inline link:** `[[node-id]]` or `[[node-id|shown text]]`. For navigation only; it never creates an Edge (ADR 0001).
- **Figure:** `![[fig-id]]` on a line of its own. The image and caption come from `manifest.yaml`. A Figure may appear in more than one Node.
- **Citation:** `[@Key]` in parentheses, `@Key` in running text, and `[@Key1; @Key2]` for several. Keys are looked up in `references.yaml`.
- **Math:** `$…$` inline and `$$…$$` for display, rendered with KaTeX. Use `\boldsymbol` (not `\pmb`) and `\operatorname{Diag}`. For multi-line math use `aligned` or `gathered`. There are no equation labels; refer to an equation through the Node that contains it.
