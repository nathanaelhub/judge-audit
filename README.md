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

- **79 items, one domain, written by one person** (the first dataset; see the council dataset above for a second). The minimal-fail items
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

## Second dataset: council summaries (2026-11-04, Sonnet / Haiku 5.5, 5 votes per item)

The [Nashville Council Digest](https://github.com/nathanaelhub/nashville-council-digest) publishes
Claude-written summaries of city legislation only after a second Claude reading (its "judge")
says they're faithful. Run over 1,124 summaries in batches of 8, that judge flagged 14; a review
called 6 of them real errors and 4 false alarms. `datasets/council/` turns the digest's labeled
summaries into judge-audit tasks: 50 bills (a seeded sample of 40 from its planted-error
evaluation, plus 10 reviewed flags), 191 summaries, with the digest judge's own faithfulness rule
as the rubric. Built by `scripts/council_dataset.py`.

| | Sonnet | Haiku |
|---|---:|---:|
| Accuracy (191 items, 5 votes) | 96% | 94% |
| Correct summaries flagged (40 published + 2 harmless swaps) | 0 of 42 | 0 of 42 |
| The digest's 4 batch false alarms, judged one at a time | 0 of 4 flagged | 0 of 4 flagged |
| Planted wrong amounts, numbers, names, reversed verbs | 112 of 112 | 111 of 112 |
| Planted name swaps | 23 of 27 | 20 of 27 |
| The 6 "real errors" from the digest's review | 2 of 6 | 2 of 6 |
| Error ICC; 3 votes are worth | 0.90; 1.1 votes | 0.83; 1.1 votes |

(Counts are majority verdicts over 5 votes.)

**1. The false alarms didn't come back one at a time.** Each of the four summaries the batched
judge flagged, while its own explanation said nothing was wrong, passed 5 of 5 times with both
models. Two things differ from the digest, though: these calls judge one summary each with this
repo's prompt, and the four were chosen *because* they were flagged, so they might pass on a
re-run in batches too. This run can't separate those.

**2. Errors are locked to items again, so voting doesn't help.** Error ICC 0.90 (Sonnet): three
votes are worth 1.1 independent ones. The misses are the same items every time.

**3. Most of those items are judgment calls, and one was my labeling mistake.**

- The first version of the converter labeled a planted swap harmless only if the digest's judge
  had accepted it. That made the labels depend on the judge being audited. RS2026-2192 ("a
  contract between A and B" written as "between B and A") was labeled an error because the old
  judge flagged it; Sonnet passed it 5 of 5, correctly. Harmless swaps are now decided from the
  text (`symmetric_swap`, tested), and the numbers above use the corrected labels.
- Sonnet's other repeated misses are 4 scrambled-word swaps (a name or address moved
  mid-sentence, leaving garbled but recoverable text) and 4 of the review's 6 "real errors". On those four it named the exact
  problem and called it minor: "a loose but consistent paraphrase", "a slight simplification of
  'and/or'", "the response omits that condition, but omission is allowed". The digest's rule does
  say leaving details out is fine. For RS2026-1721, the strongest of the four, Sonnet argued that
  "any property tax abatement" already carries the condition, since an abatement exists only if the
  owner joins the plan, which is a fair reading. The review that labeled these was done by
  Claude, not an independent person; this run says those labels are arguable.

**4. A stricter rule finds a real omission on the live site.** `datasets/council-v2/` is the same
dataset with one change to the rule: an omission is *not* fine "if what is left out changes what
the item does: a condition, limit or exception that the summary's statement depends on." Sonnet
then caught one more of the six reviewed errors (3 of 6), missed one fewer swap, and failed one
published summary 4 of 5 times: BL2026-1565 says projects over $5 million "still need a completed
cost itemization form", and the ordinance exempts planning-only and enterprise-funded projects.
Under the stricter rule that's a real error, and it's on the digest today.

Reports: [v1](results/2026-11-04-council/report-v1.md),
[v2 rule](results/2026-11-04-council/report-v2.md); every verdict with the judge's reasoning
is next to them. 2,865 calls, $10.58 at API prices.

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
