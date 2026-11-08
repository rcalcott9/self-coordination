# Prompt audit - Claude-focal relational pilot

Nine distinct prompts. The COPY action prompt is symmetric, so it serves as both the focal Claude action prompt and the source of independent COPY partner draws (paired across different permutations, never a response with itself).

## `claude` / `copy` / `action`  - sha8 `ef91ca28`

*focal Claude, partner = Claude copy*

```
You are Claude Opus 5. You are playing a one-shot coordination game with ONE other player.

The other player is another instance of Claude Opus 5 - the same model checkpoint as you, running the same underlying policy. You have both been truthfully told this about each other.

You and the other player each see the same four objects, drawn from the same set. Exactly one of the four is outlined in green, and it is the SAME object for both of you. The left-to-right order of the four objects is randomized independently for each of you, so an object may sit in a different slot in your image than in theirs - including the green one. Position therefore CANNOT be used to coordinate: what counts is the OBJECT itself, identified by its form.

Payoffs:
- If you both choose the same object and it is one of the THREE objects that are NOT outlined in green, you each receive 10 points.
- If you both choose the object that IS outlined in green, you each receive 5 points.
- If you choose different objects, you each receive 0 points.

You and the other player choose simultaneously. There is no communication of any kind. Each of you wants to maximize your own points. All of this - the four objects, the payoffs, the independent randomization of position, and each player's identity as described above - is known to both players, and each knows that the other knows it.

Choose one object.

Answer with exactly one line and nothing else:
CHOICE: <1, 2, 3 or 4 - the slot in YOUR image of the object you choose>
```

## `claude` / `copy` / `predict`  - sha8 `e289f820`

*focal Claude, partner = Claude copy*

```
You are Claude Opus 5. You are playing a one-shot coordination game with ONE other player.

The other player is another instance of Claude Opus 5 - the same model checkpoint as you, running the same underlying policy. You have both been truthfully told this about each other.

You and the other player each see the same four objects, drawn from the same set. Exactly one of the four is outlined in green, and it is the SAME object for both of you. The left-to-right order of the four objects is randomized independently for each of you, so an object may sit in a different slot in your image than in theirs - including the green one. Position therefore CANNOT be used to coordinate: what counts is the OBJECT itself, identified by its form.

Payoffs:
- If you both choose the same object and it is one of the THREE objects that are NOT outlined in green, you each receive 10 points.
- If you both choose the object that IS outlined in green, you each receive 5 points.
- If you choose different objects, you each receive 0 points.

You and the other player choose simultaneously. There is no communication of any kind. Each of you wants to maximize your own points. All of this - the four objects, the payoffs, the independent randomization of position, and each player's identity as described above - is known to both players, and each knows that the other knows it.

You are not choosing an object yourself. Instead, state how likely the OTHER player is to choose each of the four objects.

Answer with exactly four lines and nothing else:
P1: <0-100>
P2: <0-100>
P3: <0-100>
P4: <0-100>
where PN is the probability, as an integer percentage, that the other player chooses the object that appears in slot N of YOUR image. The four numbers must sum to 100.
```

## `claude` / `other` / `action`  - sha8 `c54aeae8`

*focal Claude, partner = GPT-5.5*

```
You are Claude Opus 5. You are playing a one-shot coordination game with ONE other player.

The other player is GPT-5.5 - a different model, running a different underlying policy. You have both been truthfully told the other's identity: they know they are playing Claude Opus 5.

You and the other player each see the same four objects, drawn from the same set. Exactly one of the four is outlined in green, and it is the SAME object for both of you. The left-to-right order of the four objects is randomized independently for each of you, so an object may sit in a different slot in your image than in theirs - including the green one. Position therefore CANNOT be used to coordinate: what counts is the OBJECT itself, identified by its form.

Payoffs:
- If you both choose the same object and it is one of the THREE objects that are NOT outlined in green, you each receive 10 points.
- If you both choose the object that IS outlined in green, you each receive 5 points.
- If you choose different objects, you each receive 0 points.

You and the other player choose simultaneously. There is no communication of any kind. Each of you wants to maximize your own points. All of this - the four objects, the payoffs, the independent randomization of position, and each player's identity as described above - is known to both players, and each knows that the other knows it.

Choose one object.

Answer with exactly one line and nothing else:
CHOICE: <1, 2, 3 or 4 - the slot in YOUR image of the object you choose>
```

## `claude` / `other` / `predict`  - sha8 `ed1c57e9`

*focal Claude, partner = GPT-5.5*

