"""
The four historical rungs, with each model's OWN native provider settings.

SETTINGS ARE NOT IDENTICAL ACROSS THE LADDER AND ARE NOT PRETENDED TO BE.
There is a hard inference-surface boundary in both families, verified live by
ladder_probe.py:

    OpenAI     gpt-4o-2024-05-13      NO reasoning parameter  -> temperature=1.0
               gpt-5-2025-08-07       reasoning.effort=low    (rejects temperature)
    Anthropic  claude-opus-4-5-...    400 "adaptive thinking is not supported on this
                                      model" -> temperature=1.0
               claude-opus-4-6        thinking adaptive + output_config.effort=low

No chain-of-thought scaffolds or extra reasoning prompts are added to older models to
equalise them - the prompt is byte-identical across every rung (sha8 3003ae1b).

PRE-REGISTERED LIMITATION (spec §8, quoted verbatim in every report):
"Historical comparisons are partially confounded by changes in provider inference
surfaces. GPT-4o and Opus 4.5 do not expose the same reasoning controls as later
models, so any sharp discontinuity at these boundaries cannot by itself establish
capability emergence."
"""
import os

LADDER = [
    dict(key="gpt4o", provider="openai", family="GPT-4o", released="2024-05",
         model_id="gpt-4o-2024-05-13", display="GPT-4o",
         gpt_surface="temperature", claude_surface=None, order=1),
    dict(key="gpt5", provider="openai", family="GPT-5", released="2025-08",
         model_id="gpt-5-2025-08-07", display="GPT-5",
         gpt_surface="reasoning", claude_surface=None, order=2),
    dict(key="opus45", provider="anthropic", family="Opus 4.5", released="2025-11",
         model_id="claude-opus-4-5-20251101", display="Claude Opus 4.5",
         gpt_surface=None, claude_surface="temperature", order=1),
    dict(key="opus46", provider="anthropic", family="Opus 4.6", released="2026-02",
         model_id="claude-opus-4-6", display="Claude Opus 4.6",
         gpt_surface=None, claude_surface="thinking", order=2),
    # Added 2026-08-15 to fill the Anthropic gap: 4.6 failed the competence gate and
    # 4.8 is the next observed rung, so the line rests on only two points.
    dict(key="opus47", provider="anthropic", family="Opus 4.7", released="2026-04",
         model_id="claude-opus-4-7", display="Claude Opus 4.7",
         gpt_surface=None, claude_surface="thinking", order=3),
]

# Already collected; never rerun. Paths are the source projects.
ANCHORS = [
    dict(key="gpt54", provider="openai", display="GPT-5.4", released="2026-03", order=3,
         model_id="gpt-5.4-2026-03-05", exp="policy_specific_self_coordination_20260812_1401/"
         "replication_5_4_4_8", role="gpt"),
    dict(key="gpt55", provider="openai", display="GPT-5.5", released="2026-04", order=4,
         model_id="gpt-5.5-2026-04-23",
         exp="policy_specific_self_coordination_20260812_1401", role="gpt"),
    dict(key="opus48", provider="anthropic", display="Claude Opus 4.8", released="2026-05",
         order=3, model_id="claude-opus-4-8",
         exp="policy_specific_self_coordination_20260812_1401/replication_5_4_4_8",
         role="claude"),
    dict(key="opus5", provider="anthropic", display="Claude Opus 5", released="2026-07",
         order=4, model_id="claude-opus-5",
         exp="policy_specific_self_coordination_20260812_1401", role="claude"),
]

ROOT = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(os.path.dirname(ROOT),
                    "policy_specific_self_coordination_20260812_1401", "code")


def env_for(m):
    """Environment for one rung. The unused provider keeps a valid default."""
    e = dict(os.environ)
    e["PSC_EXP_DIR"] = os.path.join(ROOT, "models", m["key"])
    e["PSC_TEMPERATURE"] = "1.0"
    if m["provider"] == "openai":
        e["PSC_GPT_ID"] = m["model_id"]
        e["PSC_GPT_ID_PINNED"] = m["model_id"]
        e["PSC_GPT_NAME"] = m["display"]
        e["PSC_GPT_SURFACE"] = m["gpt_surface"]
    else:
        e["PSC_CLAUDE_ID"] = m["model_id"]
        e["PSC_CLAUDE_NAME"] = m["display"]
        e["PSC_CLAUDE_SURFACE"] = m["claude_surface"]
        e["PSC_CLAUDE_MAX_TOKENS"] = "2000"
    return e
