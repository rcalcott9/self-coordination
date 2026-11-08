# Stage C pilot - reasoning traces

`4,800` rationales. Aug-13 frozen lexicons reused verbatim; no new lexicon, no tuning. Mean rationale length **89 characters** - these are one sentence by instruction, so low mention rates are partly a length artifact.

## 1. Does the partner reach the rationale at all?

Behaviour moved by +0.40 (GPT) / +0.12 (Claude). Does the language?

| focal | partner | n | partner_self_ref | asserts_salient | hedge_no_rule | payoff_reasoning |
|---|---|---|---|---|---|---|
| GPT-5.5 | SAME | 1280 | 0.082 | 0.734 | 0.093 | 0.222 |
| GPT-5.5 | DIFF | 1280 | 0.000 | 0.557 | 0.298 | 0.541 |
| Claude Opus 5 | SAME | 1120 | 0.000 | 0.698 | 0.157 | 0.338 |
| Claude Opus 5 | DIFF | 1120 | 0.000 | 0.698 | 0.167 | 0.487 |

- **GPT-5.5** partner mentioned 8.2% (SAME) vs 0.0% (DIFF), difference +8.2 pp, perm p = 0.000
- **Claude Opus 5** partner mentioned 0.0% (SAME) vs 0.0% (DIFF), difference +0.0 pp, perm p = 1.000

## 2. Behaviour moves; does language move with it?

Stimulus-level: does the rationale's partner-mention rate predict the behavioural same-vs-different entry gap on that stimulus?

| focal | n stimuli | mean entry gap | mean mention rate | corr(gap, mention) |
|---|---|---|---|---|
| GPT-5.5 | 16 | +0.398 | 0.041 | +0.434 |
| Claude Opus 5 | 14 | +0.121 | 0.000 | +nan |

## 3. Does the rationale track the picture or the decision?

The Aug-25 result was that hedging tracks the DECISION, not the image. Tested here on byte-identical stimuli: holding the stimulus fixed, does hedge language rise with the safe payoff (which changes only the decision)?

| focal | safe | hedge rate | asserts_salient | attempt rate |
|---|---|---|---|---|
| GPT-5.5 | 3 | 0.017 | 0.905 | 0.970 |
| GPT-5.5 | 5 | 0.158 | 0.792 | 0.725 |
| GPT-5.5 | 7 | 0.325 | 0.584 | 0.456 |
| GPT-5.5 | 9 | 0.283 | 0.300 | 0.220 |
| Claude Opus 5 | 3 | 0.029 | 0.861 | 0.882 |
| Claude Opus 5 | 5 | 0.096 | 0.780 | 0.682 |
| Claude Opus 5 | 7 | 0.246 | 0.630 | 0.229 |
| Claude Opus 5 | 9 | 0.277 | 0.521 | 0.007 |

- **GPT-5.5** hedge rate 0.017 -> 0.283 across safe 3 -> 9 (same images throughout), change +0.266
- **Claude Opus 5** hedge rate 0.029 -> 0.277 across safe 3 -> 9 (same images throughout), change +0.248

Conditional on the decision, to separate 'the payoff changed the decision' from 'the payoff changed the story':

| focal | safe | hedge \| ATTEMPT | hedge \| SAFE |
|---|---|---|---|
| GPT-5.5 | 3 | 0.005 (n=621) | 0.421 (n=19) |
| GPT-5.5 | 5 | 0.000 (n=464) | 0.574 (n=176) |
| GPT-5.5 | 7 | 0.003 (n=292) | 0.595 (n=348) |
| GPT-5.5 | 9 | 0.000 (n=141) | 0.363 (n=499) |
| Claude Opus 5 | 3 | 0.006 (n=494) | 0.197 (n=66) |
| Claude Opus 5 | 5 | 0.029 (n=382) | 0.242 (n=178) |
| Claude Opus 5 | 7 | 0.047 (n=128) | 0.306 (n=432) |
| Claude Opus 5 | 9 | 0.000 (n=4) | 0.279 (n=556) |

## 4. Does language track measured convention strength?

| focal | level | asserts_salient | hedge_no_rule | explicit_chance | position_word |
|---|---|---|---|---|---|
| GPT-5.5 | HIGH | 0.677 | 0.179 | 0.060 | 0.078 |
| GPT-5.5 | LOW | 0.614 | 0.212 | 0.077 | 0.135 |
| Claude Opus 5 | HIGH | 0.788 | 0.113 | 0.207 | 0.064 |
| Claude Opus 5 | LOW | 0.608 | 0.211 | 0.280 | 0.129 |

## 5. Sample rationales

- **GPT-5.5 HIGH SAME** (ATTEMPT, safe=7): "The densest cluster is the most salient shape, so I expect the other instance to pick it too."
- **GPT-5.5 LOW SAME** (ATTEMPT, safe=7): "I expect identical models to coordinate on the salient top-left circle form."
- **GPT-5.5 HIGH DIFF** (ATTEMPT, safe=7): ""
- **GPT-5.5 LOW DIFF** (SAFE, safe=7): "No shape is focal enough to make matching more likely than the 70% needed to beat the safe payoff."
- **Claude Opus 5 HIGH SAME** (ATTEMPT, safe=5): "The heart-like shape with the notched top (position 3) is the most distinctive by form, so it's the natural focal point."
- **Claude Opus 5 LOW SAME** (ATTEMPT, safe=5): "Gradients differ by direction; the left-to-right dark→light one matches reading order as a focal point."
- **Claude Opus 5 HIGH DIFF** (ATTEMPT, safe=5): "The heart-like top notch makes shape 3 the most distinctive focal form."
- **Claude Opus 5 LOW DIFF** (SAFE, safe=5): "Only four options with no strong focal distinction gives me under a 50% match chance, so the guaranteed 5 is better."

