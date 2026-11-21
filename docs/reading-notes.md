# Reading notes

Observations from using the reading prototype, gathered to judge whether reading a Work as a graph beats reading the PDF. Newest first. Record what was seen, who saw it, and what it suggests; keep fixes and decisions in their own places.

## 2026-11-21 · Wrapping an existing LaTeX paper in the PaperWeave class

**Observed:** the deep GP paper's original source (`version_1.tex`, 473 lines, Springer's svjour3 class) was wrapped in the PaperWeave class and imported as `works/deep-gp-wrapped`. This happened in two steps.
- **Mechanical step** (`scripts/prepare_legacy.py`, seconds). It converted the title, authors, abstract, keywords and venue. It numbered the 16 labelled equations, splitting three `align` blocks into 11 single displays, and turned 11 `figure*` environments into Figures. It kept the paper's 4 footnotes as Notes. It dropped comments, the funding `\thanks`, the affiliations, the acknowledgements and the declarations. It left 34 `\todo` markers:
  - 12 section headings,
  - 19 references to figures or sections,
  - 2 citations with a prefix (`\citep[DGP;][]`),
  - 1 address without `https://`.
- **Markup step** (done by Claude, reusing the decisions already made in `works/deep-gp-networks`):
  - wrapping the text in 26 Node environments and including the 2 Primers,
  - copying in the Gists, Summaries and Edges,
  - resolving every marker: section headings became Node boundaries, figure references became "the figure below", and section references became Inline links,
  - a few small edits where a Node boundary cut a sentence off from its context, such as "It works similarly" becoming "The DGP works similarly".

The document imported on the first attempt and passed the validator. It survives Work → LaTeX → Work byte for byte (41 files), and its PDF builds.

**Compared with the hand-converted Work:**
- Headers, Gists, Summaries, Edges and references are identical, because they were reused.
- The Full tiers hold 4,597 words against 4,902, and most Nodes are 75–100% alike word for word.
- The differences are what hand conversion adds:
  - sentences moved between Nodes,
  - linking sentences ("See … for what connects them"),
  - footnotes folded into the text,
  - equations left unnumbered,
  - the paper's typos corrected ("the variance of is input" is still there in the wrapped Work).
- Two Nodes, `covariance-stationarity` and `network-design`, have no Full tier in the wrapped Work. In the hand-converted Work they were put together from sentences scattered across the paper, and no single passage of the source matches them. Conversely, `disc-missing-piece` gains a Full tier, the paper's own paragraph, where the hand-converted Work had only a Summary.

**Suggests:** the class and the helper make the LaTeX side cheap. The mechanical step does most of the rewriting, and every place that needs a decision is marked, so none can slip through. The real cost of wrapping is not markup but authoring the graph: choosing the Node boundaries and writing about 28 Gists, 24 Summaries and 60 Edges. Here that work was reused rather than done, so this note does not measure it. Splitting `align` blocks loses the alignment of the equals signs, which reads worse in the PDF than in the original. Nodes that synthesise an idea spread across a paper cannot be wrapped, only written. The wrapped references came from the hand-converted Work; reading the paper's own `library.bib` still needs the BibTeX import helper.

## 2026-11-20 · Converting a paper straight from its PDF

**Observed:** the Thalanga paper (`works/vgp-thalanga`) was converted by a language model (Claude) from its published PDF alone, with no LaTeX source. The result is 29 Nodes, 21 Figures and 44 references, and it passes the validator. The PDF had no text layer ("Microsoft: Print To PDF"), so the model read every page as an image. Figures were extracted directly from the PDF at full quality. The model wrote the Gists, Summaries and Primers, chose how to split the paper into Nodes and declared the Edges; the Full tiers follow the paper's wording. Reading the paper this closely also surfaced inconsistencies in the paper itself: calibration described as under-coverage where the figures show over-coverage, a Cu maximum that differs between the Discussion and Table 3, and a Gaussian likelihood mentioned in the Conclusion where an ε-insensitive one was used.

**Limits:**
- **Not deterministic.** The output depends on the model, its version and the instructions it is given. Another run, or another model, could split the Nodes differently, declare different Edges, and word the Gists and Summaries differently. Unlike the planned LaTeX class (ADR 0002), this is not a conversion that can be repeated and get the same Work.
- **Needs manual validation.** The validator checks structure only: Node types, Edge rules, links, Figures and citation keys. It cannot tell whether the content is faithful. Transcribing from page images can introduce errors in numbers, equations and references, and the tiers the model writes can shift emphasis or meaning. Before a converted Work is trusted, the author or another expert must check:
  - numbers, tables and equations against the paper,
  - the reference list,
  - whether each Node split and each declared Edge matches the argument,
  - every Gist, Summary and Primer written by the model.

**Suggests:** conversion from PDF is a practical way to bring existing papers into a library (see *Libraries of Works* in [deferred.md](deferred.md)), but only as a draft, as the *Drafting by a language model* item already says. A converted Work should record that it was machine-converted and whether it has been validated, and by whom, so a Reader can tell.

## 2026-11-20 · Figures stay next to their text (author's first impression)

**Observed:** Figures always sit beside the text that refers to them, so the Reader never has to search for "Figure 7" two pages away.

**Why it happens:** this comes from the format, not the app. Figures are placed inside the Detail tier of the Node that refers to them, not where a journal's layout puts them. One Figure can appear in several Nodes, for example `fig-gold-numeric` in both `result-gold` and `disc-gold-vs-cokriging`, so each argument shows its own evidence. A PDF can print a figure only once.

**To check with colleagues:** most Gists show no Figure, and some Results only show theirs from the Summary up. Do Readers miss the Figures at the Gist level, or prefer it that way? The Figure panel offers the visuals without the text; does anyone use it?