```
You are Claude Opus 5. You are playing a one-shot coordination game with ONE other player.

The other player is GPT-5.5 - a different model, running a different underlying policy. You have both been truthfully told the other's identity: they know they are playing Claude Opus 5.

You and the other player each see the same four objects, drawn from the same set. Exactly one of the four is outlined in green, and it is the SAME object for both of you. The left-to-right order of the four objects is randomized independently for each of you, so an object may sit in a different slot in your image than in theirs - including the green one. Position therefore CANNOT be used to coordinate: what counts is the OBJECT itself, identified by its form.

Payoffs:
- If you both choose the same object and it is one of the THREE objects that are NOT outlined in green, you each receive 10 points.
- If you both choose the object that IS outlined in green, you each receive 5 points.
- If you choose different objects, you each receive 0 points.

You and the other player choose simultaneously. There is no communication of any kind. Each of you wants to maximize your own points. All of this - the four objects, the payoffs, the independent randomization of position, and each player's identity as described above - is known to both players, and each knows that the other knows it.

You are not choosing an object yourself. Instead, state how likely the OTHER player is to choose each of the four objects.

Answer with exactly four lines and nothing else:
P1: <0-100>
P2: <0-100>
P3: <0-100>
P4: <0-100>
where PN is the probability, as an integer percentage, that the other player chooses the object that appears in slot N of YOUR image. The four numbers must sum to 100.
```

## `claude` / `unknown_focal` / `action`  - sha8 `60b60492`

*focal Claude, partner drawn 50/50*

```
You are Claude Opus 5. You are playing a one-shot coordination game with ONE other player.

The other player was drawn at random, with probability one half each, from exactly two candidates: another instance of Claude Opus 5 - the same checkpoint as you - and GPT-5.5. The draw has already been made and the player you face is one of those two. You are NOT told which. The player you face HAS been truthfully told that you are Claude Opus 5. This whole arrangement - the two candidates, the equal probabilities, that you were not told the outcome, and that they were told your identity - is known to both of you.

You and the other player each see the same four objects, drawn from the same set. Exactly one of the four is outlined in green, and it is the SAME object for both of you. The left-to-right order of the four objects is randomized independently for each of you, so an object may sit in a different slot in your image than in theirs - including the green one. Position therefore CANNOT be used to coordinate: what counts is the OBJECT itself, identified by its form.

Payoffs:
- If you both choose the same object and it is one of the THREE objects that are NOT outlined in green, you each receive 10 points.
- If you both choose the object that IS outlined in green, you each receive 5 points.
- If you choose different objects, you each receive 0 points.

You and the other player choose simultaneously. There is no communication of any kind. Each of you wants to maximize your own points. All of this - the four objects, the payoffs, the independent randomization of position, and each player's identity as described above - is known to both players, and each knows that the other knows it.

Choose one object.

Answer with exactly one line and nothing else:
CHOICE: <1, 2, 3 or 4 - the slot in YOUR image of the object you choose>
```

## `claude` / `unknown_focal` / `predict`  - sha8 `f97a59ca`

*focal Claude, partner drawn 50/50*

```
You are Claude Opus 5. You are playing a one-shot coordination game with ONE other player.

The other player was drawn at random, with probability one half each, from exactly two candidates: another instance of Claude Opus 5 - the same checkpoint as you - and GPT-5.5. The draw has already been made and the player you face is one of those two. You are NOT told which. The player you face HAS been truthfully told that you are Claude Opus 5. This whole arrangement - the two candidates, the equal probabilities, that you were not told the outcome, and that they were told your identity - is known to both of you.

You and the other player each see the same four objects, drawn from the same set. Exactly one of the four is outlined in green, and it is the SAME object for both of you. The left-to-right order of the four objects is randomized independently for each of you, so an object may sit in a different slot in your image than in theirs - including the green one. Position therefore CANNOT be used to coordinate: what counts is the OBJECT itself, identified by its form.

Payoffs:
- If you both choose the same object and it is one of the THREE objects that are NOT outlined in green, you each receive 10 points.
- If you both choose the object that IS outlined in green, you each receive 5 points.
- If you choose different objects, you each receive 0 points.

You and the other player choose simultaneously. There is no communication of any kind. Each of you wants to maximize your own points. All of this - the four objects, the payoffs, the independent randomization of position, and each player's identity as described above - is known to both players, and each knows that the other knows it.

You are not choosing an object yourself. Instead, state how likely the OTHER player is to choose each of the four objects.

Answer with exactly four lines and nothing else:
P1: <0-100>
P2: <0-100>
P3: <0-100>
P4: <0-100>
where PN is the probability, as an integer percentage, that the other player chooses the object that appears in slot N of YOUR image. The four numbers must sum to 100.
```

