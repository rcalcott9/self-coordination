"""Unit tests for the 4-option Study 2 apparatus. No API calls.

Run:  python3 -m pytest test_s4.py -q      (or: python3 test_s4.py)
"""
import json, os, math
from collections import Counter
import s4_common as S


# ------------------------------------------------------- position schedule ----
def test_schedule_exact_item_position_balance():
    """Every item in every position exactly n/4 times - the whole point."""
    for n in (4, 8, 12, 20, 24, 48, 60, 72, 96, 120):
        sched = S.position_schedule(n)
        assert len(sched) == n
        inc = Counter()
        for pid in sched:
            for pos, item in enumerate(S.PERMS[pid]):
                inc[(item, pos)] += 1
        tgt = n // 4
        assert all(inc[(i, p)] == tgt for i in range(4) for p in range(4)), \
            f"n={n} unbalanced: {dict(inc)}"


def test_schedule_is_deterministic():
    assert S.position_schedule(60) == S.position_schedule(60)


def test_schedule_rejects_bad_n():
    for n in (5, 7, 30, 61):
        try:
            S.position_schedule(n)
        except ValueError:
            continue
        raise AssertionError(f"n={n} should have been rejected")


def test_schedule_uses_many_permutations():
    """A schedule collapsed onto one Latin square would confound relative order."""
    assert len(set(S.position_schedule(60))) >= 12
    assert len(set(S.position_schedule(48))) == 24


def test_item_at_matches_perms():
    for pid in range(24):
        for pos in range(4):
            assert S.item_at(pid, pos) == S.PERMS[pid][pos]


# ------------------------------------------------------------- estimators -----
def test_unbiased_match_floor_is_quarter_not_half():
    """The reason the study moved to 4 options at all."""
    uniform = Counter({0: 250, 1: 250, 2: 250, 3: 250})
    assert abs(S.unbiased_match(uniform) - 0.25) < 0.01
    binary = Counter({0: 500, 1: 500})
    assert abs(S.unbiased_match(binary) - 0.50) < 0.01


def test_unbiased_match_deterministic_is_one():
    assert S.unbiased_match(Counter({2: 60})) == 1.0


def test_unbiased_match_is_below_plugin():
    c = Counter({0: 30, 1: 20, 2: 10})
    assert S.unbiased_match(c) < S.plugin_match(c)


def test_unbiased_match_nan_below_two():
    assert math.isnan(S.unbiased_match(Counter({0: 1})))
    assert math.isnan(S.unbiased_match(Counter()))


def test_weak_convention_sits_between_chance_and_strong():
    """The band that only exists at 4 options."""
    weak = Counter({0: 30, 1: 20, 2: 5, 3: 5})       # a real but soft preference
    m = S.unbiased_match(weak)
    assert 0.25 < m < 0.75, m


def test_entropy_bounds():
    assert abs(S.entropy_bits(Counter({0: 25, 1: 25, 2: 25, 3: 25})) - 2.0) < 1e-9
    assert S.entropy_bits(Counter({1: 40})) == 0.0


def test_position_bias_flat_vs_fixed():
    assert abs(S.position_bias(Counter({0: 15, 1: 15, 2: 15, 3: 15}))) < 1e-9
    assert abs(S.position_bias(Counter({0: 60})) - 0.75) < 1e-9


def test_wilson_ci_brackets_point():
    lo, hi = S.wilson_ci(30, 60)
    assert lo < 0.5 < hi


def test_boot_ci_brackets_and_is_seeded():
    items = [0] * 40 + [1] * 20
    a = S.boot_match_ci(items, b=400)
    b = S.boot_match_ci(items, b=400)
    assert a == b
    assert a[0] <= S.unbiased_match(Counter(items)) <= a[1]


