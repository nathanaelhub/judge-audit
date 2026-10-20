"""Turn a verdict log into reliability statistics and a Markdown report."""

from __future__ import annotations

from collections import defaultdict

from . import metrics as m
from .data import Item, invariance_groups


def votes_by_judge(rows: list[dict], items: list[Item]) -> dict[str, dict[str, list[bool | None]]]:
    """judge -> item id -> verdicts in sample order (errored calls skipped)."""
    known = {i.id for i in items}
    out: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in sorted(rows, key=lambda r: r["sample"]):
        if not r.get("error") and r["item"] in known:
            out[r["judge"]][r["item"]].append(r["verdict"])
    return {j: dict(v) for j, v in out.items()}


# Fewer wrong votes than this and the error ICC is noise, not a measurement.
MIN_ERRORS_FOR_ICC = 10


def summarize(votes: dict[str, list], items: list[Item], k_majority: int = 3, ci_draws: int = 2000) -> dict:
    labels = {i.id: i.label for i in items}
    votes = {i: v for i, v in votes.items() if i in labels}
    acc = m.accuracy(votes, labels)
    wrong = sum(v is not None and v != labels[i] for i, vs in votes.items() for v in vs)
    icc = m.error_icc(votes, labels) if wrong >= MIN_ERRORS_FOR_ICC else None
    k = min((len(v) for v in votes.values()), default=0)
    parsed = sum(v is not None for vs in votes.values() for v in vs)
    total = sum(len(vs) for vs in votes.values())
    p = 1 - acc["accuracy"] if acc["accuracy"] is not None else None

    def acc_of(sample):
        return m.accuracy(*m.resample(votes, labels, sample))["accuracy"]

    out = {
        **acc,
        "accuracy_ci": m.bootstrap_ci(acc_of, list(votes), n=ci_draws),
        "unparsed": total - parsed,
        "wrong_votes": wrong,
        "samples_per_item": k,
        "flip_rate": m.flip_rate(votes),
        "self_kappa": m.fleiss_kappa(votes),
        "error_icc": icc,
        "majority_k": k_majority if k >= k_majority else None,
        "majority_accuracy": m.majority_accuracy(votes, labels, k_majority) if k >= k_majority else None,
        "majority_accuracy_if_independent": (1 - m.binomial_majority_error(p, k_majority)
                                             if p is not None and k >= k_majority else None),
        "effective_votes": m.effective_votes(k_majority, icc) if icc is not None and k >= k_majority else None,
        "invariance": m.invariance(votes, invariance_groups(items)),
    }
    by_kind: dict[str, list[bool]] = defaultdict(list)
    kind_of = {i.id: i.kind for i in items}
    for iid, vs in votes.items():
        by_kind[kind_of[iid]] += [v == labels[iid] for v in vs if v is not None]
    out["accuracy_by_kind"] = {kd: sum(x) / len(x) for kd, x in sorted(by_kind.items()) if x}
    return out


def wrong_items(votes: dict[str, list], items: list[Item]) -> list[tuple[Item, int, int]]:
    """Items the judge got wrong at least once: (item, wrong votes, total votes)."""
    out = []
    for it in items:
        vs = [v for v in votes.get(it.id, []) if v is not None]
        wrong = sum(v != it.label for v in vs)
        if wrong:
            out.append((it, wrong, len(vs)))
    return sorted(out, key=lambda t: (-t[1] / t[2], t[0].id))


def _f(x, pct=False, nd=2):
    if x is None:
        return "—"
    return f"{100 * x:.0f}%" if pct else f"{x:.{nd}f}"


def markdown(rows: list[dict], items: list[Item]) -> str:
    by_judge = votes_by_judge(rows, items)
    models = {r["judge"]: r.get("model") for r in rows if r.get("model")}
    cost = sum(r.get("cost_usd") or 0 for r in rows)
    lines = [f"{len(items)} items ({sum(i.label for i in items)} PASS / {sum(not i.label for i in items)} FAIL by construction), "
             f"{len(rows)} judge calls, ${cost:.2f} at API prices.", ""]

    lines += ["## Accuracy", "",
              "| Judge | Model | Accuracy (95% CI) | False fail | False pass | Unparsed |",
              "|---|---|---|---:|---:|---:|"]
    sums = {j: summarize(v, items) for j, v in by_judge.items()}
    for j, s in sums.items():
        ci = s["accuracy_ci"]
        interval = f" ({_f(ci[0], True)}–{_f(ci[1], True)})" if ci else ""
        lines.append(f"| {j} | {models.get(j, '')} | {_f(s['accuracy'], True)}{interval} | "
                     f"{_f(s['false_fail'], True)} | {_f(s['false_pass'], True)} | {s['unparsed']} |")

    lines += ["", "## Does voting help?", "",
              "| Judge | Votes/item | Flip rate | Self-agreement κ | Error ICC | Majority-of-3 accuracy | If votes were independent | Effective votes (of 3) |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for j, s in sums.items():
        lines.append(f"| {j} | {s['samples_per_item']} | {_f(s['flip_rate'], True)} | {_f(s['self_kappa'])} | "
                     f"{_f(s['error_icc'])} | {_f(s['majority_accuracy'], True)} | "
                     f"{_f(s['majority_accuracy_if_independent'], True)} | {_f(s['effective_votes'], nd=1)} |")

    lines += ["", "## Does rewording change the verdict?", "",
              "| Judge | Rewrites whose verdict differs from the reference |", "|---|---|"]
    for j, s in sums.items():
        inv = s["invariance"]
        lines.append(f"| {j} | {inv['changed']} of {inv['pairs']} ({_f(inv['rate'], True)})"
                     + (f": {', '.join(inv['items'])}" if inv["items"] else "") + " |")

    kinds = sorted({k for s in sums.values() for k in s["accuracy_by_kind"]})
    lines += ["", "## Accuracy by item kind", "", "| Judge | " + " | ".join(kinds) + " |",
              "|---|" + "---:|" * len(kinds)]
    for j, s in sums.items():
        lines.append(f"| {j} | " + " | ".join(_f(s["accuracy_by_kind"].get(k), True) for k in kinds) + " |")

    if len(by_judge) > 1:
        judges = list(by_judge)
        lines += ["", "## Agreement between judges (Cohen's κ on majority verdicts)", "",
                  "| | " + " | ".join(judges) + " |", "|---|" + "---:|" * len(judges)]
        maj = {j: {i: m.majority([x for x in v if x is not None]) if any(x is not None for x in v) else None
                   for i, v in by_judge[j].items()} for j in judges}
        for a in judges:
            lines.append(f"| {a} | " + " | ".join("—" if a == b else _f(m.cohen_kappa(maj[a], maj[b])) for b in judges) + " |")

    lines += ["", "## Items judged wrong", ""]
    for j, v in by_judge.items():
        wrong = wrong_items(v, items)
        lines += [f"**{j}** ({len(wrong)} items)", ""]
        for it, w, n in wrong:
            truth = "PASS" if it.label else "FAIL"
            lines.append(f"- `{it.id}` ({it.kind}, truly {truth}): wrong {w}/{n}")
        lines.append("")
    return "\n".join(lines)