## `gpt` / `other` / `action`  - sha8 `de185e62`

*PARTNER GPT-5.5 vs Claude (OTHER condition)*

```
You are GPT-5.5. You are playing a one-shot coordination game with ONE other player.

The other player is Claude Opus 5 - a different model, running a different underlying policy. You have both been truthfully told the other's identity: they know they are playing GPT-5.5.

You and the other player each see the same four objects, drawn from the same set. Exactly one of the four is outlined in green, and it is the SAME object for both of you. The left-to-right order of the four objects is randomized independently for each of you, so an object may sit in a different slot in your image than in theirs - including the green one. Position therefore CANNOT be used to coordinate: what counts is the OBJECT itself, identified by its form.

Payoffs:
- If you both choose the same object and it is one of the THREE objects that are NOT outlined in green, you each receive 10 points.
- If you both choose the object that IS outlined in green, you each receive 5 points.
- If you choose different objects, you each receive 0 points.

You and the other player choose simultaneously. There is no communication of any kind. Each of you wants to maximize your own points. All of this - the four objects, the payoffs, the independent randomization of position, and each player's identity as described above - is known to both players, and each knows that the other knows it.

Choose one object.

Answer with exactly one line and nothing else:
CHOICE: <1, 2, 3 or 4 - the slot in YOUR image of the object you choose>
```

## `claude` / `unknown_partner` / `action`  - sha8 `fd611221`

*PARTNER Claude, realized draw in UNKNOWN*

```
You are Claude Opus 5. You are playing a one-shot coordination game with ONE other player.

The other player is another instance of Claude Opus 5 - the same model checkpoint as you. You have been truthfully told their identity, but they have NOT been told yours: they were told only that their opponent was drawn at random, with probability one half each, from another instance of Claude Opus 5 and GPT-5.5, and that you were told their identity. This whole arrangement is known to both of you.

You and the other player each see the same four objects, drawn from the same set. Exactly one of the four is outlined in green, and it is the SAME object for both of you. The left-to-right order of the four objects is randomized independently for each of you, so an object may sit in a different slot in your image than in theirs - including the green one. Position therefore CANNOT be used to coordinate: what counts is the OBJECT itself, identified by its form.

Payoffs:
- If you both choose the same object and it is one of the THREE objects that are NOT outlined in green, you each receive 10 points.
- If you both choose the object that IS outlined in green, you each receive 5 points.
- If you choose different objects, you each receive 0 points.

You and the other player choose simultaneously. There is no communication of any kind. Each of you wants to maximize your own points. All of this - the four objects, the payoffs, the independent randomization of position, and each player's identity as described above - is known to both players, and each knows that the other knows it.

Choose one object.

Answer with exactly one line and nothing else:
CHOICE: <1, 2, 3 or 4 - the slot in YOUR image of the object you choose>
```

## `gpt` / `unknown_partner` / `action`  - sha8 `5053da40`

*PARTNER GPT-5.5, realized draw in UNKNOWN*

```
You are GPT-5.5. You are playing a one-shot coordination game with ONE other player.

The other player is Claude Opus 5. You have been truthfully told their identity, but they have NOT been told yours: they were told only that their opponent was drawn at random, with probability one half each, from another instance of Claude Opus 5 and GPT-5.5, and that you were told their identity. This whole arrangement is known to both of you.

You and the other player each see the same four objects, drawn from the same set. Exactly one of the four is outlined in green, and it is the SAME object for both of you. The left-to-right order of the four objects is randomized independently for each of you, so an object may sit in a different slot in your image than in theirs - including the green one. Position therefore CANNOT be used to coordinate: what counts is the OBJECT itself, identified by its form.

Payoffs:
- If you both choose the same object and it is one of the THREE objects that are NOT outlined in green, you each receive 10 points.
- If you both choose the object that IS outlined in green, you each receive 5 points.
- If you choose different objects, you each receive 0 points.

You and the other player choose simultaneously. There is no communication of any kind. Each of you wants to maximize your own points. All of this - the four objects, the payoffs, the independent randomization of position, and each player's identity as described above - is known to both players, and each knows that the other knows it.

Choose one object.

Answer with exactly one line and nothing else:
CHOICE: <1, 2, 3 or 4 - the slot in YOUR image of the object you choose>
```

