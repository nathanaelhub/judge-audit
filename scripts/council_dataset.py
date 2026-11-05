"""Build datasets/council from the Nashville Council Digest's labeled summaries.

Run from this repo with the digest installed alongside, so its own code produces
the exact text its judge was shown:

    uv run --with-editable ../nashville-council-digest python scripts/council_dataset.py ../nashville-council-digest
    uv run --with-editable ../nashville-council-digest python scripts/council_dataset.py ../nashville-council-digest v2

Each task is one bill or resolution: the prompt is the official text the summary
was written from, the one rubric is the digest judge's own faithfulness criterion,
and the responses are summaries with known labels:

- reference: the published summary, from the digest's planted-error evaluation
  (2026-10-29), where a review found none of the 80 wrong.
- minimal-fail: a copy with one planted error (a changed amount or number, a name
  not in the bill, two names swapped, the opening verb reversed), or one of the six
  published summaries the 2026-10-30 review found really wrong.
- variant-pass: a planted swap that kept the meaning, by the 2026-10-29 review's rule:
  the two names swapped are the two sides of a symmetric phrase ("a contract between
  A and B" became "between B and A"). Decided from the text by `symmetric_swap`,
  not from any judge's verdict.
- hard-pass: one of the four correct published summaries the digest's judge flagged
  (its own explanation said nothing was wrong).

Left out because the right label is arguable: the garbled RM20/RM9-NS summary,
three loose wordings, and RS2026-2150 (the resolution and its analysis disagree on
the Sheriff's pay). A seeded sample of 40 of the 80 evaluated bills keeps the run
affordable at five votes each.
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

CRITERION = (
    "The summary is faithful to the official text: everything it says is supported by the text, "
    "and nothing is reversed or attached to the wrong party, place or amount. Leaving details out "
    "is fine; saying something the text doesn't support, or the opposite of what it says, is not."
)
# v2: the same rule, except an omission that changes what the item does is not fine. Tested because
# v1 let a dropped condition ("only if the owner joins MDHA's plan") pass as an allowed omission.
CRITERION_V2 = (
    "The summary is faithful to the official text: everything it says is supported by the text, "
    "and nothing is reversed or attached to the wrong party, place or amount. Leaving details out "
    "is fine, unless what is left out changes what the item does: a condition, limit or exception "
    "that the summary's statement depends on. Saying something the text doesn't support, or the "
    "opposite of what it says, is not."
)
PROMPT = "Summarize this Nashville Metro Council item in plain language for residents.\n\n{source}"

# From evals/results/2026-10-30-judge/review.md in the digest.
REAL_ERRORS = {
    "BL2026-1363": "says the firearms, knives and drones ban can be waived; the text bans them outright",
    "RS2026-1721": "states the $42 million cap unconditionally; it applies only if the owner joins MDHA's plan",
    "BL2025-1008": "calls 120% of median income the limit; it is a ceiling, and each district sets its own",
    "BL2026-1434": "notice goes to the owner of land the easement crosses, not 'easement owners'",
    "BL2026-1614": "requires NDOT and Water approval; the text says NDOT and/or Water",
    "BL2026-1257": "puts the backyard cottage 'behind' the house; the text doesn't",
}
FALSE_ALARMS = ["BL2025-1158", "BL2025-1072", "RS2026-1869", "RS2026-1962"]
AMBIGUOUS = {"RS2026-2150"}
SAMPLE = 40


def symmetric_swap(original: str, swapped: str) -> bool:
    """True when the swap only reversed the two sides of "between A and B"."""
    for m in re.finditer(r"between (.+?) and (.+?)(?=[,.]| for | to | on | through )", original):
        a, b = m.group(1), m.group(2)
        if original.replace(f"between {a} and {b}", f"between {b} and {a}", 1) == swapped:
            return True
    return False


def toml_str(s: str) -> str:
    if "'''" in s:
        raise ValueError("text contains ''' and can't be a literal string")
    return "'''\n" + s.strip() + "\n'''"


def write_task(out: Path, file: str, source: str, responses: list[dict], criterion: str = CRITERION) -> None:
    lines = [f"prompt = {toml_str(PROMPT.format(source=source))}", "", "[rubrics]",
             f"faithful = {json.dumps(criterion)}", ""]
    for r in responses:
        lines += ["[[response]]", f'id = "{r["id"]}"', f'kind = "{r["kind"]}"']
        if r.get("of"):
            lines.append(f'of = "{r["of"]}"')
        if r.get("note"):
            lines.append(f"note = {json.dumps(r['note'])}")
        lines += [f"labels = {{ faithful = {'true' if r['label'] else 'false'} }}", f"text = {toml_str(r['text'])}", ""]
    (out / f"{file}.toml").write_text("\n".join(lines), encoding="utf-8")


def by_kind_original(cases: list[dict]) -> str:
    return next(c["summary"] for c in cases if c["kind"] == "original")


def main(digest: str, version: str = "v1") -> None:
    root = Path(digest)
    name = "council" if version == "v1" else f"council-{version}"
    criterion = CRITERION if version == "v1" else CRITERION_V2
    out = Path(__file__).resolve().parents[1] / "datasets" / name
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.toml"):
        old.unlink()

    cases = json.loads((root / "evals/results/2026-10-29/cases.json").read_text(encoding="utf-8"))
    by_file: dict[str, list[dict]] = {}
    for c in cases:
        by_file.setdefault(c["file"], []).append(c)
    files = sorted(f for f in by_file if f not in AMBIGUOUS)
    chosen = sorted(random.Random(20261104).sample(files, SAMPLE))

    tasks: dict[str, tuple[str, list[dict]]] = {}
    for f in chosen:
        responses, source = [], None
        for c in sorted(by_file[f], key=lambda c: (c["kind"] != "original", c["id"])):
            source = c["source"]
            if c["kind"] == "original":
                responses.append({"id": "reference", "kind": "reference", "label": True, "text": c["summary"]})
            elif c["kind"] == "swap" and symmetric_swap(by_kind_original(by_file[f]), c["summary"]):
                responses.append({"id": c["id"], "kind": "variant-pass", "of": "reference", "label": True,
                                  "note": "planted swap that kept the meaning", "text": c["summary"]})
            else:
                responses.append({"id": c["id"], "kind": "minimal-fail", "of": "reference", "label": False,
                                  "note": f"planted: {c['kind']}", "text": c["summary"]})
        tasks[f] = (source, responses)

    # Published summaries reviewed by hand after the digest's judge flagged them.
    from council_digest import summarize
    from council_digest.records import meetings
    items = {i.file: i for m in meetings() for i in m.items}
    for f, why in [*REAL_ERRORS.items(), *((f, None) for f in FALSE_ALARMS)]:
        it = items[f]
        summary = json.loads((root / "data/summaries" / f"{f}.json").read_text(encoding="utf-8"))["summary"]
        r = ({"id": "published", "kind": "minimal-fail", "label": False, "note": f"real error: {why}", "text": summary}
             if why else {"id": "published", "kind": "hard-pass", "label": True,
                          "note": "correct; the digest's judge flagged it in a batch of 8", "text": summary})
        source, responses = tasks.get(f, (summarize.source(it), []))
        tasks[f] = (source, responses + [r])

    for f, (source, responses) in sorted(tasks.items()):
        write_task(out, f, source, responses, criterion)
    n = sum(len(r) for _, r in tasks.values())
    print(f"{len(tasks)} tasks, {n} responses -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../nashville-council-digest", sys.argv[2] if len(sys.argv) > 2 else "v1")
