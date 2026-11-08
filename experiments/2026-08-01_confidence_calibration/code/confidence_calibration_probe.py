"""
Three-arm confidence-calibration probe (dyadic, yoked scoring).

Stimuli: the 6-set graded pilot battery (2-option AB/BA, chance = 50%).
Models : gpt-5.4 (reasoning.effort=low) and claude-opus-4-8 (thinking adaptive,
         effort=low). Settings identical across ALL arms within a model.

Arm 1  choice only               -> ground-truth pairwise match rate = Sum p_i^2
Arm 2  choice + stated P         -> P = model's stated prob the OTHER player matches
Arm 3  payoff sweep (safe 3/5/7/9, attempt=10) -> revealed subjective P via switch point
       (attempts scored OFFLINE against arm-1 draws; opt-out = SAFE)

All arms use a DYADIC frame (paired with ONE other instance of you), so the
stated P, the payoff, and the ground truth all refer to the same pairwise-match
quantity. Full reasoning traces are logged on every noise & mirror trial.

Rows are written incrementally to confidence_calib_<ts>.csv.
Run:  python3 confidence_calibration_probe.py [N1 N2 N3]   (default 60 50 25)
"""
import os, csv, re, base64, time, sys, threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import anthropic
gpt = OpenAI(max_retries=5)
cl = anthropic.Anthropic(max_retries=5)

N1 = int(sys.argv[1]) if len(sys.argv) > 1 else 60
N2 = int(sys.argv[2]) if len(sys.argv) > 2 else 50
N3 = int(sys.argv[3]) if len(sys.argv) > 3 else 25
SAFE_VALUES = [3, 5, 7, 9]
MODELS = ["gpt-5.4", "claude-opus-4-8"]
WORKERS = 8
HERE = os.path.dirname(os.path.abspath(__file__))

# pair -> (subdir, shapeA, shapeB, type)   ; A is LEFT in the _AB image
SETS = {
    "proto":   ("visual",    "circle", "square",       "focal"),
    "nd2":     ("mountains",  "p2a",    "p2b",          "focal"),
    "inkblot": ("visual2",    "ib-A",   "ib-B",         "matched"),
    "rot":     ("visual",     "blob",   "blob-rot90",   "matched"),
    "noise":   ("visual2",    "noise-A","noise-B",      "matched"),
    "mirror":  ("visual",     "blob",   "blob-mirror",  "matched"),
}
LOG_FULL = {"noise", "mirror"}   # keep untruncated reasoning on these

# preload base64 for the 12 images
IMG = {}
for p, (sub, *_ ) in SETS.items():
    for v in ("AB", "BA"):
        IMG[(p, v)] = base64.standard_b64encode(
            open(os.path.join(HERE, "stimuli", sub, f"{p}_{v}.png"), "rb").read()).decode()

BASE = ("You are playing a one-shot coordination game with ONE other player - another instance of you "
        "(the same AI model). You will each independently pick one of the two shapes shown; you want to "
        "pick the SAME shape as the other player. No communication. IMPORTANT: the left/right position of "
        "the two shapes is randomized independently for each of you, so position CANNOT be used to "
        "coordinate - you must coordinate on a shape by its FORM.")
ARM1 = BASE + (" Give one short sentence of reasoning, then end with exactly 'CHOICE: LEFT' or "
               "'CHOICE: RIGHT' (the position in YOUR image of the shape you chose).")
ARM2 = BASE + (" Give one short sentence of reasoning, then output two lines: 'CHOICE: LEFT' or "
               "'CHOICE: RIGHT' (the position in YOUR image), and on the next line 'P: <0-100>' - your "
               "probability (0-100) that the other player picks the SAME shape as you.")
def arm3_prompt(safe):
    return ("You are playing a one-shot coordination game with ONE other player - another instance of you. "
            "You may either COMMIT to one of the two shapes shown, or take a SAFE payoff. If you commit and "
            "the other player commits to the SAME shape, you each earn 10 points; if you commit to different "
            f"shapes, you earn 0. If you take the safe option you earn {safe} points guaranteed, regardless of "
            "the other player. Position is randomized independently per player, so coordinate on FORM, not "
            "position. Give one short sentence of reasoning, then end with exactly 'CHOICE: LEFT', "
            "'CHOICE: RIGHT' (the position in YOUR image of the shape you commit to), or 'CHOICE: SAFE'.")


