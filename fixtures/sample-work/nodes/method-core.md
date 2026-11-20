---
id: method-core
type: method
title: Core method
contribution: true
edges:
  relies_on: [concept-model]
---

## Gist
Fits the model of Equation [[#eq-model]] by maximising Equation [[#eq-likelihood]].

## Summary
We maximise Equation [[#eq-likelihood]] by gradient ascent.

### Steps
- Initialise.
- Iterate until convergence.

![[fig-sample]]

| Setting | Value | Note |
|---|:---:|---:|
| Steps | 100 | fixed |
| Rate | 0.1 | **tuned** |
