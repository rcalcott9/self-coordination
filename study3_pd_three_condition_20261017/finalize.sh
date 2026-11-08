#!/bin/zsh
# Finish the hand-off steps the worktree guard blocked. Safe to run once; refuses to overwrite.
set -euo pipefail
W=${0:A:h}
SC=~/Desktop/Coordination/Self_Coordination
RL=~/.codex/.chatgpt-projects/g-p-6aa069d23ae08191a861f83470dbc913/review_loop
PY=/opt/anaconda3/bin/python

# 1. study folder into the project (copy; the worktree copy stays as the committed record)
[ -e $SC/study3_pd_three_condition_20261017 ] && { echo "already copied: $SC/study3_pd_three_condition_20261017"; } || cp -R $W $SC/study3_pd_three_condition_20261017

# 2. completion JSON + processed_messages -> completed
[ -e $RL/completions/pd-three-condition-pilot-20usd-01.json ] && echo "completion exists, not overwritten" || cp $W/review_loop_outbox/completions/pd-three-condition-pilot-20usd-01.json $RL/completions/
$PY - $RL $W/HANDOFF_ADDENDA.md $SC ~/claudine/projects/self-coordination-diary.md <<'EOF'
import json, os, sys, re
rl, add, sc, diary = sys.argv[1:]
p = rl + "/processed_messages.json"; r = json.load(open(p)); m = r["messages"]["pd-three-condition-pilot-20usd-01"]
if m["status"] != "completed":
    m.update(status="completed", completed_at="2026-10-17T20:40:00+00:00"); open(p + ".tmp", "w").write(json.dumps(r, indent=2)); os.replace(p + ".tmp", p)
A = open(add).read()
def block(tag): return A.split(f"## [{tag}]")[1].split("\n", 1)[1].split("\n## [")[0].strip() + "\n"
led = sc + "/COMPLETION_LEDGER_20261009.md"; t = open(led).read()
if "PD three-condition pilot COMPLETED" not in t:
    head, rest = t.split("\n", 1); open(led, "w").write(head + "\n\n" + block("LEDGER") + rest)
rep = sc + "/study3a_pass5_PROPOSED_20261016/results/run/analysis/REPORT.md"; t = open(rep).read()
if "Reporting corrections (2026-10-17" not in t: open(rep, "a").write("\n" + block("PASS5_REPORT"))
t = open(diary).read()
if "PD three-condition pilot" not in t:
    i = t.index("\n## 2026"); open(diary, "w").write(t[:i] + "\n" + block("DIARY") + t[i:])
print("done")
EOF
