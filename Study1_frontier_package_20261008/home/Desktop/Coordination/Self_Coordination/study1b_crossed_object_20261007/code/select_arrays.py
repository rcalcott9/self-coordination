"""Phase B: deterministic stratum selection from INDEPENDENT reference-choice distributions only.

  python code/select_arrays.py [--root DIR] [--use-existing-frame] [--fake-screen-from-frame A,B,...]

Inputs: Phase-A screening draws (runs/screen/*.csv, each row checked against FROZEN_SCREEN's
hash). With --use-existing-frame, existing frame-configuration counts (VIS-FRAME-41, same prompt
and settings) are ADDED for arrays that have them; the flag and the per-array source are recorded.
No prediction data are read, and the script refuses to run if any exist.

Strata (thresholds below are PLACEHOLDERS, to be filled from the inventory workstream before freezing):
  S1  opposing concentrated : both models concentrated, different modal shapes
  S2  concentrated/diffuse  : S2_G = GPT concentrated & Opus diffuse; S2_O = the reverse
  S3  shared-policy control : both concentrated on the same modal shape
Within a stratum, eligible arrays are ordered by a seeded hash of the array id (never by any
outcome or prediction quantity), capped per family, then truncated to the stratum quota.
Writes design/SELECTION.json + .sha256 once; it will not overwrite an existing selection.
"""
import argparse, csv, glob, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C                                                     # noqa: E402

CONFIG = dict(                                   # FINAL 2026-10-07 (from inventory workstream), fixed before screening
    conc_min_modal_share=0.75,                   # concentrated: modal share >= .75, unique mode
    diffuse_max_modal_share=0.50,                # diffuse: modal share <= .50
    s1_fallback_min_modal_share=0.70,            # S1 only: if < s1_min_eligible arrays qualify at .75, admit both >= .70, different modes
    s1_min_eligible=4,
    min_draws=24,
    quota={"S1": 8, "S2_G": 6, "S2_O": 8, "S3": 10},
    max_per_family={"S1": 2, "S2_G": 2, "S2_O": 2, "S3": 1},
    order_seed="S1B-SELECT-20261007",
    placeholder=False,
)


def wmm(c):
    n = sum(c); return sum(k * (k - 1) for k in c) / (n * (n - 1))


def classify(c, cfg):
    n = sum(c); mx = max(c)
    modal = [i for i, k in enumerate(c) if k == mx]
    conc = len(modal) == 1 and mx / n >= cfg["conc_min_modal_share"]
    diff = mx / n <= cfg["diffuse_max_modal_share"]
    loose = len(modal) == 1 and mx / n >= cfg["s1_fallback_min_modal_share"]
    return dict(n=n, counts=list(c), modal=modal[0] if len(modal) == 1 else None, modal_share=mx / n, loose=loose,
                wmm=wmm(c), concentrated=conc, diffuse=diff)


