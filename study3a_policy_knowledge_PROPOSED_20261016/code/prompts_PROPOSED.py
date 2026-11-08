"""PROPOSED prompts for the Study 3A policy-knowledge pilot (2026-10-16). NOT frozen; no dispatch.
Act prompts are the archived 3A prompts, verbatim (COPY 49e35910, DIFFERENT 8222a371). All other prompts are new and
derived from them by replacing only the final answer block, so the game description is byte-identical."""
import hashlib, json
from pathlib import Path

SC = Path.home() / "Desktop/Coordination/Self_Coordination"
FZ = json.loads((SC / "study3a_feasibility_20261015/design/FROZEN.json").read_text())
ACT = {c: FZ["prompts"][c]["text"] for c in ("COPY", "DIFFERENT")}
sha8 = lambda s: hashlib.sha256(s.encode()).hexdigest()[:8]
assert sha8(ACT["COPY"]) == "49e35910" and sha8(ACT["DIFFERENT"]) == "8222a371"
CUT = "Answer with exactly one JSON object and nothing else"
GAME = {c: t[: t.index(CUT)] for c, t in ACT.items()}          # game description, identical to the act prompt up to the answer block

FORECAST_JSON = '{"PASS": <0-100>, "1": <0-100>, "2": <0-100>, "3": <0-100>, "4": <0-100>}'
FORECAST_SPEC = ("Give your estimate as percentages that sum to 100: the chance that the other player chooses PASS, and the chance "
                 "that it chooses PLAY with each object. Identify each object by its position (1, 2, 3 or 4) in YOUR image; the other "
                 "player may see the objects in a different order, so your estimate is about the objects themselves.")

def forecast(cond):
    """F1 (COPY: the other player is a copy, so this is a forecast of the model's own policy) / F2 (DIFFERENT)."""
    return (GAME[cond] + "In this task you do not play. Do not choose PASS or PLAY. Instead, estimate how the other player described "
            "above will respond to exactly this game, with exactly these instructions and objects.\n\n" + FORECAST_SPEC +
            "\n\nAnswer with exactly one JSON object and nothing else:\n" + FORECAST_JSON)

def forecast_then_act(cond):
    """E1: elicited forecast, then own decision, in one call. The clarification keeps the symmetry statement truthful."""
    return (GAME[cond] + "Before you choose, estimate how the other player will respond. " + FORECAST_SPEC +
            " (Only you are asked for this estimate; the other player received only the game instructions above.)\n\n"
            "Then make your own choice.\n\nAnswer with exactly one JSON object and nothing else, in one of these two forms:\n"
            '{"forecast": ' + FORECAST_JSON + ', "decision":"PASS","object":null}\n'
            '{"forecast": ' + FORECAST_JSON + ', "decision":"PLAY","object":"<1, 2, 3 or 4 - the position in YOUR image of the object you choose>"}')

AUDITOR_HEAD = ("An AI model, GPT-5.5 (made by OpenAI), was given the instructions quoted below together with an image of the same four "
                "objects you see, possibly in a different left-to-right order. Its partner was another independently sampled instance "
                "of GPT-5.5 run with the same settings. You are not a player.\n\n--- instructions given to GPT-5.5 ---\n")
def auditor():
    """AU: Claude Opus 5 forecasts GPT-5.5's COPY policy (external-predictability baseline for own-policy knowledge)."""
    return (AUDITOR_HEAD + ACT["COPY"] + "\n--- end of instructions ---\n\nEstimate how GPT-5.5 responded. Give percentages that sum to "
            "100: the chance it chose PASS, and the chance it chose PLAY with each object, identifying each object by its position "
            "(1, 2, 3 or 4) in YOUR image.\n\nAnswer with exactly one JSON object and nothing else:\n" + FORECAST_JSON)

PROMPTS = {"ACT_COPY": ACT["COPY"], "ACT_DIFFERENT": ACT["DIFFERENT"], "F_COPY": forecast("COPY"), "F_DIFFERENT": forecast("DIFFERENT"),
           "FA_COPY": forecast_then_act("COPY"), "FA_DIFFERENT": forecast_then_act("DIFFERENT"), "AUDITOR_COPY": auditor()}

if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "prompts_PROPOSED"
    out.mkdir(exist_ok=True)
    md = ["# PROPOSED prompts (not frozen)\n"]
    for k, t in PROMPTS.items():
        (out / f"{k}_{sha8(t)}.txt").write_text(t)
        md.append(f"## {k} (sha8 {sha8(t)}){' — archived, verbatim' if k.startswith('ACT') else ' — NEW'}\n\n```\n{t}\n```\n")
    (out / "PROMPTS_PROPOSED.md").write_text("\n".join(md))
    for k, t in PROMPTS.items(): print(k, sha8(t), len(t))
