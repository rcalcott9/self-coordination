# AUDIT PROCEDURE — code-convention item battery

Auditor: T3 (code-redteam). Procedure version 1.0, paired with `rejection_rubric.md` v1.0.
Written blind, before receipt of any item. **This procedure is not yet running.** It executes only
when the lead sends T2's items in a separate message.

---

## 0. Standing constraints

- **No API calls, ever.** Every test in the rubric is a reading, reasoning, or local-computation
  test. Nothing here requires querying a model. If a question can only be settled empirically, the
  verdict is FLAG with a note for the pilot gate — never a probe.
- **Write only** under `audits/code/`. No edits to lead-owned control documents, and none to
  `code/design/`.
- **Independence.** `code/design/` has not been read and will not be read except for the item file
  the lead sends. If the lead sends a path rather than content, only the item file itself is opened;
  T2's rationale, notes, or self-audit are not read before verdicts are recorded, because reading
  T2's justification is the fastest way to lose an independent judgement.

## 1. Inputs required before the audit can start

Refuse to start, and say so, if any of these is missing — auditing an item stripped of its prompt
context can only catch a subset of C6.

| input | why |
|---|---|
| the item set: `item_id`, stem, all four options, `mechanism`, `family` | the unit of audit |
| the **exact full prompt** as it will be sent, including system prompt, instructions, and any worked example | C6 leaks live outside the stem as often as inside it |
| the response schema / answer format and the mapping rule to `canonical_choice` | C8 is unauditable without it |
| how option order is seeded (`presentation_id`) | C7 (iv) and B4 |
| the target language(s) and any stated codebase context per item | C2, C3 and C4 are all context-dependent |

If only partial input arrives, audit what is there and mark the unauditable criteria `NA` with the
missing input named. `NA` is never counted as 0.

## 2. Pass structure

Run passes in this order and do not look ahead. The ordering is deliberate: the masked-stem pass
must happen before the options are ever seen, and the convention pass must happen before any
positive-validity reasoning, so that the desire to keep an item does not soften the tests.

- **Pass 0 — freeze.** Record the rubric hash, the item-file hash, the date, and the item count.
- **Pass 1 — masked stems (C6).** Read every stem with options hidden. For each, write down a
  predicted modal answer, or "no prediction". Only then uncover. Run the banned-lexicon grep and the
  stem/option token-overlap check. Record predictions before uncovering; a prediction written after
  seeing the options is worthless.
- **Pass 2 — surface metrics (C7, C8).** Mechanical, no judgement: option character lengths and
  max/min ratio, case-style and formatting odd-one-out sweep, parallel-form check, the six pairwise
  mutual-exclusivity checks, order-permutability, and the five-response double-coding check against
  the mapping rule.
- **Pass 3 — semantics (C4, C2, C1, C5).** In that order. Equivalence first, because a
  functionally distinct option set makes the rest moot. For each firing criterion, produce the
  artefact the rubric's evidence table demands (snippet, diagnostic name, mechanism-plus-scale).
- **Pass 4 — convention status (C3, C9, C10).** The judgement-heavy pass. For every item, write out
  the two-source test result, the ignorance and rephrase probes, and all three C10 test outputs.
  These are written in full even when the criterion does not fire, because a bare "C10: 0" is not
  reviewable by the lead.
- **Pass 5 — positive validity (A1, A2, A3).** Only for items still standing. Name the sources for
  A2 and write the four one-sentence defences for A3.
- **Pass 6 — aggregation and battery checks.** Apply the verdict rules; run B1-B5; write repairs.
- **Pass 7 — self-check.** Re-read every ACCEPT and ask once more: *would every competent model give
  the same answer, and would it be able to say why?* If yes, the item is C10 and the earlier pass
  was too generous. Also re-read every REJECT-DOMAIN and confirm it is not actually a repairable
  construction defect being mislabelled as a fact about the world.

## 3. Verdict rules (from the rubric, restated for execution)

- any criterion at severity 2 → **REJECT**
- three or more criteria at severity 1 → **REJECT**
- one or two criteria at severity 1, none at 2 → **FLAG**
- all criteria at 0 but A1/A2/A3 not positively evidenced → **FLAG**
- all criteria at 0 and A1-A3 evidenced → **ACCEPT**
- REJECT is sub-labelled `REJECT-CONSTRUCTION` (Class A: C1, C2, C4, C5, C6, C7, C8, C9) or
  `REJECT-DOMAIN` (Class B: C3, C10). If both classes fire, label `REJECT-CONSTRUCTION` and note the
  Class-B finding separately, so the Class-B rate is not inflated by items that were broken anyway.

Ties and doubt resolve **downward** (toward FLAG/REJECT). A wrongly rejected item costs one item; a
wrongly accepted item contaminates `cross_model_match` for the whole domain and cannot be detected
after collection.

## 4. Output format

Three artefacts, all written under `audits/code/`.

### 4.1 `item_verdicts.csv` — machine-readable, one row per item

Column order is fixed. Severity columns take `0`, `1`, `2`, or `NA`.

