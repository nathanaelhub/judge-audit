"""Reliability statistics for LLM judges.

Input everywhere is a mapping item_id -> list of verdicts from one judge
(True = PASS, False = FAIL, None = the judge's reply could not be parsed),
plus, where accuracy is involved, item_id -> the item's true label.

Pure functions, standard library only, so they can be checked by hand.
"""

from __future__ import annotations

import random
import statistics
from collections.abc import Callable, Mapping, Sequence
from math import comb

Votes = Mapping[str, Sequence[bool | None]]
Labels = Mapping[str, bool]


def _clean(votes: Votes) -> dict[str, list[bool]]:
    """Drop unparseable verdicts, and items left with none."""
    out = {i: [v for v in vs if v is not None] for i, vs in votes.items()}
    return {i: vs for i, vs in out.items() if vs}


def majority(vs: Sequence[bool]) -> bool | None:
    """PASS if most votes pass; None on a tie."""
    p = sum(vs)
    f = len(vs) - p
    return None if p == f else p > f


def error_rates(votes: Votes, labels: Labels) -> dict[str, float]:
    """Per-item share of votes that disagree with the label (p_i)."""
    return {i: sum(v != labels[i] for v in vs) / len(vs) for i, vs in _clean(votes).items()}


def accuracy(votes: Votes, labels: Labels) -> dict:
    """Single-vote accuracy, plus false-fail and false-pass rates.

    false_fail: share of votes on truly passing items that said FAIL (the
    failure mode that hides a good answer); false_pass: the reverse.
    """
    v = _clean(votes)
    single = [x == labels[i] for i, vs in v.items() for x in vs]
    on_pass = [not x for i, vs in v.items() if labels[i] for x in vs]
    on_fail = [x for i, vs in v.items() if not labels[i] for x in vs]
    return {
        "accuracy": sum(single) / len(single) if single else None,
        "false_fail": sum(on_pass) / len(on_pass) if on_pass else None,
        "false_pass": sum(on_fail) / len(on_fail) if on_fail else None,
        "items": len(v),
        "votes": len(single),
    }


def majority_accuracy(votes: Votes, labels: Labels, k: int) -> float | None:
    """Accuracy of a majority of the first ``k`` votes (k odd), over items with k votes."""
    if k % 2 == 0:
        raise ValueError("k must be odd so a majority always exists")
    hits = [majority(vs[:k]) == labels[i] for i, vs in _clean(votes).items() if len(vs) >= k]
    return sum(hits) / len(hits) if hits else None


def binomial_majority_error(p: float, k: int) -> float:
    """P(majority of k independent votes is wrong) when each is wrong with probability p."""
    return sum(comb(k, j) * p**j * (1 - p) ** (k - j) for j in range(k // 2 + 1, k + 1))


def error_icc(votes: Votes, labels: Labels) -> float | None:
    """How much a judge's errors are tied to the item rather than to the draw.

    Intraclass correlation of the error indicator, from per-item error
    rates: var(p_i) / (p(1 - p)) with p the overall error rate, after
    removing the sampling variance a binomial draw adds to each p_i. 0 means
    a repeat vote is an independent coin flip with the same odds; 1 means a
    repeat is a copy (the judge is wrong on the same items every time).
    """
    p_i = error_rates(votes, labels)
    v = _clean(votes)
    ns = [len(v[i]) for i in p_i]
    if len(p_i) < 2 or min(ns) < 2:
        return None
    p = sum(p_i[i] * len(v[i]) for i in p_i) / sum(ns)
    if p in (0.0, 1.0):
        return None
    observed = statistics.pvariance(list(p_i.values()))
    # E[var of p_i] from binomial noise alone: p(1-p)/n per item, averaged.
    noise = statistics.fmean(p * (1 - p) / n for n in ns)
    return max(0.0, min(1.0, (observed - noise) / (p * (1 - p) - noise))) if p * (1 - p) > noise else None


def effective_votes(k: int, icc: float) -> float:
    """Independent votes that k correlated votes are worth (Kish design effect)."""
    return k / (1 + (k - 1) * icc)


def flip_rate(votes: Votes) -> float | None:
    """Chance that two votes on the same item, drawn at random, disagree."""
    rates = []
    for vs in _clean(votes).values():
        n = len(vs)
        if n < 2:
            continue
        p = sum(vs)
        rates.append(p * (n - p) / comb(n, 2))
    return statistics.fmean(rates) if rates else None


def fleiss_kappa(votes: Votes) -> float | None:
    """Agreement among a judge's own repeated votes, beyond chance (equal counts per item)."""
    v = _clean(votes)
    n = min((len(vs) for vs in v.values()), default=0)
    if n < 2 or len(v) < 2:
        return None
    rows = [vs[:n] for vs in v.values()]
    p_pass = sum(sum(r) for r in rows) / (n * len(rows))
    pe = p_pass**2 + (1 - p_pass) ** 2
    po = statistics.fmean((sum(r) * (sum(r) - 1) + (n - sum(r)) * (n - sum(r) - 1)) / (n * (n - 1)) for r in rows)
    return None if pe == 1 else (po - pe) / (1 - pe)


def cohen_kappa(a: Mapping[str, bool | None], b: Mapping[str, bool | None]) -> float | None:
    """Agreement between two judges' per-item verdicts, beyond chance."""
    pairs = [(a[i], b[i]) for i in a.keys() & b.keys() if a[i] is not None and b[i] is not None]
    if not pairs:
        return None
    n = len(pairs)
    po = sum(x == y for x, y in pairs) / n
    pa, pb = sum(x for x, _ in pairs) / n, sum(y for _, y in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)


def invariance(votes: Votes, groups: Mapping[str, Sequence[str]]) -> dict:
    """How often a label-preserving rewrite changes a judge's verdict.

    ``groups`` maps a reference item to variants that should get the same
    verdict (paraphrases, reformatting, padding). Compares majority
    verdicts; ties are skipped.
    """
    v = _clean(votes)
    changed, total, which = 0, 0, []
    for ref, variants in groups.items():
        r = majority(v[ref]) if ref in v else None
        if r is None:
            continue
        for var in variants:
            m = majority(v[var]) if var in v else None
            if m is None:
                continue
            total += 1
            if m != r:
                changed += 1
                which.append(var)
    return {"changed": changed, "pairs": total, "rate": changed / total if total else None, "items": which}


def bootstrap_ci(stat: Callable[[list[str]], float | None], items: Sequence[str],
                 n: int = 2000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float] | None:
    """Percentile CI for ``stat`` by resampling items (votes on one item stay together)."""
    rng = random.Random(seed)
    items = list(items)
    draws = []
    for _ in range(n):
        s = stat([rng.choice(items) for _ in items])
        if s is not None:
            draws.append(s)
    if len(draws) < n // 2:
        return None
    draws.sort()
    return draws[int(alpha / 2 * len(draws))], draws[int((1 - alpha / 2) * len(draws)) - 1]


def resample(votes: Votes, labels: Labels, sample: list[str]) -> tuple[dict, dict]:
    """Votes and labels for a bootstrap sample of item ids (duplicates renamed)."""
    return ({f"{i}#{n}": votes[i] for n, i in enumerate(sample)},
            {f"{i}#{n}": labels[i] for n, i in enumerate(sample)})
