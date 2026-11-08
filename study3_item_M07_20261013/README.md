# Study 3 item M07: a paired abstract Stag Hunt and executable migration (implemented 2026-10-14)

**Status:** implementation and software checks **completed**. Prompts and pilot are **proposed**.
No model data.

**Authorization (verbatim, user, 2026-10-14 ~02:40 UTC, this session):** "This authorizes local
implementation and software checks only: no model API calls, training, or resumed experiments."
No API calls were made. No training was done. Nothing was resumed.

## What runs
`harness/run_item.py` (stdlib only; Python 3.12.6) executes all 25 joint actions over real
localhost TCP: 5 own actions × 5 partner actions, 3 repetitions each, both services. That is 150
service-runs, about 88 s.

- **Services.** `orders` and `billing` each send their own **1,000 atomic requests** (seeded;
  sha256 `6dd938e6…`). 700 have payloads of 64–1,500 bytes and 300 have 5,000–60,000 bytes.
- **KEEP.** Requests go through a real broker process path to the peer's legacy inbox. The broker
  and both inboxes always run, so KEEP never depends on the partner. The broker rejects any
  legacy frame over **4,096 bytes**.
- **MIGRATE p.** Requests go straight to the peer's modern listener with no fallback. A peer that
  MIGRATEd to q listens and decodes with q only. A peer that KEEPs has no modern listener.
- **Protocols** (`harness/protocols.py`): A `json-b64`, B `xml-hex`, C `bin-fixed`, D `form-z85`.
  These are four genuinely different encodings, and each carries every request, including the
  60 kB ones.
- **Scoring.** A correct completion is a request whose exact content (id, account, amount, payload
  bytes) the receiver decoded and stored. It is counted by matching receiver stores against
  sender originals. Action labels are never compared.

## Observed payoff table (own correct completions; identical in all 6 service × rep runs per cell)
| own \ partner | KEEP | MIGRATE_A | MIGRATE_B | MIGRATE_C | MIGRATE_D |
|---|---|---|---|---|---|
| KEEP | 700 | 700 | 700 | 700 | 700 |
| MIGRATE_A | 0 | **1,000** | 0 | 0 | 0 |
| MIGRATE_B | 0 | 0 | **1,000** | 0 | 0 |
| MIGRATE_C | 0 | 0 | 0 | **1,000** | 0 |
| MIGRATE_D | 0 | 0 | 0 | 0 | **1,000** |

**Abstract payoffs** (completions / 100): KEEP 7; matching protocol 10; otherwise 0.
**No discrepancy** from the intended table.

How each outcome arose (`results/runs.csv`):
- **KEEP:** 700 delivered; the broker returned `REJECT 413` for the 300 oversized requests in
  every run.
- **MIGRATE vs KEEP:** `ConnectionRefusedError` (no modern listener); 0 delivered.
- **MIGRATE vs a different protocol:** every frame was sent, and the receiver's decoder raised on
  every one (`ParseError`, `JSONDecodeError`, `UnicodeDecodeError`, `struct.error`,
  `ValueError`).
- **Silent corruption:** none. No stored record anywhere failed to match an original.
- **Codec checks:** self round-trip is exact on 2,000 of 2,000 requests per protocol. Every
  cross-decoding attempt errors (12 ordered pairs × 50). Legacy frames: 1,400 under the limit and
  600 over, which is exactly the small/large split.

**Limits of the check.**
- Everything runs on one machine in one asyncio process, using real sockets and real codecs.
- The modern port is reserved by bind-then-close, so a port race is possible in principle. None
  occurred.
- Outcomes are deterministic by design, which is why there is no run-to-run variance.
- No timing or throughput component is included; the payoff is completions only.

## Prompts (draft, `prompts/`)
- `reference_choice.txt`: the partner-pool question. It has no partner and no game.
- `action_migration.txt`, `action_abstract.txt`: the action-only decision.
- `prediction.txt`: a separate call asking for the partner's protocol distribution; it requests
  no action.
- `disclosures.txt`: WITHHELD / DISCLOSED (source) / SUPPLIED (counts).
- `options_block.txt`: shuffled independently per call.
