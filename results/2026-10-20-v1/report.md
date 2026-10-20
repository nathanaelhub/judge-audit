79 items (56 PASS / 23 FAIL by construction), 1185 judge calls, $4.34 at API prices.

## Accuracy

| Judge | Model | Accuracy (95% CI) | False fail | False pass | Unparsed |
|---|---|---|---:|---:|---:|
| haiku | claude-haiku-5-5 | 97% (93%–100%) | 5% | 0% | 0 |
| sonnet | claude-sonnet-5-5 | 99% (99%–100%) | 1% | 0% | 0 |
| opus | claude-opus-5-5 | 99% (99%–100%) | 1% | 0% | 0 |

## Does voting help?

| Judge | Votes/item | Flip rate | Self-agreement κ | Error ICC | Majority-of-3 accuracy | If votes were independent | Effective votes (of 3) |
|---|---:|---:|---:|---:|---:|---:|---:|
| haiku | 5 | 1% | 0.97 | 0.80 | 97% | 100% | 1.2 |
| sonnet | 5 | 1% | 0.98 | — | 100% | 100% | — |
| opus | 5 | 1% | 0.98 | — | 100% | 100% | — |

## Does rewording change the verdict?

| Judge | Rewrites whose verdict differs from the reference |
|---|---|
| haiku | 1 of 24 (4%): dcf-inputs/padded/every-input-sourced |
| sonnet | 0 of 24 (0%) |
| opus | 0 of 24 (0%) |

## Accuracy by item kind

| Judge | format | hard-pass | minimal-fail | padding | paraphrase | reference | untouched | variant-pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| haiku | 96% | 100% | 100% | 88% | 100% | 91% | 100% | 100% |
| sonnet | 98% | 100% | 100% | 98% | 100% | 100% | 100% | 100% |
| opus | 100% | 90% | 100% | 100% | 100% | 99% | 100% | 100% |

## Agreement between judges (Cohen's κ on majority verdicts)

| | haiku | sonnet | opus |
|---|---:|---:|---:|
| haiku | — | 0.94 | 0.94 |
| sonnet | 0.94 | — | 1.00 |
| opus | 0.94 | 1.00 | — |

## Items judged wrong

**haiku** (4 items)

- `dcf-inputs/padded/every-input-sourced` (padding, truly PASS): wrong 5/5
- `ifrs-filer/reference/states-coverage-gap` (reference, truly PASS): wrong 5/5
- `dcf-inputs/prose/every-input-sourced` (format, truly PASS): wrong 2/5
- `dcf-inputs/reference/every-input-sourced` (reference, truly PASS): wrong 1/5

**sonnet** (2 items)

- `dcf-inputs/padded/every-input-sourced` (padding, truly PASS): wrong 1/5
- `dcf-inputs/prose/every-input-sourced` (format, truly PASS): wrong 1/5

**opus** (2 items)

- `ifrs-filer/baseline-older-years/states-coverage-gap` (hard-pass, truly PASS): wrong 1/5
- `ifrs-filer/reference/states-coverage-gap` (reference, truly PASS): wrong 1/5

