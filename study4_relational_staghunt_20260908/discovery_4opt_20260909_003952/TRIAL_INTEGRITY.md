# Trial integrity - four-object discovery

Run `discovery_4opt_20260909_003952`, 2026-09-08.

| check | value | verdict |
|---|---|---|
| planned calls | 336 | — |
| rows written | 336 | PASS |
| transport ok | 336/336 | PASS |
| parsed ok | 336/336 | PASS |
| parse failures | 0 | PASS |
| duplicate (array,model,perm) | 0 | PASS |
| cells missing trials | 0 | PASS |
| checkpoint substitutions | 0 | PASS |
| retries needed | 0 | PASS |
| token usage recorded | no | runner does not expose it |

Every cell = exactly 24 trials, one per permutation, so every canonical object
appeared in every screen position exactly 6 times per model x array.

No stop condition was triggered. Checkpoints `gpt-5.5` / `claude-opus-5` returned on all 336 rows.
Prompt sha8 `d40ea45d` (four-option) stamped on all 336 rows.
