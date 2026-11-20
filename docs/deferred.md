# Deferred

Ideas deliberately left out of the reading prototype, to revisit once reading is shown to work.

- **Review infrastructure**: peer review attached to a Work, including crowd review and review assisted by a language model. This includes marking Nodes (often Discussions) that were added in response to review rounds, for example using a paper's response-to-reviewers letter.
- **Linear export**: producing a conventional linear paper from a Work, which needs a defined reading order.
- **Shared Primers**: a library of Primers reused across Works. Primer IDs are kept stable so they can be moved later.
- **Drafting by a language model**: generating a first draft of Nodes from a PDF or LaTeX source for a human to correct. Under ADR 0001, any such draft must produce declared Edges.
- **LaTeX class for Works**: a LaTeX class in which authors mark up Nodes, Detail tiers and Edges directly. Conversion runs both ways, automatically and deterministically, with no hand conversion and no language model in the loop: LaTeX to the Work format, and any Work back to LaTeX in this class. See *Interchangeable forms* below.
- **Agent integration for translation and explanation**: an agent that translates a Work on demand or explains a Node to the Reader, for example rephrasing it at a different level or answering questions about it. Its output is unofficial and must be marked as such.
- **Official translations**: translations of a Work approved by its author, with the language chosen from a menu in the app. They are kept apart from agent translations, so the Reader can always tell an approved text from a generated one.
- **Writing a Work in the app**: authoring tools inside PaperWeave, so an author can create Nodes, write each Detail tier, declare Edges and place Figures without editing files by hand. The tools would check the Work as it is written (the rules in `tools/validate_work.py`), show the Graph map updating live, and preview each Node as a Reader will see it. The app reads and writes the Work format, so a Work started in the app can be continued in files or in LaTeX, and the other way round. See *Interchangeable forms* below.

## Interchangeable forms

Decided in [ADR 0002](adr/0002-work-format-is-the-hub-for-interchangeable-forms.md).

A Work has three forms: the Work format (the files under `works/`, described in [work-format.md](work-format.md)), a LaTeX document in the PaperWeave class, and the editor in the app. All three must be interchangeable: an author can move a Work between any two of them, in either direction, at any point, and converting it out and back gives the same Work.

- **The Work format is the hub.** The app edits it directly, and LaTeX converts to and from it. There is no direct LaTeX-to-app path to keep in step.
- **Nothing exists in only one form.** Anything an author can express in the LaTeX class or in the app must have a place in the Work format, and anything in the Work format must be writable in both. When a feature is added to one form, it is added to the other two in the same change.
- **Round trips are tested.** For each sample Work, converting Work → LaTeX → Work and loading and saving it in the app must both reproduce the original files.
- **Open question: free LaTeX.** Arbitrary LaTeX (custom macros, packages, layout commands) cannot all be carried into the Work format. The class will need to allow a defined subset and reject or flag the rest, rather than silently dropping it.
