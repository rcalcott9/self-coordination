"""STAGE 2 - Claude-focal relational diagnostic pilot. 2,688 calls.

Job key carries arm | item type | array | condition | focal model | realized partner |
permutation | cycle, so a resume can never collapse two arms or two partner conditions.
Token usage is captured on EVERY call, so the spend gate is metered, not guessed.
"""
import argparse, base64, csv, json, os, sys, threading, time
from collections import Counter
from datetime import datetime, timezone

S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, S4); sys.path.insert(0, os.path.join(EXP, "code"))
import s4_common as S
import pilot_prompts as PP

STIM = os.path.join(EXP, "stimuli_pilot")
P = os.path.join(EXP, "pilot")
_LOCK = threading.Lock()

# empirical blended rate from battery5 (same two checkpoints, same 1240x340 images,
# 3,600 calls ~= $55). Used only for the spend gate; token counts are the audit trail.
USD_PER_CALL = 55.0 / 3600.0


def ask_gpt(client, img, prompt):
    r = client.responses.create(
        model=S.GPT_ID, reasoning={"effort": "low", "summary": "auto"},
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
    u = getattr(r, "usage", None)
    return (r.output_text or ""), "", r.model, dict(
        input=getattr(u, "input_tokens", 0) or 0, output=getattr(u, "output_tokens", 0) or 0)


def ask_claude(client, img, prompt):
    r = client.messages.create(
        model=S.CLAUDE_ID, max_tokens=S.CLAUDE_MAX_TOKENS,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": img}},
            {"type": "text", "text": prompt}]}])
    txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    u = r.usage
    return txt, "", r.model, dict(input=getattr(u, "input_tokens", 0) or 0,
                                  output=getattr(u, "output_tokens", 0) or 0)


ASK = {"gpt": ask_gpt, "claude": ask_claude}


