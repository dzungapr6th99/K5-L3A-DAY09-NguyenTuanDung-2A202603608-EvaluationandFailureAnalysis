"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    # TODO M2
    if len(human) != len(judge):
        raise ValueError("human and judge must be the same length")
    result = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for h, j in zip(human, judge):
        if h == POS and j == POS:
            result["tp"] += 1
        elif h != POS and j == POS:
            result["fp"] += 1
        elif h == POS and j != POS:
            result["fn"] += 1
        elif h != POS and j != POS:
            result["tn"] += 1
    return result


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    # TODO M2: precision = tp/(tp+fp), recall = tp/(tp+fn); return 0.0 when the denominator is 0
    conf = confusion(human, judge)
    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    # TODO M2
    cm = confusion(human, judge)
    n = len(human)
    if n == 0:
        raise ValueError("human and judge must not be empty")
    p_o = (cm["tp"] + cm["tn"]) / n
    human_fail = (cm["tp"] + cm["fn"]) / n
    judge_fail = (cm["tp"] + cm["fp"]) / n

    p_e = human_fail * judge_fail + (1 - human_fail) * (1 - judge_fail)
    if p_e == 1:
        raise ValueError("Cohen's kappa is undefined when p_e == 1")
    return (p_o - p_e) / (1 - p_e)
    


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    # TODO M2: (p_obs + spec - 1) / (sens + spec - 1)
    demominator = sensitivity + specificity - 1
    if demominator == 0:
        raise ValueError("Sensitivity and specificity cannot both be 0.5")
    corrected_rate = (observed_rate + specificity - 1) / demominator
    return max(0.0, min(1.0, corrected_rate))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    # TODO M4
    import numpy as np
    from scipy.stats import bootstrap
    if len(a) != len(b):
        raise ValueError("a and b must be the same length")
    if len(a) == 0:
        raise ValueError("a and b must not be empty")
    a_array = np.asarray(a, dtype=float)
    b_array = np.asarray(b, dtype=float)
    if np.array_equal(a_array, b_array):
        return 0.0, 0.0, 0.0
    def mean_difference(x, y, axis=-1):
        return np.mean(x, axis=axis) - np.mean(y, axis=axis)

    result = bootstrap(
        data=(a_array, b_array),
        statistic=mean_difference,
        paired=True,
        vectorized=True,
        n_resamples=n_resamples,
        confidence_level=confidence,
        method="percentile",
        rng=np.random.default_rng(rng),
    )

    difference = mean_difference(a_array, b_array)
    return (
        float(difference),
        float(result.confidence_interval.low),
        float(result.confidence_interval.high),
    )
        


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    from math import comb

    if not (0 <= c <= n and 1 <= k <= n):
        raise ValueError("Require 0 <= c <= n and 1 <= k <= n")
    return 1 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    from math import comb

    if not (0 <= c <= n and 1 <= k <= n):
        raise ValueError("Require 0 <= c <= n and 1 <= k <= n")
    return comb(c, k) / comb(n, k)
