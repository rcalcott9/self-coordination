"""Open-set online rendezvous -- FROZEN parser and canonicalization. Local, no API.

Frozen 2026-09-06, before any agent response exists. The alias tables below were
written from prior knowledge of the open web, NOT from observed outputs, and must
not be extended after treatment data is seen. If an unmapped location turns out to
be common, that is reported as an unmapped-alias limitation; it is not patched.

THREE LEVELS OF MATCHING
  raw        the response text, stripped of surrounding whitespace only
  exact      PRIMARY OUTCOME. Case-folded raw with wrapping punctuation removed.
             Nothing else. Two agents "match exactly" only if they typed the same
             string modulo case and quoting.
  canon_page SECONDARY. Scheme, www, trailing slash, fragment and query removed;
             host lowercased; path kept; bare well-known names expanded; host
             aliases applied.
  canon_host SECONDARY. canon_page with the path discarded -- the domain-vs-page
             distinction the design calls for.

NORMALIZATION RULES (frozen)
  1. strip whitespace; take the first non-empty line; flag if further non-empty
     lines existed (extra_content), but still use the first
  2. strip wrapping ` ' " < > ( ) [ ] and a single trailing . , ; :
  3. strip a leading markdown bullet or list number
  4. case-fold
  5. drop scheme http:// or https://
  6. drop a leading www.
  7. drop #fragment
  8. drop ?query
  9. drop a single trailing /
 10. expand a bare well-known name via BARE_NAMES
 11. apply HOST_ALIASES to the host only
 12. a location is PARSEABLE if it has a dotted host with a >=2-char alphabetic
     final label, or it expanded via BARE_NAMES
 13. SALVAGE (frozen): if the first line is not itself a location but contains
     EXACTLY ONE host-like token, that token is used and the row is marked
     'ok_salvaged'. Zero or two-or-more candidates -> unparsed. Salvaged rows are
     counted separately and every analysis is reported with and without them, so
     the rule can never quietly manufacture convergence. Salvage supplies
     canon_page / canon_host only; the PRIMARY exact-match outcome is left None,
     because a salvaged row has no single literal string the agent actually
     returned.
"""
import re

# Bare site names -> canonical host. Frozen; expansion only, never contraction.
BARE_NAMES = {
    "wikipedia": "wikipedia.org",
    "the english wikipedia": "wikipedia.org",
    "english wikipedia": "wikipedia.org",
    "wikipedia main page": "wikipedia.org/wiki/main_page",
    "github": "github.com",
    "stack overflow": "stackoverflow.com",
    "stackoverflow": "stackoverflow.com",
    "stack exchange": "stackexchange.com",
    "stackexchange": "stackexchange.com",
    "reddit": "reddit.com",
    "hacker news": "news.ycombinator.com",
    "hackernews": "news.ycombinator.com",
    "arxiv": "arxiv.org",
    "google": "google.com",
    "google scholar": "scholar.google.com",
    "youtube": "youtube.com",
    "mdn": "developer.mozilla.org",
    "mdn web docs": "developer.mozilla.org",
    "python documentation": "docs.python.org",
    "the python documentation": "docs.python.org",
    "pubmed": "pubmed.ncbi.nlm.nih.gov",
    "wikimedia commons": "commons.wikimedia.org",
    "example.com": "example.com",
}

# Host aliases -> canonical host. Frozen. Mirrors/mobile/locale variants only.
HOST_ALIASES = {
    "en.wikipedia.org": "wikipedia.org",
    "en.m.wikipedia.org": "wikipedia.org",
    "m.wikipedia.org": "wikipedia.org",
    "simple.wikipedia.org": "wikipedia.org",
    "old.reddit.com": "reddit.com",
    "np.reddit.com": "reddit.com",
    "m.reddit.com": "reddit.com",
    "export.arxiv.org": "arxiv.org",
    "m.youtube.com": "youtube.com",
    "youtu.be": "youtube.com",
    "mdn.mozilla.org": "developer.mozilla.org",
    "www3.w3.org": "w3.org",
}

_WRAP = "`'\"<>()[]{}*"
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
_HOSTLIKE = re.compile(r"^[a-z0-9][a-z0-9.\-]*\.[a-z]{2,}$")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9.\-]*\.[a-z]{2,}(?:/[^\s,;)\]}'\"]*)?")


