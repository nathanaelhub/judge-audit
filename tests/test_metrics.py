import random

import pytest

from judge_audit import metrics as m

T, F = True, False


def test_majority_and_ties():
    assert m.majority([T, T, F]) is True
    assert m.majority([F, F, T]) is False
    assert m.majority([T, F]) is None


def test_accuracy_splits_false_fail_and_false_pass():
    labels = {"good": T, "bad": F}
    votes = {"good": [T, T, F, F], "bad": [F, F, F, T]}
    a = m.accuracy(votes, labels)
    assert a["accuracy"] == pytest.approx(5 / 8)
    assert a["false_fail"] == pytest.approx(0.5)
    assert a["false_pass"] == pytest.approx(0.25)


def test_unparseable_votes_are_dropped_not_counted_wrong():
    a = m.accuracy({"x": [T, None, T]}, {"x": T})
    assert a["accuracy"] == 1 and a["votes"] == 2


def test_binomial_majority_error_matches_hand_calculation():
    # 3 votes, each wrong with p = 0.2: 3(0.2^2)(0.8) + 0.2^3 = 0.104
    assert m.binomial_majority_error(0.2, 3) == pytest.approx(0.104)
    assert m.binomial_majority_error(0.2, 1) == pytest.approx(0.2)


def test_copied_votes_have_icc_one_and_count_as_one_vote():
    # Wrong on the same 20% of items every time: repeats add nothing.
    labels = {f"i{n}": T for n in range(50)}
    votes = {i: [n >= 10] * 5 for n, i in enumerate(labels)}
    icc = m.error_icc(votes, labels)
    assert icc == pytest.approx(1.0)
    assert m.effective_votes(5, icc) == pytest.approx(1.0)
    assert m.majority_accuracy(votes, labels, 5) == pytest.approx(m.accuracy(votes, labels)["accuracy"])


def test_independent_votes_have_icc_near_zero_and_majority_helps():
    rng = random.Random(1)
    labels = {f"i{n}": T for n in range(2000)}
    votes = {i: [rng.random() > 0.2 for _ in range(5)] for i in labels}
    icc = m.error_icc(votes, labels)
    assert icc < 0.05
    assert m.effective_votes(5, icc) > 4
    # Majority of 3 should land near the binomial prediction (0.104 error).
    assert 1 - m.majority_accuracy(votes, labels, 3) == pytest.approx(0.104, abs=0.02)


def test_icc_undefined_without_errors_or_repeats():
    assert m.error_icc({"a": [T, T], "b": [T, T]}, {"a": T, "b": T}) is None
    assert m.error_icc({"a": [F], "b": [T]}, {"a": T, "b": T}) is None


def test_flip_rate():
    # [T, T, F]: 2 of the 3 pairs disagree; [T, T, T]: none.
    assert m.flip_rate({"a": [T, T, F], "b": [T, T, T]}) == pytest.approx(1 / 3)


def test_fleiss_kappa_perfect_and_chance():
    assert m.fleiss_kappa({"a": [T] * 3, "b": [F] * 3}) == pytest.approx(1.0)
    # Every item split the same way: agreement is below chance.
    assert m.fleiss_kappa({"a": [T, F], "b": [T, F]}) < 0


def test_cohen_kappa_hand_example():
    a = {"1": T, "2": T, "3": F, "4": F}
    b = {"1": T, "2": F, "3": F, "4": F}
    # po = 0.75, pe = 0.5*0.25 + 0.5*0.75 = 0.5 -> kappa 0.5
    assert m.cohen_kappa(a, b) == pytest.approx(0.5)


def test_invariance_counts_changed_majorities():
    votes = {"ref": [T, T, T], "para": [T, T, F], "table": [F, F, T], "tie": [T, F]}
    out = m.invariance(votes, {"ref": ["para", "table", "tie"]})
    assert (out["changed"], out["pairs"], out["items"]) == (1, 2, ["table"])


def test_bootstrap_ci_brackets_the_estimate():
    labels = {f"i{n}": T for n in range(40)}
    votes = {i: [n % 4 != 0] * 3 for n, i in enumerate(labels)}  # 75% right

    def acc(sample):
        return m.accuracy(*m.resample(votes, labels, sample))["accuracy"]

    lo, hi = m.bootstrap_ci(acc, list(labels), n=500)
    assert lo < 0.75 < hi and hi - lo < 0.35
