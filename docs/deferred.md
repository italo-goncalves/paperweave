# Deferred

Ideas deliberately left out of the reading prototype, to revisit once reading is shown to work.

- **Review infrastructure**: peer review attached to a Work, including crowd review and review assisted by a language model. This includes marking Nodes (often Discussions) that were added in response to review rounds, for example using a paper's response-to-reviewers letter.
- **Linear export**: producing a conventional linear paper from a Work, which needs a defined reading order.
- **Shared Primers**: a library of Primers reused across Works. Primer IDs are kept stable so they can be moved later.
- **Drafting by a language model**: generating a first draft of Nodes from a PDF or LaTeX source for a human to correct. Under ADR 0001, any such draft must produce declared Edges.
- **LaTeX class for Works**: a LaTeX class in which authors mark up Nodes, Detail tiers and Edges directly. Conversion runs both ways, automatically and deterministically, with no hand conversion and no language model in the loop: LaTeX to the Work format, and any Work back to LaTeX in this class. See *Interchangeable forms* below. Design so far:
  - One environment per Node type (`\begin{result}[contribution]{id}{Title}`), with Edges as commands at its top (`\uses{…}`), `\gist{…}`, and `summary` and `full` environments. Primers live in their own files (`primers/<id>.tex`), pulled in with `\primer{id}`.
  - Node bodies accept only the inverse of the Markdown body syntax (emphasis, lists, `\subsection*`, `tabular`, `\href`, `\nodelink`, `\showfigure`, `\citep` and `\citet`, math verbatim); anything else is an error with its line number.
  - References come from a `.bib` file formatted by `paperweave.bst` (ADR 0004). Nodes appear in Paper order, and the written order is kept (ADR 0003).
  - It compiles to the Linear version: a standalone PDF, not shaped to any journal. Class options pick the Detail tier to print (`tier=gist|summary|full`) and can leave Primers out (`noprimers`); each Node shows its type, title, Gist and a line of linked Edges.
  - It serves both writing new Works and wrapping existing papers by hand, and wrapping should stay cheap.
- **Agent integration for translation and explanation**: an agent that translates a Work on demand or explains a Node to the Reader, for example rephrasing it at a different level or answering questions about it. Its output is unofficial and must be marked as such.
- **Official translations**: translations of a Work approved by its author, with the language chosen from a menu in the app. They are kept apart from agent translations, so the Reader can always tell an approved text from a generated one.
- **Writing a Work in the app**: authoring tools inside PaperWeave, so an author can create Nodes, write each Detail tier, declare Edges and place Figures without editing files by hand. The tools would check the Work as it is written (the rules in `tools/validate_work.py`), show the Graph map updating live, and preview each Node as a Reader will see it. The app reads and writes the Work format, so a Work started in the app can be continued in files or in LaTeX, and the other way round. See *Interchangeable forms* below.
- **Citations between Works**: a Work can cite another Work, or a single Node in it, such as one Result or Method, rather than only a whole paper. A Reader following the citation opens the cited Node at a Detail tier of their choice, without leaving PaperWeave. Conventional references (`references.yaml`) remain for works outside PaperWeave. Open questions: whether a citation of another Work's Node is a typed Edge (ADR 0001) that the Graph map can show, and how a citation stays valid when the cited Work is revised, which needs stable Node IDs and versioned Works.
- **Libraries of Works**: a collection of Works read and searched together, for example an institution's internal knowledge base or a researcher's personal library. A library would offer search across its Works, Concepts and Methods shared between Works, and a map of citations between them. Shared Primers (above) become one part of this. This is the likeliest route to adoption: launching PaperWeave as a new publishing standard is hard, but a library is useful to one group or one person as soon as their existing works can be converted, which makes the LaTeX class and drafting by a language model the prerequisites.

## Interchangeable forms

Decided in [ADR 0002](adr/0002-work-format-is-the-hub-for-interchangeable-forms.md).

A Work has three forms: the Work format (the files under `works/`, described in [work-format.md](work-format.md)), a LaTeX document in the PaperWeave class, and the editor in the app. All three must be interchangeable: an author can move a Work between any two of them, in either direction, at any point, and converting it out and back gives the same Work.

- **The Work format is the hub.** The app edits it directly, and LaTeX converts to and from it. There is no direct LaTeX-to-app path to keep in step.
- **Nothing exists in only one form.** Anything an author can express in the LaTeX class or in the app must have a place in the Work format, and anything in the Work format must be writable in both. When a feature is added to one form, it is added to the other two in the same change.
- **Round trips are tested.** For each sample Work, converting Work → LaTeX → Work and loading and saving it in the app must both reproduce the original files.
- **Open question: free LaTeX.** Arbitrary LaTeX (custom macros, packages, layout commands) cannot all be carried into the Work format. The class will need to allow a defined subset and reject or flag the rest, rather than silently dropping it.