```
item_id,mechanism,family,verdict,verdict_sublabel,C1,C2,C3,C4,C5,C6,C7,C8,C9,C10,A1,A2,A3,
n_at_2,n_at_1,primary_criterion,repairable,mechanism_changed_by_repair,auditor,rubric_version,
rubric_sha256,item_file_sha256,audit_date
```

- `verdict` ∈ {ACCEPT, FLAG, REJECT}
- `verdict_sublabel` ∈ {"", REJECT-CONSTRUCTION, REJECT-DOMAIN}
- `A1|A2|A3` ∈ {met, unmet, NA}
- `primary_criterion` — the single criterion that most drives the verdict, for triage
- `repairable` ∈ {yes, no, n/a}; `mechanism_changed_by_repair` ∈ {yes, no, n/a}
- `auditor` = `T3`

### 4.2 `item_findings.md` — human-readable, one block per item

Every item gets a block, including ACCEPTs. Evidence fields carry the artefacts the rubric's
evidence table requires; a criterion at 1 or 2 with an empty evidence field is an incomplete audit,
not a finding.

```
### <item_id>  [<mechanism> / <family>]
VERDICT: <ACCEPT|FLAG|REJECT> (<sublabel>)   primary: <criterion or ->

Masked-stem prediction (written before options seen): <prediction | none>
Severities: C1 0  C2 0  C3 2  C4 0  C5 0  C6 1  C7 0  C8 0  C9 0  C10 2
Positive validity: A1 met | A2 unmet | A3 unmet

EVIDENCE
  C3 — <sources checked by name; what they all land on>
  C6 — <the leaking words; whether the masked prediction succeeded>
  C10 — reason articulated: <one sentence>
        counterfactual community: <different | slightly wrong>
        attested split: <named split | none found>
  <one line per criterion at 1 or 2; criteria at 0 need no line except C3/C9/C10, which are always
   written out per Pass 4>

REPAIR  (required for REJECT-CONSTRUCTION; optional and non-binding for REJECT-DOMAIN)
  1 criterion targeted: <Cn at severity n>
  2 minimal edit: <smallest change>
  3 restated item: stem + all four options as they would read
  4 predicted test outcome: <what Cn's own test returns afterwards>
  5 re-check: <criteria the repair could newly trip, and why it does not>
  6 label impact: mechanism <unchanged | CHANGED -> this is a new item, not a repair>
  7 what is lost: <REJECT-DOMAIN only>
```

### 4.3 `audit_summary.md` — battery level

Contains: counts by verdict and sublabel; the criterion-firing histogram (how many items tripped
each of C1-C10, which tells the lead whether T2's generator has a systematic defect or the domain is
simply standardised); the **Class-B rate** stated as a finding per MASTER_DESIGN S3 and B5; results
of B1-B5; the list of items surviving to the pilot gate; the list of FLAG items with the single
piece of evidence that would settle each; and a short statement of what this audit could not check
(see S6).

## 5. Reliability discipline

- Severities and evidence are recorded **before** the verdict is computed, and the verdict is derived
  mechanically from S3. No holistic verdicts.
- Pass 4 is the least reliable pass — C3 and C10 rest on the auditor's own knowledge of what real
  communities do, and that knowledge is neither complete nor current. Every C3 and C10 severity
  therefore carries a named-source field, so the lead can overrule a judgement by naming a source the
  auditor missed. An unsourced C3/C10 call caps at severity 1.
- Recommend to the lead: a second independent pass on Pass 4 only. It is cheap, it is where
  disagreement will concentrate, and per-criterion agreement between two auditors is itself
  reportable.
- The auditor does not repair items into acceptability. Repairs are proposals handed back; T2 owns
  the items and the lead owns the decision.

## 6. Known limits of this audit — must be carried into the summary

1. **Training-frequency attractors.** An option may be arbitrary for humans yet strongly attractored
   for language models by corpus frequency. Such an item looks perfectly valid on every criterion
   here and still produces convergence that is a shared-corpus artefact rather than a convention.
   No a-priori reading test detects this.
2. **Common-cause confound.** Even a flawless item cannot separate *convergence* from *shared
   training data*. That is a study-level threat the rubric cannot touch, and it bears on the
   interpretation of any Stage 1 similarity result.
3. **Auditor knowledge cutoff.** Judgements about what the ecosystem has standardised (C3) reflect
   the auditor's knowledge, not a corpus measurement, and cannot be refreshed without network access.
   A locus that was live two years ago may have been settled by a formatter release since.
4. **Battery-level cue structure.** Position balance, stem templating, and priming across the item
   sequence produce cues no per-item pass can see. B2-B4 are a partial defence only.
5. **Elicitation artefacts.** Answer-format effects, refusal behaviour, and self-consistency pressure
   sit in the prompt and the runner, not the item, and are outside this rubric's scope.
6. **Post-hoc undecidability.** Neither this audit nor the pilot data can distinguish an item that
   collapses because it is *right* (C10) from one that collapses because it is *conventional*. That
   asymmetry is the entire reason the rubric is a-priori, and it means the pilot gate can retire bad
   items but can never certify good ones.
7. **Single-auditor variance.** One reviewer, no reliability statistic. See S5.
