"""
MMD (Maximum Mean Discrepancy) - comparison/ablation metric ONLY, per
DSSA_IMPLEMENTATION_FREEZE.md Sec 6: "Metrics: cosine distance and MMD only
... The primary metric remains cosine. MMD is a comparison/ablation only."

Biased RBF-kernel MMD^2 estimator (always non-negative, unlike the unbiased
estimator - appropriate for a diagnostic/comparison run, not a claim about
which estimator is "the" frozen choice, since CKA/MMD/cosine were left as
candidates in the original abstract and cosine was frozen as primary).
Bandwidth: median heuristic over the combined sample, a standard, documented
default - not tuned or chosen to produce any particular result.
"""
from __future__ import annotations

import torch


def median_heuristic_bandwidth(x: torch.Tensor, y: torch.Tensor) -> float:
    combined = torch.cat([x, y], dim=0)
    d = torch.cdist(combined, combined, p=2)
    n = d.shape[0]
    off_diag = d[~torch.eye(n, dtype=torch.bool)]
    med = off_diag.median().item()
    return max(med, 1e-6)


def mmd2_biased(x: torch.Tensor, y: torch.Tensor, bandwidth: float | None = None) -> float:
    """x: (N_x, D), y: (N_y, D). Returns scalar biased MMD^2 estimate with an RBF kernel."""
    if bandwidth is None:
        bandwidth = median_heuristic_bandwidth(x, y)
    gamma = 1.0 / (2 * bandwidth ** 2)

    def rbf(a, b):
        d2 = torch.cdist(a, b, p=2) ** 2
        return torch.exp(-gamma * d2)

    kxx = rbf(x, x).mean()
    kyy = rbf(y, y).mean()
    kxy = rbf(x, y).mean()
    return (kxx + kyy - 2 * kxy).item()
