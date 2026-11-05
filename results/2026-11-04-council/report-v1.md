191 items (46 PASS / 145 FAIL by construction), 1910 judge calls, $5.30 at API prices.

## Accuracy

| Judge | Model | Accuracy (95% CI) | False fail | False pass | Unparsed |
|---|---|---|---:|---:|---:|
| sonnet | claude-sonnet-5-5 | 96% (93%–98%) | 0% | 6% | 0 |
| haiku | claude-haiku-5-5 | 94% (90%–97%) | 1% | 8% | 0 |

## Does voting help?

| Judge | Votes/item | Flip rate | Self-agreement κ | Error ICC | Majority-of-3 accuracy | If votes were independent | Effective votes (of 3) |
|---|---:|---:|---:|---:|---:|---:|---:|
| sonnet | 5 | 1% | 0.98 | 0.90 | 96% | 99% | 1.1 |
| haiku | 5 | 2% | 0.95 | 0.83 | 94% | 99% | 1.1 |

## Does rewording change the verdict?

| Judge | Rewrites whose verdict differs from the reference |
|---|---|
| sonnet | 0 of 0 (—) |
| haiku | 0 of 0 (—) |

## Accuracy by item kind

| Judge | hard-pass | minimal-fail | reference | variant-pass |
|---|---:|---:|---:|---:|
| sonnet | 100% | 94% | 100% | 100% |
| haiku | 100% | 92% | 99% | 100% |

## Agreement between judges (Cohen's κ on majority verdicts)

| | sonnet | haiku |
|---|---:|---:|
| sonnet | — | 0.95 |
| haiku | 0.95 | — |

## Items judged wrong

**sonnet** (10 items)

- `BL2025-1008/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1434/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1442/e5c5b737/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1614/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `RS2026-1721/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `RS2026-2123/76c4627d/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1572/ed3bf084/faithful` (minimal-fail, truly FAIL): wrong 4/5
- `RS2026-2224/ff783eb5/faithful` (minimal-fail, truly FAIL): wrong 4/5
- `RS2026-2125/b4917edc/faithful` (minimal-fail, truly FAIL): wrong 1/5
- `RS2026-2187/31ad2502/faithful` (minimal-fail, truly FAIL): wrong 1/5

**haiku** (15 items)

- `BL2026-1434/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1572/ed3bf084/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1590/50edfe4f/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1614/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `RS2026-1721/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `RS2026-2125/b4917edc/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `RS2026-2224/ff783eb5/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1442/e5c5b737/faithful` (minimal-fail, truly FAIL): wrong 4/5
- `RS2026-2105/4025adb9/faithful` (minimal-fail, truly FAIL): wrong 4/5
- `RS2026-2123/76c4627d/faithful` (minimal-fail, truly FAIL): wrong 4/5
- `RS2026-2187/31ad2502/faithful` (minimal-fail, truly FAIL): wrong 4/5
- `BL2025-1008/published/faithful` (minimal-fail, truly FAIL): wrong 3/5
- `BL2026-1442/reference/faithful` (reference, truly PASS): wrong 2/5
- `RS2026-2144/4bd85524/faithful` (minimal-fail, truly FAIL): wrong 2/5
- `RS2026-2233/b72f2757/faithful` (minimal-fail, truly FAIL): wrong 1/5

