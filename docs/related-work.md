# Related work

Projects close to PaperWeave, and how they differ. None found so far combines all three of its parts: a graph of one Work's Results, Methods and Concepts as the reading experience itself; Detail tiers the Reader adjusts per Node; and Context the Reader can skip.

## Graph-shaped claims and evidence

- **Discourse graphs** (Joel Chan, Protocol Labs): notes typed as Question, Claim or Evidence, linked by supports and opposes edges. The closest match to a Result tied to its evidence, but built for a researcher's own notes across many papers, not for reading one Work. [blog](https://research.protocol.ai/blog/2023/discourse-graphs-and-the-future-of-science/)
- **Micropublications** (Clark, Ciccarese and Goble, 2014): a formal model of claims, evidence and arguments, attached to an existing article as separate metadata. [arXiv](https://arxiv.org/pdf/1305.3506)
- **Nanopublications and Nanoarguments**: single assertions with their provenance, joined into a shared network across sites. Each unit is smaller than a PaperWeave Node. [registry](https://registry.knowledgepixels.com/np/RAs2LsC60TPCz-hrWXbmoS0F9nt_dgWF7hyPOZWyHer60.xml.txt)
- **Claim graphs in biochemistry** (ArgMining 2020): found that the evidence for a claim is often another claim, which supports letting Results support other Results. [ACL](https://aclanthology.org/2020.argmining-1.10)
- **Argument as a queryable graph** (2026): proposes a claim registry linking each claim to its figures, numbers and code. [arXiv](https://arxiv.org/pdf/2603.23526)

## Reading interfaces

- **GraphMind** (2025): its Paper Structured Graph links claims to methods to experiments, and clicking a node shows the matching passage of the paper. Built for judging novelty, not for reading, but its interaction is close to the Graph map's. [arXiv](https://arxiv.org/pdf/2510.15706)
- **TextFold, formerly PaperFold**: an open-source, local-first reader that lets the Reader "zoom" any text through five folding levels. It reads the HTML versions of arXiv, PubMed Central, bioRxiv and medRxiv papers, Wikipedia articles and Markdown files, and needs a connected language model to produce the levels. It is the closest existing match to Detail tiers. The difference: its levels are generated from a linear text, while a Work's tiers are written or approved by the author and sit on a graph of typed Nodes (compare the roadmap items on drafting and on agent explanations in [deferred.md](deferred.md)). Known only from third-party directory entries ([PaperFold](https://aiindigo.com/tool/paperfold), [TextFold](https://aiindigo.com/tool/textfold)); the rename, the Apache-2.0 licence and the details above are not yet checked against its own repository.
- **ScholarPhi, now Semantic Reader** (UC Berkeley, Allen Institute for AI): shows definitions of terms and symbols where they appear, and has a "declutter" mode that dims passages unrelated to a chosen term. Readers answered faster with it in a lab study. It adds aids on top of a linear PDF. [Berkeley](https://www.ischool.berkeley.edu/news/2021/scholarphi-novel-interface-reading-scientific-papers), [CACM](https://cacm.acm.org/research/the-semantic-reader-project)
- **Living Papers** (University of Washington): an open-source toolkit for interactive web articles, with reading aids such as enhanced citations, cross-references and interactive equations. A possible base to build on. [site](https://idl.uw.edu/living-papers-paper/living-papers)
- **Stretchtext** (Ted Nelson, 1960s): text that expands in place to more or less detail, the original idea behind Detail tiers.

## Publishing platforms

- **Octopus** (UK): splits research into eight linked publication types, such as problem, hypothesis, methods, results and analysis. Its known weak spot is who stitches the pieces back into a story, the same open question as a Reading order for linear export. [UKSG](https://www.uksg.org/?p=4578)

## Where PaperWeave stands

These projects either model a paper's argument for machines (micropublications, nanopublications), add aids on top of a linear text (ScholarPhi, TextFold), or split research into separate publications (Octopus). PaperWeave treats the graph of one Work as the reading experience itself, with Detail tiers that the author controls.
