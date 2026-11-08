"""
STUDY 2 - forbidden-vocabulary scan. Mechanical enforcement of
design/INTERPRETATION_GUARDRAILS.md.

    python3 check_terms.py            # scan, print, exit 1 on any hit
    python3 check_terms.py --list     # print what would be scanned and exit 0

NO API CALLS, no dependencies beyond the standard library.

WHAT IS SCANNED. Every .md file under study2_partner_policy_20260822/, plus every
figure caption (figures/*.txt) - i.e. the study's own prose and the text that
travels with its figures. Nothing outside this study's directory is touched.

WHAT IS FORBIDDEN. FROZEN_PARAMS.FORBIDDEN_TERMS, matched case-insensitively with
word boundaries so stems are caught ("colluded", "deceptions"). These are HARD:
one hit is a failure and the exit status is 1.

WHAT IS WARNED. The introspection family. FROZEN_PARAMS forbids introspection "as
an established mechanism", not the word itself - a sentence that explicitly denies
an introspective mechanism is legitimate and common in this study's limits
sections. A machine cannot tell the two apart, so every occurrence is surfaced for
a human to check and the exit status is unaffected.

ESCAPE HATCH, because the guardrails document has to name the terms it forbids:
    <!-- terms-check: allow -->        on the same line   -> that line is exempt
    <!-- terms-check: allow-file -->   in the first 40 lines -> whole file exempt
Both are printed in the report, so an exemption can never be silent. Use the
line-level form; the file-level form exists for a document that is entirely about
the vocabulary, and using it hides real hits.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "design"))
import FROZEN_PARAMS as FP                          # noqa: E402  the only term source

ALLOW_LINE = "terms-check: allow"
ALLOW_FILE = "terms-check: allow-file"

# Warned, never fatal - see the module docstring.
WARN_TERMS = ("introspection", "introspect", "introspective", "introspectively")

SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}


def targets():
    out = []
    for root, dirs, files in os.walk(EXP):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            path = os.path.join(root, f)
            if f.endswith(".md"):
                out.append(path)
            elif f.endswith(".txt") and os.path.basename(root) == "figures":
                out.append(path)          # figure captions travel with the figures
    return sorted(out)


def pattern(terms):
    return re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")\w*\b",
                      re.IGNORECASE)


def scan(paths):
    hard = pattern(FP.FORBIDDEN_TERMS)
    soft = pattern(WARN_TERMS)
    hits, warns, exempt_files, exempt_lines = [], [], [], []
    for path in paths:
        try:
            lines = open(path, errors="replace").read().splitlines()
        except OSError as exc:
            hits.append((path, 0, f"UNREADABLE: {exc}", ""))
            continue
        if any(ALLOW_FILE in ln for ln in lines[:40]):
            exempt_files.append(path)
            continue
        for i, ln in enumerate(lines, 1):
            h = hard.findall(ln)
            if h:
                if ALLOW_LINE in ln:
                    exempt_lines.append((path, i, sorted(set(x.lower() for x in h))))
                else:
                    hits.append((path, i, ", ".join(sorted(set(h))), ln.strip()))
            w = soft.findall(ln)
            if w and ALLOW_LINE not in ln:
                warns.append((path, i, ", ".join(sorted(set(w))), ln.strip()))
    return hits, warns, exempt_files, exempt_lines


def rel(p):
    return os.path.relpath(p, EXP)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="list targets and exit 0")
    args = ap.parse_args()

    paths = targets()
    print("=" * 78)
    print("FORBIDDEN-VOCABULARY SCAN - study2_partner_policy_20260822")
    print("=" * 78)
    print(f"forbidden (hard, from FROZEN_PARAMS.FORBIDDEN_TERMS): "
          f"{', '.join(FP.FORBIDDEN_TERMS)}")
    print(f"warned   (soft, not fatal)                          : "
          f"{', '.join(WARN_TERMS)}")
    print(f"scanned  : {len(paths)} files (*.md anywhere, figures/*.txt captions)")

    if args.list:
        for p in paths:
            print(f"   {rel(p)}")
        return 0

    hits, warns, ex_files, ex_lines = scan(paths)

    if ex_files:
        print(f"\nFILE-LEVEL EXEMPTIONS ({len(ex_files)}) - these were NOT scanned:")
        for p in ex_files:
            print(f"   {rel(p)}")
    if ex_lines:
        print(f"\nLINE-LEVEL EXEMPTIONS ({len(ex_lines)}) - declared, not hidden:")
        for p, i, terms in ex_lines:
            print(f"   {rel(p)}:{i}  [{', '.join(terms)}]")

    if warns:
        print(f"\nWARNINGS ({len(warns)}) - introspection family; check that each one "
              "DENIES an introspective mechanism rather than asserting it:")
        for p, i, t, ln in warns:
            print(f"   {rel(p)}:{i}  [{t}]  {ln[:100]}")
    else:
        print("\nWARNINGS: none")

    if hits:
        print(f"\nFAILURES ({len(hits)}):")
        for p, i, t, ln in hits:
            print(f"   {rel(p)}:{i}  [{t}]  {ln[:100]}")
        print("\nRESULT: FAIL - forbidden vocabulary present. See "
              "design/INTERPRETATION_GUARDRAILS.md for the permitted phrasing.")
        return 1

    print("\nRESULT: PASS - no forbidden term in any scanned file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
