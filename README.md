# PaperWeave

A prototype of non-linear academic text: a Work is a graph of typed Nodes that a Reader navigates selectively, at a Detail tier they choose. Vocabulary is in [GLOSSARY.md](GLOSSARY.md), the file format in [docs/work-format.md](docs/work-format.md), decisions in [docs/adr/](docs/adr/), and similar projects in [docs/related-work.md](docs/related-work.md).

## Run

```bash
npm install
npm run dev
```

Then open http://localhost:5173. Every Work under `works/` is bundled in; pick one from the menu in the top bar, or open `?work=<id>` directly. `works/` is not versioned (see `.gitignore`), so a fresh clone has no Work to show until you add one.

Check a Work after editing its files:

```bash
python -P scripts/validate_work.py works/deep-gp-networks
```

## Reading

- **Results list**: the Abstract, the Results in the author's order, and the Conclusion. Clicking an entry starts a new Trail. "Browse every Node" lists the whole Work by type.
- **Reading panel**: the Trail, kept in Paper order (Context, Concepts with their Primers, Methods, Results, Discussions, Conclusion; see ADR 0003): a Node you open (from an Inline link, an Edge chip or the Graph map) lands where it sits in the Work, so dependencies appear above what uses them and Discussions below what they discuss. Each Node has G/S/F buttons to set its own Detail tier; clicking the selected one again returns it to the global tier in the top bar.
- **Graph map**: the whole Work in a fixed layered layout, top to bottom from Context to the Conclusion, with Results sharing one band. The layout is computed once (crossings are reduced but not always zero) and never moves while you read. Opening a Node highlights its Neighbourhood (the Node and everything one Edge away) and dims the rest; Trail Nodes are outlined.
- **Figure panel**: the Figures of the Nodes in the Trail, or every Figure in the Work. Click an image to enlarge it.

Panels can be dragged by their header between the three columns, resized with the gaps between them, and hidden. The layout is saved in this browser only.
