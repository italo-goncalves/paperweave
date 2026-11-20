# The Work format is the hub; the LaTeX class and the app editor convert to and from it without loss

A Work will be writable in three forms: the Work format (the files under `works/`, see [work-format.md](../work-format.md)), a LaTeX document in the PaperWeave class, and the editor in the app. Authors must be able to move a Work between any two of these, in either direction, at any point, and get back exactly what they started with. We decided that the Work format is the single hub: the app reads and writes it directly, and LaTeX converts to and from it deterministically, with no language model involved. There is no direct path between LaTeX and the app. A hub keeps the number of converters at two instead of three pairs, makes the Work format the one place where the meaning of a Work is defined, and keeps it readable and diffable as plain files.

## Considered options

- **LaTeX as the source**, with the Work format generated from it. Rejected: authors who don't use LaTeX, and the app, would depend on a LaTeX toolchain, and anything the app can express would have to be invented in LaTeX first.
- **One-way conversion into the Work format** (the earlier roadmap item). Rejected: an author who edits in the app could never return to LaTeX, which forces a final choice of form at the start.

## Consequences

- Nothing exists in only one form. Anything the LaTeX class or the app can express must have a place in the Work format, and anything in the Work format must be writable in both. A feature added to one form is added to the other two in the same change.
- Round trips are tested: for each sample Work, Work → LaTeX → Work and loading and saving in the app must both reproduce the original files byte for byte. The Work format therefore needs a canonical serialisation (key order, line wrapping, whitespace), or the tests compare parsed content instead.
- The LaTeX class accepts only a defined subset of LaTeX. Custom macros, packages and layout commands outside it are rejected or flagged, never silently dropped.
- Conversion carries declared Edges as Edges (ADR 0001); a LaTeX `\ref` or an Inline link never becomes one.