# ---------------------------------------------------------------- parsers -----
def test_parse_choice_variants():
    assert S.parse_choice("blah CHOICE: 3") == 2
    assert S.parse_choice("CHOICE: [1]") == 0
    assert S.parse_choice("choice: 4") == 3
    assert S.parse_choice("CHOICE: 2\ntrailing") == 1


def test_parse_choice_takes_last_mention():
    assert S.parse_choice("CHOICE: 1 ... actually CHOICE: 4") == 3


def test_parse_choice_returns_none_never_a_default():
    """Study 1's legacy runner returned 'J' on failure and J was the estimand."""
    for bad in ("", None, "no answer", "CHOICE: 5", "CHOICE: LEFT", "CHOICE: zero"):
        assert S.parse_choice(bad) is None, bad


def test_parse_probability_and_salience():
    assert S.parse_probability("MATCH_PROBABILITY: 70") == 0.70
    assert S.parse_probability("MATCH_PROBABILITY: 0") == 0.0
    assert S.parse_probability("MATCH_PROBABILITY: 101") is None
    assert S.parse_salience("SALIENCE: 55") == 0.55
    assert S.parse_salience("nothing") is None
    assert S.parse_likely("LIKELY: 2") == 1


# ---------------------------------------------------------------- prompts -----
def test_prompts_mention_four_and_forbid_position():
    for p in (S.STAGE_A_PROMPT, S.SALIENCE_PROMPT,
              S.auditor_prompt("gpt"), S.auditor_prompt("claude")):
        assert "four" in p.lower()
        assert "position" in p.lower()
        assert "two shapes" not in p.lower()


def test_auditor_prompts_differ_only_by_model_name():
    """Byte-identical after name normalisation - so a partner/auditor effect can
    never be a wording effect. Carried over from Study 2's partner template."""
    g = S.auditor_prompt("gpt").replace(S.DISPLAY["gpt"], "<M>")
    c = S.auditor_prompt("claude").replace(S.DISPLAY["claude"], "<M>")
    assert g == c


def test_prompt_hashes_are_stable():
    assert S.PROMPT_SHA["stage_a"] == S.sha8(S.STAGE_A_PROMPT)
    assert len(S.PROMPT_SHA["stage_a"]) == 8


# ---------------------------------------------------------------- battery -----
def _battery_dir():
    return S.STIM


def test_battery_rendered_and_complete():
    man = os.path.join(_battery_dir(), "battery_manifest.csv")
    if not os.path.exists(man):
        import pytest
        pytest.skip("battery not rendered yet")
    import csv
    rows = list(csv.DictReader(open(man)))
    assert len(rows) >= 100, f"only {len(rows)} stimuli"
    for r in rows[:8] + rows[-8:]:
        d = os.path.join(_battery_dir(), r["stimulus_id"])
        assert os.path.isdir(d), d
        assert len([f for f in os.listdir(d) if f.endswith(".png")]) == 24
        m = json.load(open(os.path.join(d, "manifest.json")))
        assert len(m) == 24
        for pid in range(24):
            assert sorted(m[str(pid)]) == [0, 1, 2, 3]


def test_manifest_round_trips_position_to_item():
    man = os.path.join(_battery_dir(), "battery_manifest.csv")
    if not os.path.exists(man):
        import pytest
        pytest.skip("battery not rendered yet")
    import csv
    sid = list(csv.DictReader(open(man)))[0]["stimulus_id"]
    m = json.load(open(os.path.join(_battery_dir(), sid, "manifest.json")))
    for pid in range(24):
        for pos in range(4):
            assert m[str(pid)][pos] == S.item_at(pid, pos)


if __name__ == "__main__":
    import sys
    fns = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    bad = 0
    for name, fn in fns:
        try:
            fn()
            print(f"  PASS  {name}")
        except BaseException as e:
            if type(e).__name__ == "Skipped":
                print(f"  SKIP  {name}")
                continue
            bad += 1
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns)-bad}/{len(fns)} passed")
    sys.exit(1 if bad else 0)