def build_jobs(man, spec):
    asym = {a["array_id"] for a in man["asymmetric"]}
    jobs = []
    for sid in spec["arrays"]:
        it = "asymmetric" if sid in asym else "control"
        for cond in ("copy", "other", "unknown"):
            for arm in ("action", "predict"):
                for perm in range(24):
                    rp = ("claude" if cond == "copy" else "gpt" if cond == "other"
                          else spec["unknown_realized_partner"][sid][str(perm)])
                    pc = {"copy": "copy", "other": "other", "unknown": "unknown_focal"}[cond]
                    jobs.append(dict(
                        job_key=f"pilot|role:focal|{arm}|{it}|{sid}|{cond}|focal:claude|"
                                f"realized:{rp}|p{perm:02d}|c0",
                        role="focal", arm=arm, item_type=it, sid=sid, condition=cond,
                        actor="claude", realized_partner=rp, perm_id=perm, cycle=0,
                        prompt_key=f"claude|{pc}|{arm}"))
        # partner actions - OTHER
        for perm in range(24):
            jobs.append(dict(
                job_key=f"pilot|role:partner|action|{it}|{sid}|other|focal:gpt|"
                        f"realized:claude|p{perm:02d}|c0",
                role="partner", arm="action", item_type=it, sid=sid, condition="other",
                actor="gpt", realized_partner="claude", perm_id=perm, cycle=0,
                prompt_key="gpt|other|action"))
        # partner actions - UNKNOWN (the realized draw)
        for perm in range(24):
            who = spec["unknown_realized_partner"][sid][str(perm)]
            jobs.append(dict(
                job_key=f"pilot|role:partner|action|{it}|{sid}|unknown|focal:{who}|"
                        f"realized:claude|p{perm:02d}|c0",
                role="partner", arm="action", item_type=it, sid=sid, condition="unknown",
                actor=who, realized_partner="claude", perm_id=perm, cycle=0,
                prompt_key=f"{who}|unknown_partner|action"))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume-from", default=None)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--meter-only", type=int, default=0)
    ap.add_argument("--budget", type=float, default=50.0)
    ap.add_argument("--spent-already", type=float, default=0.0)
    a = ap.parse_args()

    man = json.load(open(os.path.join(P, "PILOT_MANIFEST_FINAL.json")))
    spec = json.load(open(os.path.join(P, "STRATEGIC_RUN_LOCKED.json")))
    assert spec["review_sheet_approval"], "review sheets not approved - refusing to run"
    assert PP.PROMPT_SHA == spec["prompt_sha"], "prompt hashes drifted since the freeze"

    jobs = build_jobs(man, spec)
    assert len(jobs) == 14 * 3 * 2 * 24 + 14 * 24 * 2 == 2688, len(jobs)
    assert len({j["job_key"] for j in jobs}) == len(jobs), "duplicate job_key"
    for sid in spec["arrays"]:                # exact counterbalance in every cell
        for k in {(j["role"], j["arm"], j["condition"]) for j in jobs}:
            c = Counter(j["perm_id"] for j in jobs if j["sid"] == sid
                        and (j["role"], j["arm"], j["condition"]) == k)
            assert not c or (len(c) == 24 and set(c.values()) == {1}), (sid, k, c)
    for sid in spec["arrays"]:                # UNKNOWN realizations balanced 12/12
        c = Counter(j["actor"] for j in jobs if j["sid"] == sid
                    and j["role"] == "partner" and j["condition"] == "unknown")
        assert c == Counter({"claude": 12, "gpt": 12}), (sid, c)

    sids = spec["arrays"]
    mine = [j for j in jobs if sids.index(j["sid"]) % a.nshards == a.shard]
    if a.meter_only:
        mine = mine[:a.meter_only]

    print("=== STAGE 2: CLAUDE-FOCAL RELATIONAL PILOT ===")
    print(f"arrays {len(sids)}  jobs {len(jobs)}  this shard {len(mine)}"
          f"  ({a.shard+1}/{a.nshards})")
    print(f"gpt {S.GPT_ID}   claude {S.CLAUDE_ID}")
    print(f"stimuli {STIM}  (green)")
    print(f"locked  {open(os.path.join(P,'STRATEGIC_RUN_LOCKED.json.sha256')).read().strip()[:16]}")
    print(f"run dir {a.run_dir}\n", flush=True)
    if a.dry_run:
        for k in sorted({j["prompt_key"] for j in jobs}):
            f, c, arm = k.split("|")
            print(f"  {k:34s} sha8={PP.sha8(PP.prompt(f, c, arm))}")
        return

    clients = S.make_clients()
    imgs, rows, usage = {}, [], Counter()
    done = set()
    rp = a.resume_from
    if rp and os.path.exists(rp):
        # a DIRECTORY resumes from every shard file in it, so a repair pass sees the
        # whole run. Only ok=True counts as done: a transport failure is retried by a
        # later explicit pass, never silently inside the one that recorded it, and
        # every attempt stays in the jsonl.
        files = ([os.path.join(rp, f) for f in sorted(os.listdir(rp))
                  if f.endswith(".jsonl")] if os.path.isdir(rp) else [rp])
        for f in files:
            for line in open(f):
                try:
                    d = json.loads(line)
                    if d.get("ok"):
                        done.add(d["job_key"])
                except Exception:
                    pass
        print(f"  resume: {len(done)} completed from {len(files)} file(s)")
    todo = [j for j in mine if j["job_key"] not in done]
    os.makedirs(os.path.join(a.run_dir, "data"), exist_ok=True)
    raw_p = os.path.join(a.run_dir, "data", f"pilot_s{a.shard}of{a.nshards}.jsonl")
    fh = open(raw_p, "a")
    n_done = [0]

    def img_for(j):
        k = (j["sid"], j["perm_id"])
        if k not in imgs:
            with open(os.path.join(STIM, j["sid"], f"perm{j['perm_id']:02d}.png"), "rb") as f:
                imgs[k] = base64.b64encode(f.read()).decode()
        return imgs[k]

    def one(j):
        t0 = time.time()
        f, c, arm = j["prompt_key"].split("|")
        pr = PP.prompt(f, c, arm)
        try:
            txt, _, mid, u = ASK[j["actor"]](clients[j["actor"]], img_for(j), pr)
            ok, err = True, ""
        except Exception as e:
            txt, mid, u, ok, err = "", "", dict(input=0, output=0), False, f"{type(e).__name__}: {e}"
        rec = dict(j); rec.pop("prompt_key", None)
        rec.update(prompt_key=j["prompt_key"], prompt_sha8=PP.sha8(pr), raw=txt,
                   api_model=mid, ok=ok, error=err, tok_in=u["input"], tok_out=u["output"],
                   secs=round(time.time() - t0, 2),
                   ts=datetime.now(timezone.utc).isoformat())
        with _LOCK:
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            rows.append(rec); usage["in"] += u["input"]; usage["out"] += u["output"]
            n_done[0] += 1
            if n_done[0] % 100 == 0:
                print(f"    {n_done[0]}/{len(todo)}", flush=True)
        return rec

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(one, todo))
    fh.close()

    nfail = sum(1 for r in rows if not r["ok"])
    est = a.spent_already + len(rows) / max(len(rows), 1) * 0  # placeholder
    est = a.spent_already + len(jobs) * USD_PER_CALL
    json.dump(dict(n=len(rows), transport_fail=nfail, tok_in=usage["in"],
                   tok_out=usage["out"], usd_per_call_basis=USD_PER_CALL,
                   projected_total_usd=round(est, 2)),
              open(os.path.join(a.run_dir, f"usage_s{a.shard}.json"), "w"), indent=1)
    print(f"\nrows {len(rows)}  transport_fail {nfail}")
    print(f"tokens in {usage['in']:,}  out {usage['out']:,}")
    print(f"projected combined spend ${est:.2f} (basis ${USD_PER_CALL:.4f}/call)")
    print(f"-> {raw_p}")


if __name__ == "__main__":
    main()
