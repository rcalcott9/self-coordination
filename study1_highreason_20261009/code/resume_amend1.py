"""Amendment 1 resume: run the frozen code/run.py unmodified with the global cap raised to $184.22
($149.22 spent at the cap stop + $35 authorised). Nothing else changes; see design/AMENDMENT_1_resume.md.

  /opt/anaconda3/bin/python code/resume_amend1.py --stage main [--dry] [--workers N]
"""
import importlib.util, os, sys

CAP = 184.22
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
spec = importlib.util.spec_from_file_location("run_frozen", os.path.join(HERE, "run.py"))
run = importlib.util.module_from_spec(spec); spec.loader.exec_module(run)
_verify = run.verify


def verify():
    F, fsha = _verify()                      # all frozen-hash and code-hash checks run unchanged
    assert fsha == "933aa87d", fsha
    F["cap_usd"] = CAP
    return F, fsha


run.verify = verify
run.main()