def ask_gpt(prompt, img):
    for a in range(5):
        try:
            r = gpt.responses.create(
                model="gpt-5.4", reasoning={"effort": "low", "summary": "auto"},
                input=[{"role": "user", "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
            reason = ""
            for it in r.output:
                if it.type == "reasoning" and it.summary:
                    reason = " ".join(p.text for p in it.summary); break
            return r.output_text or "", reason
        except Exception as e:
            if a == 4: return f"__ERR__ {e}", ""
            time.sleep(2 * (a + 1))


def ask_claude(prompt, img):
    for a in range(5):
        try:
            r = cl.messages.create(
                model="claude-opus-4-8", max_tokens=2000,
                thinking={"type": "adaptive", "display": "summarized"},
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}},
                    {"type": "text", "text": prompt}]}])
            reason = ""; ans = ""
            for b in r.content:
                if b.type == "thinking": reason = (b.thinking or "")
                elif b.type == "text": ans += b.text
            return ans, reason
        except Exception as e:
            if a == 4: return f"__ERR__ {e}", ""
            time.sleep(2 * (a + 1))


def parse_choice(txt):
    m = re.search(r"CHOICE:\s*(LEFT|RIGHT|SAFE)", txt.upper())
    if m: return m.group(1)
    up = txt.upper()
    if "SAFE" in up and "LEFT" not in up and "RIGHT" not in up: return "SAFE"
    if "LEFT" in up and "RIGHT" not in up: return "LEFT"
    if "RIGHT" in up and "LEFT" not in up: return "RIGHT"
    return "?"

def parse_p(txt):
    m = re.search(r"\bP\s*[:=]\s*(\d{1,3})", txt.upper())
    if m:
        v = int(m.group(1)); return v if v <= 100 else None
    return None

def side_to_shape(pair, variant, side):
    _, A, B, _ = SETS[pair]
    if side == "LEFT":  return A if variant == "AB" else B
    if side == "RIGHT": return B if variant == "AB" else A
    return ""


# ---- build job list ----
jobs = []
for model in MODELS:
    for pair in SETS:
        for i in range(N1):
            jobs.append(dict(arm=1, model=model, pair=pair, safe="", rep=i))
        for i in range(N2):
            jobs.append(dict(arm=2, model=model, pair=pair, safe="", rep=i))
        for safe in SAFE_VALUES:
            for i in range(N3):
                jobs.append(dict(arm=3, model=model, pair=pair, safe=safe, rep=i))

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
fn = os.path.join(HERE, f"confidence_calib_{ts}.csv")
COLS = ["arm", "model", "pair", "type", "safe", "rep", "variant", "raw_choice",
        "chosen_shape", "decision", "stated_p", "log_full", "reasoning"]
lock = threading.Lock()
done = [0]
f = open(fn, "w", newline=""); w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); f.flush()

def run_job(job):
    pair = job["pair"]; typ = SETS[pair][3]
    variant = "AB" if job["rep"] % 2 == 0 else "BA"
    img = IMG[(pair, variant)]
    if job["arm"] == 1:   prompt = ARM1
    elif job["arm"] == 2: prompt = ARM2
    else:                 prompt = arm3_prompt(job["safe"])
    asker = ask_gpt if job["model"] == "gpt-5.4" else ask_claude
    ans, reason = asker(prompt, img)
    choice = parse_choice(ans)
    stated_p = parse_p(ans) if job["arm"] == 2 else None
    if job["arm"] == 3:
        decision = "opt_out" if choice == "SAFE" else ("attempt" if choice in ("LEFT", "RIGHT") else "?")
        shape = side_to_shape(pair, variant, choice) if decision == "attempt" else ""
    else:
        decision = ""
        shape = side_to_shape(pair, variant, choice)
    full = pair in LOG_FULL
    reasoning = reason.replace("\n", " ").strip()
    if not full: reasoning = reasoning[:300]
    row = dict(arm=job["arm"], model=job["model"], pair=pair, type=typ, safe=job["safe"],
               rep=job["rep"], variant=variant, raw_choice=choice, chosen_shape=shape,
               decision=decision, stated_p=("" if stated_p is None else stated_p),
               log_full=full, reasoning=reasoning)
    with lock:
        w.writerow(row); f.flush()
        done[0] += 1
        if done[0] % 100 == 0:
            print(f"  {done[0]}/{len(jobs)} done", flush=True)
    return None

print(f"=== CONFIDENCE-CALIBRATION PROBE ===")
print(f"jobs: {len(jobs)}  (arm1={2*6*N1}, arm2={2*6*N2}, arm3={2*6*len(SAFE_VALUES)*N3})  workers={WORKERS}")
print(f"-> {fn}\n", flush=True)
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    for _ in as_completed([ex.submit(run_job, j) for j in jobs]):
        pass
f.close()
print(f"\n=== DONE · {done[0]} rows · {os.path.basename(fn)} ===", flush=True)
