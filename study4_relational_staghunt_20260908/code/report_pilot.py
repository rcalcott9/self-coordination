"""Diagnostic report for the Claude-focal relational pilot."""
import json, os, sys

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(EXP, "pilot")


def ci(d, k):
    lo, hi = d[f"{k}_ci"]
    return f"[{lo:+.3f}, {hi:+.3f}]"


def excl0(d, k):
    lo, hi = d[f"{k}_ci"]
    return "yes" if (lo > 0 or hi < 0) else "no"


def main(run_dir):
    r = json.load(open(os.path.join(run_dir, "pilot_results.json")))
    man = json.load(open(os.path.join(P, "PILOT_MANIFEST_FINAL.json")))
    C, pa, ig = r["contrasts"], r["per_array"], r["integrity"]
    asym = [v for v in pa.values() if v["item_type"] == "asymmetric"]
    ctrl = [v for v in pa.values() if v["item_type"] == "control"]

    L = ["# Study 4 - Claude-focal relational diagnostic pilot", "",
         f"Run `{r['run_dir']}`.  Manifest sha `{r['manifest_sha'][:16]}`.  "
         f"Run spec sha `{r['run_sha'][:16]}`.", "",
         "8 confirmed asymmetric arrays (Claude focal, n=72 confirmation) and 6 "
         "independently validated shared-policy controls (n=24 validation). Three partner "
         "conditions x two arms x 24 permutations, each exactly once. Diagnostic pilot - "
         "exploratory, not confirmatory.", "",
         "## 1. Trial integrity", "",
         f"- rows {ig['n_rows']}, transport failures **{ig['transport_fail']}**",
         f"- action parse failures **{ig['parse_fail_action']}**, prediction parse "
         f"failures **{ig['parse_fail_predict']}**",
         f"- checkpoints on every row: `{ig['checkpoints']}`",
         f"- cells {ig['n_cells']} of {ig['expected_cells']} expected; incomplete cells: "
         f"**{ig.get('incomplete_cells') or 'none'}**",
         "- every cell holds all 24 permutations exactly once; job keys carry role, arm, "
         "item type, array, condition, focal model, realized partner, permutation and "
         "cycle, so no arm or condition can collapse on resume", "",
         "## 2. Action arm", "",
         "P(Claude's locked modal object), P(green), and coordination against "
         "independently measured partner actions. COPY coordination uses the "
         "bias-corrected estimator, which excludes self-pairs by construction.", "",
         "| item type | condition | P(Claude modal) | P(green) | coordination | E[payoff] |",
         "|---|---|---|---|---|---|"]
    for nm, g in (("asymmetric", asym), ("control", ctrl)):
        for c in ("copy", "other", "unknown"):
            k = f"act_{c}"
            L.append(f"| {nm} | {c.upper()} | "
                     f"{sum(x[k]['p_claude_modal'] for x in g)/len(g):.3f} | "
                     f"{sum(x[k]['p_green'] for x in g)/len(g):.3f} | "
                     f"{sum(x[k]['coord'] for x in g)/len(g):.3f} | "
                     f"{sum(x[k]['exp_payoff'] for x in g)/len(g):.2f} |")
    L += ["", "## 3. Prediction arm", "",
          "Mean probability mass Claude assigns to each object for the PARTNER's choice, "
          "and Brier against the independently measured partner action distribution "
          "(lower is better; 0.75 is the uniform-guess score at four options).", "",
          "| item type | condition | P(Claude modal) | P(GPT modal) | P(green) | entropy (bits) | Brier |",
          "|---|---|---|---|---|---|---|"]
    for nm, g in (("asymmetric", asym), ("control", ctrl)):
        for c in ("copy", "other", "unknown"):
            k = f"prd_{c}"
            L.append(f"| {nm} | {c.upper()} | "
                     f"{sum(x[k]['p_claude_modal'] for x in g)/len(g):.3f} | "
                     f"{sum(x[k]['p_gpt_modal'] for x in g)/len(g):.3f} | "
                     f"{sum(x[k]['p_green'] for x in g)/len(g):.3f} | "
                     f"{sum(x[k]['entropy_bits'] for x in g)/len(g):.3f} | "
                     f"{sum(x[k]['brier'] for x in g)/len(g):.3f} |")
    L += ["", "## 4. Primary contrasts and the interaction", "",
          "Cluster bootstrap over ARRAYS within item type (4,000 draws); arrays are the "
          "sampling unit for the item-type contrast. With 8 and 6 arrays these intervals "
          "are wide by construction - that is the honest precision of a pilot.", "",
          "| contrast | asymmetric | control | difference-in-differences | DiD CI | excludes 0 |",
          "|---|---|---|---|---|---|"]
    for name, d in C.items():
        p = d["point"]
        L.append(f"| `{name}` | {p['asym']:+.3f} {ci(d,'asym')} | "
                 f"{p['control']:+.3f} {ci(d,'control')} | **{p['did']:+.3f}** | "
                 f"{ci(d,'did')} | {excl0(d,'did')} |")
    L += ["", "## 5. Is it one array or one mechanism?", "",
          "Leave-one-out on the primary action contrast "
          "(`act_claude_modal_copy_minus_other`).", "",
          "| dropped | DiD | CI | excludes 0 |", "|---|---|---|---|"]
    for k, d in r["robustness"].items():
        if k == "drop_unmatched_numerosity":
            continue
        L.append(f"| {k.split(':',1)[1]} | {d['point']['did']:+.3f} | {ci(d,'did')} | "
                 f"{excl0(d,'did')} |")
    L += ["", "### The unmatched-numerosity re-run", "",
          "The control set has no numerosity array (`m5_numerosity_v6` failed validation), "
          "so the two numerosity asymmetric arrays are unmatched. Every contrast re-run "
          "with numerosity dropped from BOTH sides:", "",
          "| contrast | DiD (all) | DiD (no numerosity) | CI | excludes 0 |",
          "|---|---|---|---|---|"]
    for name, d in r["robustness"]["drop_unmatched_numerosity"].items():
        L.append(f"| `{name}` | {C[name]['point']['did']:+.3f} | "
                 f"**{d['point']['did']:+.3f}** | {ci(d,'did')} | {excl0(d,'did')} |")
    # ---- the split that decides what "asymmetric" means here ----
    comp = [v for v in asym if pa[v["array_id"]]["gpt_modal"] != v["claude_modal"]]
    diff = [v for v in asym if pa[v["array_id"]]["gpt_modal"] == v["claude_modal"]]
    L += ["", "## 5b. Competing convention vs merely-diffuse GPT", "",
          "In only " + str(len(comp)) + " of the 8 asymmetric arrays does GPT hold a "
          "DIFFERENT modal object from Claude (`" +
          "`, `".join(v["array_id"] for v in comp) + "`). In the other " + str(len(diff)) +
          " GPT's modal coincides with Claude's and is merely weaker/diffuse. If the "
          "relational effect is real, it should be concentrated in the competing-convention "
          "arrays, where switching partner actually changes the best response.", "",
          "| subset | n | act P(mod) COPY | act P(mod) OTHER | COPY-OTHER | act P(green) OTHER-COPY |",
          "|---|---|---|---|---|---|"]
    for nm, g in (("competing convention", comp), ("GPT diffuse, same modal", diff),
                  ("control", ctrl)):
        if not g:
            continue
        L.append(f"| {nm} | {len(g)} | "
                 f"{sum(x['act_copy']['p_claude_modal'] for x in g)/len(g):.3f} | "
                 f"{sum(x['act_other']['p_claude_modal'] for x in g)/len(g):.3f} | "
                 f"{sum(x['act_copy']['p_claude_modal']-x['act_other']['p_claude_modal'] for x in g)/len(g):+.3f} | "
                 f"{sum(x['act_other']['p_green']-x['act_copy']['p_green'] for x in g)/len(g):+.3f} |")

    L += ["", "## 6. Array-level effects", "", "| array | type | mech | "
          "act P(mod) COPY/OTHER/UNK | act P(green) COPY/OTHER/UNK | prd P(mod) COPY/OTHER/UNK |",
          "|---|---|---|---|---|---|"]
    for sid in sorted(pa):
        v = pa[sid]
        a = [v[f"act_{c}"] for c in ("copy", "other", "unknown")]
        d = [v[f"prd_{c}"] for c in ("copy", "other", "unknown")]
        L.append(f"| `{sid}` | {v['item_type'][:4]} | {v['mechanism']} | "
                 + " / ".join(f"{x['p_claude_modal']:.2f}" for x in a) + " | "
                 + " / ".join(f"{x['p_green']:.2f}" for x in a) + " | "
                 + " / ".join(f"{x['p_claude_modal']:.2f}" for x in d) + " |")
    open(os.path.join(run_dir, "PILOT_DIAGNOSTIC_REPORT.md"), "w").write("\n".join(L) + "\n")
    print(f"-> {os.path.join(run_dir, 'PILOT_DIAGNOSTIC_REPORT.md')}")
    return r


if __name__ == "__main__":
    main(sys.argv[1])
