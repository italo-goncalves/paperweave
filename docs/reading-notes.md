# Reading notes

Observations from using the reading prototype, gathered to judge whether reading a Work as a graph beats reading the PDF. Newest first. Record what was seen, who saw it, and what it suggests; keep fixes and decisions in their own places.

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
