---
title: "Welcome — and a quick test of math rendering"
description: "A short post to verify LaTeX, code, and links work as expected."
pubDate: 2026-05-22
tags: ["meta"]
---

This is the first post on the new site. I'll mostly use this space for shorter notes
on AI safety and economics — things that don't quite fit the longer Substack format.

## Inline and display math

Inline math like $\beta = 0.85$ and $\sum_{i=1}^n x_i$ should render via KaTeX.

Display math:

$$
\mathcal{L}(\theta) = \mathbb{E}_{\tau \sim \pi_\theta} \left[ r(\tau) \right]
- \lambda \cdot \mathrm{KL}\!\left( \pi_\theta \,\|\, \pi_{\mathrm{ref}} \right)
$$

A multi-line aligned equation:

$$
\begin{aligned}
y_t &= \alpha + \beta x_t + \varepsilon_t \\
\varepsilon_t &\sim \mathcal{N}(0, \sigma^2)
\end{aligned}
$$

## Code

```python
def reward(trajectory):
    return sum(r for _, _, r in trajectory)
```

## Links and emphasis

A reference to [Acemoglu and Restrepo (2024)](https://example.com), some *italics*,
and **bold** text — note the serif treats these gracefully.

> Block quotes look like this, slightly indented and muted.

That's it for the test post. Replace this with real content.
