"""Bottom-row tables for the 2x3 figure, combining frontier 1b (low + high reasoning) and the Qwen crossed study.

  data/crossed_prediction_cells_all.csv  every predictor x target cell, all columns/settings (long)
  data/self_advantage_by_column.csv      one row per figure column x setting x item:
      D_self_target = (comparator -> column model) - (column model -> itself)   [target-specific self advantage]
      D_pooled      = study's pooled self-minus-cross advantage for that item
  Scale note: frontier Brier is over 4 options, Qwen over 2 (expected Brier ranges 0-2 in both, chance levels differ).
"""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(os.path.dirname(HERE), "data")
QX = os.path.expanduser("~/Desktop/Superrationality/Stag/qwen_crossed_prediction_20261009/analysis")
rd = lambda p: list(csv.DictReader(open(p)))

cells = []
for r in rd(os.path.join(D, "crossed_prediction_cells.csv")):
    cells.append(dict(column_pair="GPT-5.5 x Claude Opus 5", setting=r["setting"], array=r["array"], family=r["family"],
                      stratum=r["stratum"], sample=r["sample"], predictor=r["predictor"], target=r["target"], self_cell=r["self_cell"],
                      n_options=4, n_pred_parsed=r["n_pred_parsed"], brier_mean=r["brier_mean"], brier_sd=r["brier_sd"],
                      logscore_mean=r["logscore_mean"], n_scoring_draws_target=r["n_scoring_draws_target"],
                      target_dist_fresh=r["target_dist_fresh"]))
for r in rd(os.path.join(QX, "crossed_prediction_cells.csv")):
    cells.append(dict(column_pair="Qwen step-316 x Qwen base", setting=r["setting"], array=r["array"], family=r["family"],
                      stratum=r["stratum"], sample=r["sample"], predictor=r["predictor"], target=r["target"], self_cell=r["self_cell"],
                      n_options=2, n_pred_parsed=r["n_pred_parsed"], brier_mean=r["brier_mean"], brier_sd=r["brier_sd"],
                      logscore_mean=r["logscore_mean"], n_scoring_draws_target=r["n_scoring_draws_target"],
                      target_dist_fresh=r["target_dist_fresh"]))
with open(os.path.join(D, "crossed_prediction_cells_all.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(cells[0])); w.writeheader(); w.writerows(cells)

rows = []
for r in rd(os.path.join(D, "self_advantage_items.csv")):
    for col, key, comp in (("gpt", "D_target_gpt", "Claude Opus 5"), ("claude", "D_target_opus", "GPT-5.5")):
        rows.append(dict(column=col, setting=r["setting"], array=r["array"], family=r["family"], stratum=r["stratum"],
                         sample=r["sample"], comparator=comp, n_options=4, D_self_target=r[key], D_pooled=r["D_pooled"],
                         tvd_fresh=r["tvd_fresh"], same_modal=r["same_modal"]))
for r in rd(os.path.join(QX, "self_advantage_items.csv")):
    rows.append(dict(column="qwen", setting=r["setting"], array=r["array"], family=r["family"], stratum=r["stratum"],
                     sample=r["sample"], comparator="Qwen3.5-397B-A17B base (untuned)", n_options=2,
                     D_self_target=r["D_target_focal_s316"], D_pooled=r["D_pooled"], tvd_fresh=r["tvd_fresh"],
                     same_modal=r["same_modal"]))
with open(os.path.join(D, "self_advantage_by_column.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
import collections
print("cells", collections.Counter((c["column_pair"], c["setting"]) for c in cells))
print("by_column", collections.Counter((r["column"], r["setting"]) for r in rows))
