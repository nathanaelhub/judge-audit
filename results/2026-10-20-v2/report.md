79 items (56 PASS / 23 FAIL by construction), 1185 judge calls, $4.08 at API prices.

## Accuracy

| Judge | Model | Accuracy (95% CI) | False fail | False pass | Unparsed |
|---|---|---|---:|---:|---:|
| haiku | claude-haiku-5-5 | 100% (99%–100%) | 0% | 0% | 0 |
| sonnet | claude-sonnet-5-5 | 100% (100%–100%) | 0% | 0% | 0 |
| opus | claude-opus-5-5 | 100% (99%–100%) | 0% | 0% | 0 |

## Does voting help?

| Judge | Votes/item | Flip rate | Self-agreement κ | Error ICC | Majority-of-3 accuracy | If votes were independent | Effective votes (of 3) |
|---|---:|---:|---:|---:|---:|---:|---:|
| haiku | 5 | 1% | 0.99 | — | 100% | 100% | — |
| sonnet | 5 | 0% | 1.00 | — | 100% | 100% | — |
| opus | 5 | 1% | 0.99 | — | 100% | 100% | — |

## Does rewording change the verdict?

| Judge | Rewrites whose verdict differs from the reference |
|---|---|
| haiku | 0 of 24 (0%) |
| sonnet | 0 of 24 (0%) |
| opus | 0 of 24 (0%) |

## Accuracy by item kind

| Judge | format | hard-pass | minimal-fail | padding | paraphrase | reference | untouched | variant-pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| haiku | 100% | 100% | 100% | 100% | 100% | 99% | 100% | 100% |
| sonnet | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| opus | 100% | 90% | 100% | 100% | 100% | 100% | 100% | 100% |

## Agreement between judges (Cohen's κ on majority verdicts)

| | haiku | sonnet | opus |
|---|---:|---:|---:|
| haiku | — | 1.00 | 1.00 |
| sonnet | 1.00 | — | 1.00 |
| opus | 1.00 | 1.00 | — |

## Items judged wrong

**haiku** (1 items)

- `ifrs-filer/reference/states-coverage-gap` (reference, truly PASS): wrong 1/5

**sonnet** (0 items)


**opus** (1 items)

- `ifrs-filer/baseline-older-years/states-coverage-gap` (hard-pass, truly PASS): wrong 1/5

