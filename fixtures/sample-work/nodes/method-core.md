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
We maximise Equation [[#eq-likelihood]] by gradient ascent.[^1]

### Steps
- Initialise.
- Iterate until convergence.

![[fig-sample]]

| Setting | Value | Note |
|---|:---:|---:|
| Steps | 100 | fixed |
| Rate | 0.1 | **tuned**[^2] |

[^1]: Any optimiser with $\nabla \ell$ works; see @Doe2019 and [[concept-model]].
[^2]: Tuned by hand.
