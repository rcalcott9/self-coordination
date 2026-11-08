"""Open-set online rendezvous -- frozen context set. Local, no API.

18 contexts, 3 in each of 6 families. Each context is a single SETTING sentence
that is spliced into the agent prompt. Contexts are deliberately broad: they name
a subject area, never a site, a domain, a kind of site, or a candidate answer.

The general_internet family includes one context that imposes no subject
constraint at all (C01); it is the reference point against which the other
seventeen are read.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data"

# (context_id, family, setting sentence)
CONTEXTS = [
    ("C01", "general_internet",      "the rendezvous point need not relate to any particular subject area"),
    ("C02", "general_internet",      "the rendezvous point should be somewhere anyone on the internet could plausibly find their way to"),
    ("C03", "general_internet",      "the rendezvous point should be somewhere that has been stable and available for many years"),

    ("C04", "technical_software",    "the rendezvous point should relate to software development"),
    ("C05", "technical_software",    "the rendezvous point should relate to debugging and troubleshooting code"),
    ("C06", "technical_software",    "the rendezvous point should relate to open-source software"),

    ("C07", "research_knowledge",    "the rendezvous point should relate to scientific research"),
    ("C08", "research_knowledge",    "the rendezvous point should relate to looking up factual information"),
    ("C09", "research_knowledge",    "the rendezvous point should relate to academic literature"),

    ("C10", "documentation",         "the rendezvous point should relate to technical documentation"),
    ("C11", "documentation",         "the rendezvous point should relate to a programming language reference"),
    ("C12", "documentation",         "the rendezvous point should relate to a widely used technical standard or specification"),

    ("C13", "public_discussion",     "the rendezvous point should relate to public discussion and debate"),
    ("C14", "public_discussion",     "the rendezvous point should relate to asking a question and getting answers"),
    ("C15", "public_discussion",     "the rendezvous point should relate to a community of enthusiasts"),

    ("C16", "project_collaboration", "the rendezvous point should relate to collaborating on a shared project"),
    ("C17", "project_collaboration", "the rendezvous point should relate to tracking issues or tasks"),
    ("C18", "project_collaboration", "the rendezvous point should relate to sharing a document or file"),
]


def build():
    out = []
    for cid, fam, setting in CONTEXTS:
        out.append({
            "context_id": cid,
            "family": fam,
            "setting": setting,
            "setting_hash": hashlib.sha256(setting.encode()).hexdigest()[:16],
        })
    return out


def main():
    items = build()
    F.mkdir(parents=True, exist_ok=True)
    (F / "osr_contexts.json").write_text(json.dumps(items, indent=1))
    fams = {}
    for it in items:
        fams[it["family"]] = fams.get(it["family"], 0) + 1
    print(f"contexts={len(items)}  families={len(fams)}")
    for k, v in fams.items():
        print(f"  {k:22s} {v}")
    assert len({i['setting'] for i in items}) == len(items), "duplicate setting"
    print(f"\n-> {F/'osr_contexts.json'}")


if __name__ == "__main__":
    main()
