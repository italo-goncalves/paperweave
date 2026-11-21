# PaperWeave

A non-linear form of academic text: a single academic work presented as a graph of typed nodes that a reader navigates selectively, at a detail level they choose, instead of reading front to back.

## Language

### The work

**Work**:
One academic piece (paper, thesis chapter) expressed as a graph of Nodes.
_Avoid_: Document, article, paper (when meaning the graph form)

**Node**:
A self-contained unit of a Work's content, of exactly one Node type.
_Avoid_: Section, card, block

**Edge**:
A typed, declared relation pointing from the dependent Node to the Node it depends on or addresses.
_Avoid_: Link (reserved for Inline links), connection

**Abstract**:
The Work's opening overview, shown at the top of the Results list; not a Node.
_Avoid_: Summary (that is a Detail tier)

**Inline link**:
A reference to another Node inside a Node's text; used for navigation only and not an Edge.
_Avoid_: Edge, cross-reference

**Contribution**:
A marker on any Node stating that it is novel to this Work, rather than a separate Node type.
_Avoid_: Novelty node

**Figure**:
A figure or table embedded in a Node's content that can also be shown on its own; not a Node.
_Avoid_: Figure node, asset

**Equation label**:
An author-chosen name that numbers a display equation and lets other Nodes refer to it; numbers run across the Work in Paper order.
_Avoid_: Equation tag, anchor

**Note**:
A short aside attached to a point in a Node's Summary, Full tier or Primer, shown on demand when reading and listed after its Node in the Linear version; each tier has its own Notes.
_Avoid_: Footnote, endnote, sidenote

### Edge types

**uses**: Result or Method → Method.
**relies on**: Result, Method or Concept → Concept.
**supports**: Result → Result.
**explains**: Primer → Concept.
**discusses**: Discussion → any Node.
**situates**: Context → any Node.
**synthesises**: Conclusion → Result.

### Node types

**Result**:
A finding the Work establishes, including quantitative comparisons with prior work; the primary entry point for Readers.
_Avoid_: Finding, outcome, claim

**Method**:
A procedure, model or experimental setup that a Result uses.
_Avoid_: Methodology, technique

**Concept**:
Theory or a definition, explained as the Work uses it.
_Avoid_: Theory node, background

**Primer**:
A single-depth didactic explanation of a Concept that stands on its own, without reference to the Work; belongs to one Work.
_Avoid_: Tutorial, appendix, explainer

**Context**:
Material that situates the Work, such as related work or motivation; skippable unless a Result links to it.
_Avoid_: Boilerplate, background, introduction

**Discussion**:
An interpretation or justification of specific Nodes (including justifications of Method choices), linked laterally to the Nodes it argues about.
_Avoid_: Commentary, remarks

**Conclusion**:
The single Node per Work that synthesises what the Work as a whole establishes.
_Avoid_: Summary, takeaways

### Reading

**Detail tier**:
One of a Node's three levels of depth: Gist, Summary or Full.
_Avoid_: Zoom level, verbosity

**Gist**:
The required one-line Detail tier every tiered Node has.
_Avoid_: Abstract, tl;dr

**Summary**:
The optional paragraph-length Detail tier.
_Avoid_: Overview

**Full**:
The optional complete Detail tier, with derivations, tables and Figures.
_Avoid_: Details, expanded

**Reader**:
A person navigating a Work.
_Avoid_: User, viewer

**Paper order**:
The single linear order of a Work's Nodes: Context, then Concepts (each followed by its Primers), Methods, Results, Discussions and the Conclusion. Within a type, what a Node depends on comes first. A Work written in LaTeX keeps the order in which its Nodes were written, which must follow the same grouping by type.
_Avoid_: Reading order, section order, sequence

**Trail**:
The Nodes a Reader has opened in the Reading panel, kept in Paper order, each at its own Detail tier.
_Avoid_: History, breadcrumb, path

**Neighbourhood**:
The most recently opened Node together with the Nodes one Edge away from it, which the Graph map highlights while dimming the rest.
_Avoid_: Subgraph, local view

### Forms

**Work format**:
The files that hold a Work (a manifest, references, Figures and one file per Node); the hub that the other forms convert to and from.
_Avoid_: Source, export

**PaperWeave class**:
The LaTeX class in which a Work is written as a LaTeX document, converting to and from the Work format.
_Avoid_: Template, style

**Linear version**:
The PDF compiled from a LaTeX document in the PaperWeave class: a standalone linear rendering of a Work's graph, not shaped to any journal's policies.
_Avoid_: Print version, paper, manuscript

### Layout

**Panel**:
A movable, resizable, hideable region of the reading interface.
_Avoid_: Pane, window, widget

**Graph map**:
The Panel showing Nodes and Edges as a graph.
_Avoid_: Graph view, network

**Results list**:
The Panel listing a Work's Results as entry points.
_Avoid_: Index, outline

**Reading panel**:
The Panel showing Node content at the chosen Detail tier.
_Avoid_: Reading pane, viewer, content panel

**Figure panel**:
The Panel showing Figures on their own.
_Avoid_: Gallery
