# One Paper order for every form of a Work

A Work needs a linear order in three places: the Trail in the Reading panel, the `.tex` file written by Work → LaTeX, and the Linear version compiled from it. Until now the app derived a Reading order from the Edges, layer by layer, and that order branches. We decided on a single total order, the Paper order, used everywhere: Context, then Concepts (each followed by the Primers that explain it), Methods, Results, Discussions and the Conclusion. Within a type, Edges put what a Node depends on first. Remaining ties go by the Results list order for Results, by first use for Methods and Concepts, by the earliest Node situated or discussed for Contexts and Discussions, and finally by Node id. A Work written in LaTeX keeps the order in which its Nodes were written, stored in an optional `order:` list in `manifest.yaml`; that order must follow the same grouping by type, and the class reports an error at compile time when it does not.

## Considered options

- **Keep the branching Reading order derived from Edges** and linearise it only for export. Rejected: the app, the files and the Linear version would each show the Work in a different order.
- **Store no order at all**, always computing it. Rejected: an author writing in LaTeX chooses an order within each type, and Work → LaTeX → Work would lose it.
- **Allow any written order in LaTeX.** Rejected: a stored order could then contradict the grouping by type, giving two notions of order instead of one.

## Consequences

- The Graph map keeps its layered layout. That is a layout, not an order, and it no longer defines the Trail.
- Work → LaTeX writes Nodes in `order` when it is present and in the computed Paper order otherwise. LaTeX → Work always writes `order`.
- A Work written in files or in the app has no `order` unless its author adds one; the validator checks that any `order` lists every Node once and follows the grouping by type.
