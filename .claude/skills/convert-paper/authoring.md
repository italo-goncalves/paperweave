# Authoring the graph

The rules for splitting a paper into Nodes and writing what the paper does not contain: Gists, Summaries, Primers and Edges. The definitions are in `GLOSSARY.md`; this is how to apply them to an existing paper. Two finished examples are worth opening before you start: `works/deep-gp-networks` (converted from LaTeX) and `works/vgp-thalanga` (from a PDF), when they exist on this machine.

## Splitting

Split by **role**, not by section. A paper's sections mix roles; a Node holds one.

- **Context**: the motivation and related work, usually from the Introduction. One Context per distinct line of argument ("the non-stationarity problem", "geostatistics versus deep learning"), not one for the whole Introduction. A related-work list in the Discussion is still Context.
- **Concept**: theory the paper relies on but did not invent, one per idea a Reader might need to look up (GP regression, the variational GP).
- **Method**: each procedure, model or component the Results use, one per piece a Reader could reuse or question on its own (each node type of a network, the training objective, the data preparation).
- **Result**: one finding a Reader would cite, with its evidence. A case study with two separate findings is two Results. The paper's own list of findings or case studies sets the `results` order in the manifest.
- **Discussion**: one argument about specific Nodes (a limitation, a justification of a choice, a comparison), discussing exactly those.
- **Conclusion**: exactly one, from the paper's conclusions.
- The roadmap paragraph ("Section 2 presents…") and the acknowledgements have no Node; list them in `review.md` as left out.

The size test: a Node is something a Reader opens on its own and understands from its Gist alone. A Full tier of one to five paragraphs is typical; a derivation can run longer. When one paragraph serves two Nodes, split it at a sentence boundary rather than copying it into both.

Some Nodes synthesise an idea the paper spreads across several places (in `deep-gp-networks`, `network-design` draws on the contributions list and two Discussion paragraphs). Such a Node gets a Gist and Summary in your words and no Full tier, since no single passage is its text; say so in `review.md`.

Mark `contribution: true` on the Nodes the paper claims as its own, taken from its list of contributions or its abstract, never from your own judgement of novelty.

## Ids and titles

Ids are kebab-case and describe the content: `result-vein`, `disc-gold-vs-cokriging`, `context-prior-work`, `primer-gp`, `sde-node`. No id starts with `eq-`. Titles are short noun phrases; a Result's title states its finding ("A folded quartz vein stays connected"), not its topic.

## Gist

One or two sentences that stand alone: a Reader who opens nothing else learns what this Node establishes or does. A Result's Gist states the finding with its key numbers ("…RMSE 1.40 vs 1.46. It takes 31.1 min to train, against 2.8 min…"). A Method's Gist says what it does and how; a Concept's says what it is. No "this section", no Notes, no Figures. Inline math and Inline links are fine.

Gists and Summaries carry the paper's **hedges** with its claims: "hard to capture" stays "hard to", not "cannot"; "increases the connectivity" gets no "much"; a number keeps its qualifier ("in log scale"); a caveat the paper attaches ("although it does not provide explicit ranges") travels with the claim; a criticism the paper makes of one cited work stays about that work, not "other works". Condensing is where overstatement creeps in, so reread each Gist against its source sentence before moving on.

## Summary

One paragraph, for the Reader who wants the mechanism and the evidence without the derivation: what, how, and why it matters, in plain sentences. It condenses this Node's own Full tier; a fact that lives in another Node's text is named with an Inline link to that Node rather than restated. It may show the Node's key Figure (`![[fig-id]]`) and link to neighbouring Nodes. Leave it out when the Full tier is itself a single short paragraph.

## Full

The paper's text, under the fidelity rule in `SKILL.md`. Check the first sentence of every Full tier: an opening that points back ("this model", "these equations", "It") lost its antecedent at the Node boundary and needs the noun named. Level-3 headings (`###`) may break up a long Full tier; take them from the paper's subsection headings where those fall inside the Node. Place each Figure (`![[fig-id]]`) in every Node that argues from it; a Figure may appear in several Nodes. Give an Equation label (`$$…$$ {#eq-name}`) to each equation the paper refers to by number, and refer to it as "Equation [[#eq-name]]".

## Primers

A Primer explains one Concept from scratch to a Reader outside the field, in a page, without referring to the Work. Write one only for a Concept that the paper's audience knows but a newcomer would not (`primer-gp` for Gaussian processes); most papers need one or two, some none. It `explains` its Concept(s). It is entirely your text, so it is the first thing a reviewer checks.

## Edges

Declare an Edge only for a genuine dependency: the source Node cannot be fully understood, or would not exist, without the target (ADR 0001). The allowed pairs are in `GLOSSARY.md` and enforced by the validator.

- `uses`: a Result or Method applies a Method.
- `relies_on`: a Result, Method or Concept builds on a Concept.
- `supports`: one Result is evidence for another.
- `explains`: a Primer to its Concept.
- `discusses`: a Discussion to each Node it argues about.
- `situates`: a Context to the Nodes it motivates, usually the contributions and the Concepts they answer.
- `synthesises`: the Conclusion to every Result.

Every Node has at least one Edge in or out. An Inline link (`[[id]]`) is navigation only; where the paper says "see Section 3", write an Inline link, and add an Edge only if the dependency is real. The validator notes Inline links with no Edge; treat each note as a question, not an instruction.
