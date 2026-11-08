# Errata: Study 1 asset-audit flags (2026-10-10)

Source: `~/Downloads/Study1_Asset_Audit_and_Pilots.pdf`, §7.2 and §10. Each correction below was checked against the files on 2026-10-10. No API calls were made.

**Policy for this note:** frozen and historical files are **not edited**. Corrected values go into the paper text, and this note records each correction.

| # | flag | verified finding | correction for the paper |
|---|---|---|---|
| 1 | "GPT's audit of Claude r = 0.07" (`self-coordination-diary.md:1061`; `coordination_studies_report.pdf`) | The recomputed value is **−.073**; the minus sign was dropped. | Report r = −.07. The legacy diary line is left as written; this note supersedes it. |
| 2 | Opus headline, partner drop and identity penalty presented together | The headline **.960 / .660, d′ 1.322** comes from the **thinking-disabled** COPY cell (`parallel_disabled_20260912_191726`). The partner drop (**+.155**) and penalty use the **adaptive** 2×2 cells. The adaptive COPY-low cell is **.967 / .777, d′ 1.056**. | Report each number with its configuration and never pool across configurations. Study 2 uses the adaptive 2×2 only. The disabled cell is a separate single-cell result. |
| 3 | 20 coded traces missing (5,341 in the corpus, 5,321 coded) | **Explained.** The coder ran over 5,279 unique texts in batches of 20 (`code_traces.py`, `BATCH = 20`). One batch, unique ids **2420–2439**, came back unresolved (`None` in `codes_pp.json`: 20 unresolved in total). `analyze.py` drops `None` codes. The affected rows are Opus 8 (`parallel_191415` 5, `pp_same_adaptive_effhigh` 2, `pp_different_adaptive_effhigh` 1) and Qwen 12 (`qwen_pp2x2_20260912_173541`). | Report coded n = 5,321 of 5,341 and give the reason: one coder batch failed and was excluded, not imputed. Recoding the batch would cost one call; it is not needed. |
| 4 | `trace_prereg/FROZEN_SHA256.txt` lists two hashes each for `codebook_two_facet.md` and `corpus_studies12.csv` | Confirmed. The current files match only the **second** hashes (`3f2ee316…`, `23c7a118…`). All three files carry timestamps within 18:23–18:24 on 2026-09-12. The first versions were not preserved, so what changed cannot be recovered. | Amendment note: "the codebook and corpus were re-frozen within one minute of the first freeze; the first versions were not preserved; all coding used the re-frozen files." Label trace analyses exploratory. |
| 5 | Qwen D11, "step 316 at lr ≈ 3.5e-5" (`plunkett_qwen/SELF_INTERPRETATION_RESULT.md:73`) | The cosine schedule recomputes to **2.78e-5**, which is also the lr the continuation pilot used. | Report lr ≈ 2.78e-5. |
| 6 | Qwen Study 1 AUC .776 | This is the **scenario-level** AUC. Trial-level AUC equals accuracy, .587. | Label it "scenario-level AUC". |

These flags are outside the paper's Study 1–3 claims and are left as documented in the audit: Opus PLAY/PASS prompts have no logged hash, stale `FROZEN_PARALLEL` api_settings, `prompt_sha8` is missing from the pooled exports, and the other Qwen documentation items. The paper's methods must still state that the Opus PLAY/PASS cells are "attributable but not hash-verified" (`trace_prereg/PROVENANCE_AUDIT.md`).
