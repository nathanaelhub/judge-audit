# judge-audit

How far can you trust an LLM judge's PASS/FAIL verdict? `judge-audit` grades
responses whose correct verdict is **known in advance** and measures:

- **accuracy**, split into false fails (a good answer failed) and false passes;
- **self-consistency**: how often two votes on the same item disagree;
- **whether repeat votes are independent**: the error intraclass correlation
  (ICC) and the number of independent votes that *k* majority votes are worth;
- **invariance**: whether a paraphrase, a table instead of prose, or extra
  padding changes the verdict;
- **agreement between judges** (Cohen's κ).

It came out of an eval audit on [open-finance-mcp](https://github.com/nathanaelhub/open-finance-mcp),
where a Haiku judge with three votes per verdict failed answers that met
every clause of their rubric, and did so unanimously.

## Findings (2026-10-20, Haiku / Sonnet / Opus 5.5, 5 votes per item)

**1. Unanimous judge errors were dataset errors.** The first run (v1) found
Haiku wrong on four items, two of them on all five votes. Its errors were
locked to items: error ICC 0.80, so three votes were worth **1.2**
independent votes, and majority-of-3 accuracy (97%) was well short of the
100% that three independent votes would give. That is exactly the pattern
from the open-finance audit.

Reading the judges' reasoning showed the items were at fault, not the judges:

| Item | What the judges said | Who was right |
|---|---|---|
| `dcf-inputs` (reference and 2 rewrites; Haiku and Sonnet) | The beta's source, "prices from Yahoo Finance (unofficial)", isn't "a named data series or filing with a link or accession number" | The judges. The rubric asks for a link; the response didn't give one. |
| `ifrs-filer/reference` | The accession numbers look invented, and the rubric fails "sources [that aren't] real" | The judges. I had made them up. |

After the fix (v2: beta source given as the Yahoo chart series with a link;
Toyota items rebuilt from Toyota's real 20-F XBRL data; the two tasks
re-judged, the other seven tasks' verdicts carried over), all three judges
are at **100%** (Haiku and Opus each with a single stray vote), and no item is
failed more than once in five votes.

**So item-locked errors are a signal to check the item, not to add votes.**
Random judge noise is what voting fixes; a high error ICC says the noise
isn't random. In v1, more votes would only have made the wrong answer look
more certain.

**2. A rubric that asks for verification asks a tool-less judge to guess.**
The `ifrs-filer` rubric fails figures cited "without real, checkable
sources". Given Toyota's *real* accession numbers and filing URLs, Haiku and
Opus each still failed one vote of five on the grounds that the numbers
"may be invented". A judge without EDGAR access can't tell a real accession
number from a plausible fake; in v1 it was right to doubt them, in v2 it was
wrong. Rubrics should ask what's checkable from the text ("cites an
accession number or link") and leave existence checks to code.

**3. On clean items, modern judges are consistent.** In v2 the flip rate
is 0–1% and self-agreement κ is 0.99–1.00 for every judge. No paraphrase,
reformatting or padding changed a verdict (0 of 24 rewrites per judge), and
the three judges' majority verdicts agree completely.

Full tables: [v1 report](results/2026-10-20-v1/report.md),
[v2 report](results/2026-10-20-v2/report.md). Every verdict, with the judge's
full reasoning, is in the `verdicts.jsonl` next to each report.

### Caveats

- **79 items, one domain, written by one person.** The minimal-fail items
  turned out easy: every judge caught all 23. Harder near-miss failures
  would test false passes, which this set barely probes.
- **Opus helped validate the labels.** A one-vote Opus pilot over the
  dataset found one ambiguous item, which was rewritten
  (`debt-build/double-counted`; the pilot log is in `results/2026-10-20-v1/`).
  Opus's accuracy here is therefore not independent of the labels.
- **The ICC needs errors to measure.** With fewer than 10 wrong votes the
  report shows "—" rather than an ICC computed from noise (Sonnet and Opus
  in v1; every judge in v2).
- Judges run through `claude -p` at the CLI's default sampling settings, with
  the prompt in `src/judge_audit/judges.py`. This is not the prompt `claude
  plugin eval` uses internally, so these numbers say how these models judge
  these rubrics, not how that tool's grader does.

## The dataset

`datasets/finance/` has one TOML file per task, taken from the open-finance-mcp
eval suite: the task prompt, its LLM-graded rubrics (15 across 9 tasks), and
responses labeled against each rubric. Labels come from how each response
was built:

| Kind | What it is | Label |
|---|---|---|
| `reference` | Meets every clause of every rubric | PASS |
| `paraphrase`, `format`, `padding` | The reference reworded, turned into a table or prose, or padded with relevant-sounding material no rubric checks | PASS, and should match the reference's verdict |
| `minimal-fail` | The reference with one clause broken: a swapped GAAP/non-GAAP label, a missing input, a news-only citation, double-counted debt | FAIL on that rubric (`untouched` on the task's other rubrics) |
| `variant-pass` | Passes by a different route the rubric allows (e.g. "couldn't retrieve this") | PASS |
| `hard-pass` | Correct answers a judge has been seen to fail | PASS |

Each `minimal-fail` carries a `note` naming the clause it breaks. Figures that
a rubric checks are real (Apple's FY2024 debt components, Coca-Cola's and
NVIDIA's reported EPS, Toyota's IFRS revenue). Accession numbers are real
where a rubric asks for real sources (`ifrs-filer`); elsewhere they are
realistic in format but may not resolve, and the commentary around the
graded facts is illustrative.

## Usage

Requires [uv](https://docs.astral.sh/uv/) and the `claude` CLI, logged in.

```bash
uv run judge-audit validate datasets/finance
uv run judge-audit run datasets/finance --judges haiku,sonnet,opus --samples 5 --log runs/my.jsonl
uv run judge-audit report datasets/finance runs/my.jsonl
```

`run` appends to a JSONL log and skips calls already in it, so an
interrupted run resumes where it stopped. Set `JUDGE_AUDIT_USE_LOGIN=1` to
drop `ANTHROPIC_API_KEY` from the judge's environment and use the CLI's
claude.ai login instead.

Each judge call runs the CLI with no tools, MCP servers, settings, hooks or
plugins, and a fixed system prompt: about 600 input tokens of overhead,
against 41,000 for a default `claude -p` call on a machine with plugins
installed. The 1,185 calls in the v2 log cost $4.08 at API prices.

To audit your own judge, write a dataset in the same format: a rubric, a
response that passes it, and edits that break one clause at a time. The
statistics are in `src/judge_audit/metrics.py`, standard library only.

## Development

```bash
uv run pytest
```

Tests cover the statistics against hand-computed values and simulated
independent and copied votes, the dataset's consistency, verdict parsing,
and a resumed run against a fake judge.

MIT licensed.
