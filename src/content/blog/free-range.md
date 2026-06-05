---
title: "A quick economic model of humane meat consumption"
description: "A framework to think about when a vegan might eat humane meat instead."
pubDate: 2026-06-05
draft: true
---

---
title: "Should vegans eat humane meat?"
description: "A quick economic model on whether marginal humane-meat demand from a vegan increases or decreases total animal welfare."
pubDate: 2026-06-05
draft: false
tags: ["economics", "animal-welfare"]
---

Humam Aziz asks, "Does eating free-range products increase animal welfare, or does it drive prices up for humane animal products, leaving consumers (who are highly elastic) to switch towards cheaper, higher-suffering animal products?" This is a non-issue for meat-eaters. Eating more-humane animal products is still better, because the most the price increase can do (assuming the supply curve isn't downward-sloping) is *offset* some of the switch. The question of whether a vegan should consider eating humane meat is a bit more complicated, but I'm skeptical. I thought I'd write up a quick economic model to think about this more clearly.

## Set-up

Suppose there are two retail markets, one for higher-welfare meat (indexed by $H$) and one for lower-welfare meat (indexed by $L$). Let $P_H$ and $P_L$ denote prices and $Q_H$ and $Q_L$ denote quantities. For simplicity, I assume that demand and supply are linear in prices, with common own-price slopes $\beta > 0$ in demand and $\epsilon > 0$ in supply, and with common cross-price slopes $\gamma \geq 0$ in demand and $\phi \geq 0$ in supply. Higher-welfare meat is costlier to produce, so we have a per-unit "wedge" $c \geq 0$; producers therefore respond to the net margin $P_H - c$ when making this allocation decision. The constants $\alpha_H$, $\alpha_L$, and $\delta$ are intercepts. Hence, the system of equations is

$$
\begin{aligned}
Q_H^d &= \alpha_H - \beta P_H + \gamma P_L, \\
Q_L^d &= \alpha_L - \beta P_L + \gamma P_H, \\
Q_H^s &= -\delta + \epsilon(P_H - c) - \phi P_L, \\
Q_L^s &= -\delta + \epsilon P_L - \phi(P_H - c).
\end{aligned}
$$

I'll assume $\beta + \epsilon > \gamma + \phi$, which ensures that own-market price responses dominate cross-market substitution (I'll call this "own-market dominance"); this ensures that the system of equations has a positive determinant.

Let $w_H$ and $w_L$ denote per-animal welfare in higher-welfare and lower-welfare production respectively. I assume that both are negative, but that lower-welfare conditions are strictly worse, so $w_L < w_H < 0$. Total animal welfare is given by $W = w_H Q_H + w_L Q_L$. Define the welfare ratio $r \equiv |w_L|/|w_H| > 1$, which measures how much worse lower-welfare conditions are per animal than higher-welfare conditions. Without loss of generality, we can set $w_H = -1$ and $w_L = -r$.

## Comparative statics

The market-clearing conditions $Q_H^d = Q_H^s$ and $Q_L^d = Q_L^s$ can be rearranged to

$$
\begin{aligned}
(\beta + \epsilon) P_H - (\gamma + \phi) P_L &= \alpha_H + \delta + \epsilon c, \\
(\beta + \epsilon) P_L - (\gamma + \phi) P_H &= \alpha_L + \delta - \phi c.
\end{aligned}
$$

Consider a vegan deciding to eat a unit of higher-welfare meat, i.e., a unit upward shift in demand for higher-welfare meat, modeled as $\Delta \alpha_H = 1$ with $\alpha_L$ and $c$ held fixed. Differentiating the system of equations gives

$$
\begin{aligned}
1 &= (\beta + \epsilon)\, \Delta P_H - (\gamma + \phi)\, \Delta P_L, \\
0 &= (\beta + \epsilon)\, \Delta P_L - (\gamma + \phi)\, \Delta P_H.
\end{aligned}
$$

