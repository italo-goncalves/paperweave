# Edges are declared in a Node's header; Inline links are not Edges

A Work's graph needs typed Edges (uses, relies on, supports, explains, discusses, situates, synthesises), but authors also mention other Nodes in passing inside the text. We decided that Edges are declared explicitly in each Node's header, and that Inline links in the text are for navigation only and never create Edges. Deriving Edges from Inline links would save authoring effort, but every passing mention would become a dependency and clutter the Graph map. Inline links also carry no type. The Graph map and the Trail are only useful if each Edge means "this Node genuinely depends on that one."

## Consequences

- A Node can have an Inline link to another Node with no Edge between them, and the reverse, so the two can drift apart. A validation step can flag Inline links that have no matching Edge as candidates for review, but it never adds an Edge automatically.
- Any future step that converts or imports content (pasted LaTeX, Word, Markdown, or drafts from a language model) must produce declared Edges, not rely on cross-references in the text.
