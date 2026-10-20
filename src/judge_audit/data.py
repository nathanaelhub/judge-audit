"""Datasets: responses with a known PASS/FAIL label per rubric.

A dataset is a directory of TOML files, one per task. Each file has the
task ``prompt``, its ``[rubrics]`` (id -> criterion text) and a list of
``[[response]]`` tables, each labeled against one or more rubrics.

Labels come from how a response was built, not from a model: a
``reference`` that meets every clause, rewrites of it that change nothing
a rubric checks (``paraphrase``, ``format``, ``padding``), and
``minimal-fail`` edits that break exactly one clause. ``hard-pass`` items
are correct answers a judge has been seen to fail. A minimal-fail response
graded on a rubric it doesn't break becomes kind ``untouched`` for that
rubric, so per-kind accuracy separates the two.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

KINDS = {"reference", "paraphrase", "format", "padding", "variant-pass", "hard-pass", "minimal-fail"}
# Rewrites that must not change any verdict; compared against their reference.
INVARIANT_KINDS = {"paraphrase", "format", "padding"}


@dataclass(frozen=True)
class Item:
    """One (response, rubric) pair: the unit a judge grades."""

    task: str
    rubric: str
    criterion: str
    prompt: str
    response: str
    text: str
    label: bool
    kind: str
    of: str | None = None
    note: str | None = None

    @property
    def id(self) -> str:
        return f"{self.task}/{self.response}/{self.rubric}"


def load(path: str | Path) -> list[Item]:
    items = []
    files = sorted(Path(path).glob("*.toml"))
    if not files:
        raise ValueError(f"no .toml task files in {path}")
    for f in files:
        task = f.stem
        d = tomllib.loads(f.read_text(encoding="utf-8"))
        rubrics = d["rubrics"]
        ids = {r["id"] for r in d["response"]}
        for r in d["response"]:
            where = f"{f.name}: response {r['id']!r}"
            if r["kind"] not in KINDS:
                raise ValueError(f"{where}: unknown kind {r['kind']!r}")
            if r.get("of") and r["of"] not in ids:
                raise ValueError(f"{where}: 'of' names unknown response {r['of']!r}")
            if not r.get("labels"):
                raise ValueError(f"{where}: no labels")
            for rubric, label in r["labels"].items():
                if rubric not in rubrics:
                    raise ValueError(f"{where}: label for unknown rubric {rubric!r}")
                kind = "untouched" if r["kind"] == "minimal-fail" and label else r["kind"]
                items.append(Item(task=task, rubric=rubric, criterion=rubrics[rubric], prompt=d["prompt"],
                                  response=r["id"], text=r["text"].strip(), label=bool(label),
                                  kind=kind, of=r.get("of"), note=r.get("note")))
    if len({i.id for i in items}) != len(items):
        raise ValueError("duplicate item ids")
    return items


def invariance_groups(items: list[Item]) -> dict[str, list[str]]:
    """reference item id -> ids of rewrites that should get the same verdict."""
    by_id = {i.id: i for i in items}
    groups: dict[str, list[str]] = {}
    for i in items:
        if i.kind in INVARIANT_KINDS and i.of:
            ref = f"{i.task}/{i.of}/{i.rubric}"
            if ref in by_id and by_id[ref].label == i.label:
                groups.setdefault(ref, []).append(i.id)
    return groups
