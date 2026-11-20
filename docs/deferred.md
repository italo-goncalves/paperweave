# Deferred

Ideas deliberately left out of the reading prototype, to revisit once reading is shown to work.

- **Review infrastructure**: peer review attached to a Work, including crowd review and review assisted by a language model. This includes marking Nodes (often Discussions) that were added in response to review rounds, for example using a paper's response-to-reviewers letter.
- **Linear export**: producing a conventional linear paper from a Work, which needs a defined reading order.
- **Shared Primers**: a library of Primers reused across Works. Primer IDs are kept stable so they can be moved later.
- **Drafting by a language model**: generating a first draft of Nodes from a PDF or LaTeX source for a human to correct. Under ADR 0001, any such draft must produce declared Edges.
- **LaTeX class for Works**: a LaTeX class in which authors mark up Nodes, Detail tiers and Edges directly, so a paper converts to the Work format automatically and deterministically, with no hand conversion and no language model in the loop.
- **Agent integration for translation and explanation**: an agent that translates a Work on demand or explains a Node to the Reader, for example rephrasing it at a different level or answering questions about it. Its output is unofficial and must be marked as such.
- **Official translations**: translations of a Work approved by its author, with the language chosen from a menu in the app. They are kept apart from agent translations, so the Reader can always tell an approved text from a generated one.
