191 items (46 PASS / 145 FAIL by construction), 955 judge calls, $5.28 at API prices.

## Accuracy

| Judge | Model | Accuracy (95% CI) | False fail | False pass | Unparsed |
|---|---|---|---:|---:|---:|
| sonnet | claude-sonnet-5-5 | 96% (94%–99%) | 2% | 4% | 0 |

## Does voting help?

| Judge | Votes/item | Flip rate | Self-agreement κ | Error ICC | Majority-of-3 accuracy | If votes were independent | Effective votes (of 3) |
|---|---:|---:|---:|---:|---:|---:|---:|
| sonnet | 5 | 1% | 0.98 | 0.90 | 96% | 100% | 1.1 |

## Does rewording change the verdict?

| Judge | Rewrites whose verdict differs from the reference |
|---|---|
| sonnet | 0 of 0 (—) |

## Accuracy by item kind

| Judge | hard-pass | minimal-fail | reference | variant-pass |
|---|---:|---:|---:|---:|
| sonnet | 100% | 96% | 98% | 100% |

## Items judged wrong

**sonnet** (8 items)

- `BL2025-1008/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1442/e5c5b737/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1614/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `RS2026-1721/published/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `RS2026-2123/76c4627d/faithful` (minimal-fail, truly FAIL): wrong 5/5
- `BL2026-1565/reference/faithful` (reference, truly PASS): wrong 4/5
- `BL2026-1572/ed3bf084/faithful` (minimal-fail, truly FAIL): wrong 4/5
- `RS2026-2224/ff783eb5/faithful` (minimal-fail, truly FAIL): wrong 2/5