Defining $D \equiv (\beta+\epsilon)^2 - (\gamma+\phi)^2$, which is strictly positive thanks to the assumption that $\beta + \epsilon > \gamma + \phi$, the price changes are

$$
\Delta P_H = \frac{\beta + \epsilon}{D}, \qquad \Delta P_L = \frac{\gamma + \phi}{D}.
$$

Substituting these into the supply equations, we have

$$
\begin{aligned}
\Delta Q_H &= \epsilon\, \Delta P_H - \phi\, \Delta P_L = \frac{\epsilon\beta + \epsilon^2 - \phi\gamma - \phi^2}{D}, \\
\Delta Q_L &= \epsilon\, \Delta P_L - \phi\, \Delta P_H = \frac{\epsilon\gamma - \phi\beta}{D}.
\end{aligned}
$$

## The animal welfare condition

The change in total animal welfare induced by the marginal demand shift is

$$
\Delta W = w_H\, \Delta Q_H + w_L\, \Delta Q_L = -\Delta Q_H - r\, \Delta Q_L.
$$

Substituting the above expressions, we get

$$
\Delta W = -\,\frac{(\epsilon\beta + \epsilon^2 - \phi\gamma - \phi^2) - r\,(\phi\beta - \epsilon\gamma)}{D}.
$$

Since $D > 0$, the sign of $\Delta W$ is determined by the sign of the numerator. Hence, the marginal demand shift (by the once-vegan) toward higher-welfare meat strictly increases total animal welfare if and only if

$$
(\epsilon\beta + \epsilon^2 - \phi\gamma - \phi^2) - r\,(\phi\beta - \epsilon\gamma) < 0.
$$

Thus, when $\phi\beta > \epsilon\gamma$, the marginal higher-welfare demand increase increases total animal welfare if and only if

$$
r > \frac{\epsilon\beta + \epsilon^2 - \phi\gamma - \phi^2}{\phi\beta - \epsilon\gamma}.
$$

Meanwhile, when $\phi\beta < \epsilon\gamma$, dividing by $\phi\beta - \epsilon\gamma < 0$ reverses the inequality, so the welfare condition becomes

$$
r < \frac{\epsilon\beta + \epsilon^2 - \phi\gamma - \phi^2}{\phi\beta - \epsilon\gamma}.
$$

But this cannot hold for any $r > 1$: combining $\phi\beta < \epsilon\gamma$ with own-market dominance forces $\epsilon > \phi$ (otherwise $\phi\beta < \epsilon\gamma \leq \phi\gamma$ would give $\beta < \gamma$, contradicting $\beta + \epsilon > \gamma + \phi$), hence $\epsilon(\beta+\epsilon) > \phi(\beta+\epsilon) > \phi(\gamma+\phi)$; the numerator is therefore positive while the denominator is negative, so the right-hand side is negative.

Hence, the two conditions that must *both* be met for this marginal demand increase to be welfare positive are

$$
\boxed{
\begin{gathered}
\phi\beta > \epsilon\gamma, \\[0.5em]
r > \frac{\epsilon\beta + \epsilon^2 - \phi\gamma - \phi^2}{\phi\beta - \epsilon\gamma}.
\end{gathered}
}
$$

Since $\Delta Q_L = (\epsilon\gamma - \phi\beta)/D$, the condition $\phi\beta > \epsilon\gamma$ is exactly the requirement that the demand shift causes lower-welfare output to fall ($\Delta Q_L < 0$). Without it, the marginal vegan adds animals to the system on net. With it, supply-side substitution actually pulls some animals out of the worse system and into the better one. The second condition then asks that the welfare ratio $r$ be large enough that the welfare gained from those displaced lower-welfare animals outweighs the welfare cost of the additional higher-welfare animals brought into existence ($\Delta Q_H > 0$, the normal own-market response).

In practice, I'd guess these conditions are hard to meet, but I'm not certain.

