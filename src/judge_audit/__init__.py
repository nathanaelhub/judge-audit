"""Measure how far an LLM judge's PASS/FAIL verdicts can be trusted."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    from . import data, report, run

    ap = argparse.ArgumentParser(prog="judge-audit", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="load a dataset and print what it contains")
    v.add_argument("dataset", type=Path)

    r = sub.add_parser("run", help="collect verdicts (resumable)")
    r.add_argument("dataset", type=Path)
    r.add_argument("--judges", default="haiku", help="comma-separated claude model aliases or ids")
    r.add_argument("--samples", type=int, default=5, help="verdicts per judge per item")
    r.add_argument("--concurrency", type=int, default=4)
    r.add_argument("--log", type=Path, required=True, help="JSONL file to append verdicts to")
    r.add_argument("--only", help="only items whose id contains this text")

    p = sub.add_parser("report", help="print the Markdown report for a verdict log")
    p.add_argument("dataset", type=Path)
    p.add_argument("log", type=Path)

    a = ap.parse_args(argv)
    items = data.load(a.dataset)
    if a.cmd == "validate":
        kinds: dict[str, int] = {}
        for i in items:
            kinds[i.kind] = kinds.get(i.kind, 0) + 1
        print(f"{len(items)} items: {sum(i.label for i in items)} PASS, {sum(not i.label for i in items)} FAIL")
        print("by kind: " + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items())))
        print(f"invariance groups: {len(data.invariance_groups(items))}")
        return 0
    if a.cmd == "run":
        if a.only:
            items = [i for i in items if a.only in i.id]
        judges = [j.strip() for j in a.judges.split(",") if j.strip()]
        asyncio.run(run.collect(items, judges, a.samples, a.log, a.concurrency,
                                progress=lambda s: print(s, file=sys.stderr, flush=True)))
        return 0
    print(report.markdown(run.read_log(a.log), items))
    return 0
