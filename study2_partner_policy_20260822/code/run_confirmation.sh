#!/bin/zsh
# Study 2 CONFIRMATION SCREEN -- Stage-A-style re-estimation at higher n.
# One argument: the actor (gpt|claude). Runs the three n-groups sequentially.
# Reuses the frozen Study 1 runner unchanged; PSC_EXP_DIR redirects all output
# under study2/data/confirmation so Study 1's tree is never written to.
set -u
ACTOR=$1
S2=/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_partner_policy_20260822
CODE=/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/policy_specific_self_coordination_20260812_1401/code
export PSC_EXP_DIR=$S2/data/confirmation
cd $CODE
echo "### $ACTOR group n=180 ###"
python3 stage_a_ground_truth.py --n 180 --models $ACTOR --stimuli a_chev_ud b_spiral_cw c_open_cplx d_texture
echo "### $ACTOR group n=120 ###"
python3 stage_a_ground_truth.py --n 120 --models $ACTOR --stimuli rot mirror
echo "### $ACTOR group n=60 ###"
python3 stage_a_ground_truth.py --n 60 --models $ACTOR --stimuli proto s_arrow
echo "### $ACTOR ALL GROUPS DONE ###"
