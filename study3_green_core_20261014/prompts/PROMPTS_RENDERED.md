# GREEN core - rendered prompts (PREPARATION ONLY; not sent)

Archived prompts reused verbatim (sha8 asserted). `withheld` is the only new text.

## `claude` / `copy` / `action` - sha8 `ef91ca28` (archived, sent in pilot)

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

## `claude` / `copy` / `predict` - sha8 `e289f820` (archived, sent in pilot)

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

## `claude` / `other` / `action` - sha8 `c54aeae8` (archived, sent in pilot)

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

## `claude` / `other` / `predict` - sha8 `ed1c57e9` (archived, sent in pilot)

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

## `claude` / `withheld` / `action` - sha8 `ca7ce3b8` (NEW)

```
You are Claude Opus 5. You are playing a one-shot coordination game with ONE other player.

The other player is an AI model. You are not told which model it is or how it was produced, and it has been told exactly the same about you.

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

## `claude` / `withheld` / `predict` - sha8 `5e31720d` (NEW)

```
You are Claude Opus 5. You are playing a one-shot coordination game with ONE other player.

The other player is an AI model. You are not told which model it is or how it was produced, and it has been told exactly the same about you.

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

## `gpt` / `copy` / `action` - sha8 `ce258781` (archived builder, never sent)

```
You are GPT-5.5. You are playing a one-shot coordination game with ONE other player.

The other player is another instance of GPT-5.5 - the same model checkpoint as you, running the same underlying policy. You have both been truthfully told this about each other.

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

## `gpt` / `copy` / `predict` - sha8 `e92b41b4` (archived builder, never sent)

```
You are GPT-5.5. You are playing a one-shot coordination game with ONE other player.

The other player is another instance of GPT-5.5 - the same model checkpoint as you, running the same underlying policy. You have both been truthfully told this about each other.

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

## `gpt` / `other` / `action` - sha8 `de185e62` (archived, sent in pilot)

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

## `gpt` / `other` / `predict` - sha8 `5835d8fe` (archived builder, never sent)

```
You are GPT-5.5. You are playing a one-shot coordination game with ONE other player.

The other player is Claude Opus 5 - a different model, running a different underlying policy. You have both been truthfully told the other's identity: they know they are playing GPT-5.5.

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

## `gpt` / `withheld` / `action` - sha8 `902f85cb` (NEW)

```
You are GPT-5.5. You are playing a one-shot coordination game with ONE other player.

The other player is an AI model. You are not told which model it is or how it was produced, and it has been told exactly the same about you.

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

## `gpt` / `withheld` / `predict` - sha8 `15c0dcf9` (NEW)

```
You are GPT-5.5. You are playing a one-shot coordination game with ONE other player.

The other player is an AI model. You are not told which model it is or how it was produced, and it has been told exactly the same about you.

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
