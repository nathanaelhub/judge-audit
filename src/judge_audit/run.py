"""Collect k verdicts per (judge, item) into a resumable JSONL log."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from pathlib import Path

from .data import Item
from .judges import ClaudeCLI


def read_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def done_keys(rows: list[dict]) -> set[tuple[str, str, int]]:
    """Calls that produced a reply; errored calls are retried on the next run."""
    return {(r["judge"], r["item"], r["sample"]) for r in rows if not r.get("error")}


async def collect(items: list[Item], judges: list[str], samples: int, log: Path,
                  concurrency: int = 4, progress: Callable[[str], None] = print) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    done = done_keys(read_log(log))
    todo = [(j, it, s) for j in judges for it in items for s in range(samples)
            if (j, it.id, s) not in done]
    progress(f"{len(todo)} calls to make ({len(done)} already in {log})")
    backends = {j: ClaudeCLI(j) for j in judges}
    sem = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()
    finished = 0

    async def one(judge: str, item: Item, sample: int) -> None:
        nonlocal finished
        async with sem:
            t0 = time.monotonic()
            j = await backends[judge].judge(item)
        row = {"judge": judge, "model": j.model, "item": item.id, "sample": sample,
               "verdict": j.verdict, "label": item.label, "cost_usd": j.cost_usd,
               "seconds": round(time.monotonic() - t0, 1), "error": j.error, "reply": j.reply}
        async with lock:
            with log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            finished += 1
            if j.error or finished % 25 == 0 or finished == len(todo):
                progress(f"  {finished}/{len(todo)}" + (f"  error on {item.id}: {j.error}" if j.error else ""))

    await asyncio.gather(*(one(*t) for t in todo))
    return len(todo)
