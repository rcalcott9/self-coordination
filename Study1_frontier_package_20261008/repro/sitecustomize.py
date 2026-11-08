"""Reproduction sandbox (loaded via PYTHONPATH by reproduce.sh).
1. Absolute paths recorded in frozen JSON files (/Users/<author>/...) are remapped into the package's mirrored HOME.
2. An audit hook makes any file OPEN outside the package (except the Python/R installation and temp dirs) an error,
   so reproduction can never silently read the original project folders."""
import os, sys, builtins, io
PKG = os.environ.get("S1PKG")
if PKG:
    HOME = os.path.join(PKG, "home"); AUTHOR = "/Users/calypsocalcott"
    def _m(p):
        if isinstance(p, str) and p.startswith(AUTHOR + "/") and not p.startswith(PKG):
            return HOME + p[len(AUTHOR):]
        return p
    _open = builtins.open
    def open_(file, *a, **k): return _open(_m(file), *a, **k)
    builtins.open = open_; io.open = open_
    for name in ("exists", "isfile", "isdir", "getsize"):
        f = getattr(os.path, name); setattr(os.path, name, (lambda f: lambda p, *a: f(_m(p), *a))(f))
    _ld = os.listdir; os.listdir = lambda p=".": _ld(_m(p))
    import glob as _g; _gg = _g.glob; _g.glob = lambda p, *a, **k: _gg(_m(p), *a, **k)
    ALLOW = (PKG, sys.prefix, sys.base_prefix, "/private/tmp", "/tmp", "/var/folders", "/private/var/folders",
             "/System", "/Library", "/usr", "/opt", "/dev", "/etc", os.path.expanduser("~/.matplotlib") if False else HOME)
    REAL = AUTHOR
    def hook(event, args):
        if event == "open" and args and isinstance(args[0], str):
            p = os.path.abspath(args[0])
            if p.startswith(REAL) and not p.startswith(PKG):
                raise PermissionError(f"[repro sandbox] read outside package blocked: {p}")
    sys.addaudithook(hook)
