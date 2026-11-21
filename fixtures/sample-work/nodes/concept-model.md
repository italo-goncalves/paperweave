---
id: concept-model
type: concept
title: The $\boldsymbol\Sigma$ model
---

## Gist
A model whose covariance is $\boldsymbol\Sigma$.

## Summary
The model is defined by

$$
y = f(x) + \varepsilon
$$ {#eq-model}

and nothing else.

## Full
The model is defined by

$$
y = f(x) + \varepsilon
$$ {#eq-model}

with noise $\varepsilon$.[^1] Its likelihood is

$$\log p(y) = -\tfrac{1}{2} y^\top \boldsymbol\Sigma^{-1} y + c$$ {#eq-likelihood}

and an unnumbered identity

$$
a = a
$$

[^1]: The noise is *independent* of $x$.