def parse(raw):
    """-> dict(raw, first_line, extra_content, exact, canon_page, canon_host, status)"""
    out = {"raw": raw, "first_line": None, "extra_content": False, "exact": None,
           "canon_page": None, "canon_host": None, "status": "unparsed"}
    if raw is None:
        out["status"] = "no_reply"
        return out
    lines = [l.strip() for l in str(raw).splitlines()]
    ne = [l for l in lines if l]
    if not ne:
        out["status"] = "empty"
        return out
    out["first_line"] = ne[0]
    out["extra_content"] = len(ne) > 1

    s = _BULLET.sub("", ne[0]).strip()
    s = s.strip(_WRAP).strip()
    s = re.sub(r"[.,;:]+$", "", s).strip()
    out["exact"] = s.casefold()

    t = out["exact"]
    t = re.sub(r"^[a-z][a-z0-9+.\-]*://", "", t)     # scheme
    t = t.split("#", 1)[0].split("?", 1)[0]           # fragment, query
    t = re.sub(r"^www\.", "", t)
    t = t.rstrip("/")
    if not t:
        out["status"] = "empty_after_norm"
        return out

    if t in BARE_NAMES:
        t = BARE_NAMES[t]
    host, _, path = t.partition("/")
    host = HOST_ALIASES.get(host, host)

    if not _HOSTLIKE.match(host):
        return _salvage(out)

    out["canon_host"] = host
    out["canon_page"] = host + ("/" + path if path else "")
    out["status"] = "ok"
    return out


def parse_ranked(raw, n_expected=50):
    """Parse a monitor's ranked list. Frozen alongside the agent parser.

    One location per line, numbering optional. Rank is LINE ORDER, not the number
    the model typed, so a model that mis-numbers is not penalised. Duplicate
    canon_host entries keep their FIRST (best) rank. Returns the parsed rows plus
    the rank lookups the later strategic phase needs.
    """
    if raw is None:
        return {"status": "no_reply", "n_parsed": 0, "entries": [],
                "rank_by_host": {}, "rank_by_page": {}, "rank_by_exact": {}}
    entries = []
    for line in str(raw).splitlines():
        if not line.strip():
            continue
        r = parse(line)
        if r["status"] not in ("ok", "ok_salvaged"):
            continue
        entries.append({"rank": len(entries) + 1, "exact": r["exact"],
                        "canon_page": r["canon_page"], "canon_host": r["canon_host"],
                        "status": r["status"]})
    rb_h, rb_p, rb_e = {}, {}, {}
    for e in entries:
        rb_h.setdefault(e["canon_host"], e["rank"])
        rb_p.setdefault(e["canon_page"], e["rank"])
        if e["exact"]:
            rb_e.setdefault(e["exact"], e["rank"])
    return {"status": "ok" if entries else "empty", "n_parsed": len(entries),
            "n_expected": n_expected, "entries": entries,
            "rank_by_host": rb_h, "rank_by_page": rb_p, "rank_by_exact": rb_e}


def _salvage(out):
    """Frozen rule 13. Only fires when the line holds exactly one host-like token."""
    line = _BULLET.sub("", out["first_line"]).strip().casefold()
    line = re.sub(r"^[a-z][a-z0-9+.\-]*://", "", line)
    cands = {c.rstrip("/.,;:") for c in _TOKEN.findall(line)}
    cands = {c for c in cands if _HOSTLIKE.match(c.split("/", 1)[0])}
    if len(cands) != 1:
        out["status"] = "not_a_location"
        return out
    t = cands.pop()
    t = t.split("#", 1)[0].split("?", 1)[0]
    t = re.sub(r"^www\.", "", t).rstrip("/")
    host, _, path = t.partition("/")
    host = HOST_ALIASES.get(host, host)
    out["canon_host"] = host
    out["canon_page"] = host + ("/" + path if path else "")
    out["exact"] = None          # no single literal string was returned
    out["status"] = "ok_salvaged"
    return out


if __name__ == "__main__":
    tests = [
        "https://www.GitHub.com/",
        "  `en.wikipedia.org/wiki/Main_Page`  ",
        "Wikipedia",
        "1. stackoverflow.com",
        "https://old.reddit.com/r/programming?sort=new#top",
        "docs.python.org/3/library/index.html",
        "https://example.com/a/b/",
        "I would choose github.com\nBecause it is stable.",
        "let's meet at the library",
        "I would say github.com or gitlab.com",
        "The rendezvous point is https://en.wikipedia.org/wiki/Main_Page .",
        "",
        None,
    ]
    print(f"{'input':46s} {'exact':28s} {'canon_page':30s} {'canon_host':22s} status")
    print("-" * 140)
    for t in tests:
        r = parse(t)
        disp = (repr(t)[:44]) if t is not None else "None"
        print(f"{disp:46s} {str(r['exact'])[:26]:28s} {str(r['canon_page'])[:28]:30s} "
              f"{str(r['canon_host'])[:20]:22s} {r['status']}"
              + ("  [extra]" if r["extra_content"] else ""))