def stratum(g, o):
    if g["concentrated"] and o["concentrated"]:
        return "S1" if g["modal"] != o["modal"] else "S3"
    if g["concentrated"] and o["diffuse"]:
        return "S2_G"
    if o["concentrated"] and g["diffuse"]:
        return "S2_O"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=C.STUDY)
    ap.add_argument("--use-existing-frame", action="store_true")
    ap.add_argument("--fake-screen-from-frame", help="SELF-TEST ONLY: comma list; counts taken from frame CSV")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    if a.fake_screen_from_frame and root == os.path.abspath(C.STUDY):
        sys.exit("ABORT: fake selection may only be written to a temp --root, never the study folder")
    if any(sum(1 for _ in open(f)) > 1 for f in glob.glob(os.path.join(root, "runs", "main", "*.csv"))):
        sys.exit("ABORT: prediction/main data already exist; selection must precede them")
    out = os.path.join(root, "design", "SELECTION.json")
    if os.path.exists(out):
        sys.exit("ABORT: SELECTION.json already frozen; refusing to overwrite")

    counts, source = {}, {}
    mid = {m: C.MODELS[m]["model_id"] for m in C.MODELS}
    if a.fake_screen_from_frame:
        arrays = a.fake_screen_from_frame.split(",")
        screen_sha = "FAKE-SELFTEST"
    else:
        FS, screen_sha = C.load_frozen(os.path.join(root, "design", "FROZEN_SCREEN.json"))
        arrays = FS["candidates"]
        for f in sorted(glob.glob(os.path.join(root, "runs", "screen", "*.csv"))):
            for r in csv.DictReader(open(f)):
                if r["parse_ok"] != "1":
                    continue
                assert r["frozen_sha8"] == screen_sha, f"screen row from another freeze: {f}"
                assert r["model_match"] == "1"
                counts.setdefault((r["answerer"], r["array"]), [0] * 4)[int(r["canonical_choice"])] += 1
                source[(r["answerer"], r["array"])] = "screen"
    if a.use_existing_frame or a.fake_screen_from_frame:
        for r in csv.DictReader(open(C.FRAME_CSV)):
            for m, i in mid.items():
                if r["checkpoint_requested"] == i and r["parse_ok"] == "1" and r["array_id"] in arrays:
                    counts.setdefault((m, r["array_id"]), [0] * 4)[int(r["canonical_index"])] += 1
                    source[(m, r["array_id"])] = ("frame" if a.fake_screen_from_frame
                                                  else source.get((m, r["array_id"]), "") + "+frame")

    table, elig = {}, {k: [] for k in CONFIG["quota"]}
    for x in arrays:
        if any(sum(counts.get((m, x), [0])) < CONFIG["min_draws"] for m in mid):
            table[x] = dict(stratum=None, reason="insufficient draws"); continue
        g, o = classify(counts[("gpt", x)], CONFIG), classify(counts[("claude", x)], CONFIG)
        s = stratum(g, o)
        table[x] = dict(stratum=s, gpt=g, claude=o, source={m: source.get((m, x)) for m in mid})
        if s:
            elig[s].append(x)
    s1_fallback_used = False
    if len(elig["S1"]) < CONFIG["s1_min_eligible"]:
        s1_fallback_used = True
        for x, t in table.items():
            if t.get("stratum") is None and "gpt" in t and t["gpt"]["loose"] and t["claude"]["loose"] \
                    and t["gpt"]["modal"] != t["claude"]["modal"]:
                t["stratum"] = "S1"; t["s1_fallback"] = True; elig["S1"].append(x)
    chosen = {}
    for s, xs in elig.items():
        xs = sorted(xs, key=lambda x: hashlib.sha256(f"{CONFIG['order_seed']}|{s}|{x}".encode()).hexdigest())
        fam, pick = {}, []
        for x in xs:
            f = x.rsplit("_m", 1)[0]
            if fam.get(f, 0) >= CONFIG["max_per_family"][s]:
                continue
            fam[f] = fam.get(f, 0) + 1; pick.append(x)
            if len(pick) == CONFIG["quota"][s]:
                break
        chosen[s] = pick
    sel = dict(phase="select", config=CONFIG, screen_frozen_sha8=screen_sha,
               used_existing_frame=bool(a.use_existing_frame), s1_fallback_used=s1_fallback_used, self_test=bool(a.fake_screen_from_frame),
               n_eligible={s: len(v) for s, v in elig.items()}, selected=chosen,
               selected_flat=sorted({x for v in chosen.values() for x in v}),
               shortfall={s: CONFIG["quota"][s] - len(v) for s, v in chosen.items() if len(v) < CONFIG["quota"][s]},
               per_array=table, code_sha8=C.code_sha8(),
               rule="selection uses only reference-choice counts; ordering by seeded hash of array id")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    h = C.write_frozen(out, sel)
    print(f"SELECTION sha256 {h[:16]}  eligible {sel['n_eligible']}  selected "
          f"{ {s: len(v) for s, v in chosen.items()} }  shortfall {sel['shortfall']}")


if __name__ == "__main__":
    main()
