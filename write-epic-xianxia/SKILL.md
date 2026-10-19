---
name: write-epic-xianxia
description: Write, revise, outline, or diagnose original Chinese epic-xianxia and cultivation-fiction scenes using a corpus-derived workflow for monumental scale, progressive revelation, combat escalation, power feedback, rhythmic sentence contrast, and chapter hooks. Use for original xianxia chapters, battle scenes, exploration scenes, realm breakthroughs, ancient mysteries, serialized-fiction pacing, or editing prose that feels flat, repetitive, or insufficiently dramatic.
---

# Write Epic Xianxia

Create original Chinese serialized fantasy using abstract narrative techniques derived from a long-form corpus. Never reproduce source characters, settings, terminology, plot events, signature lines, or recognizable passages.

## Load the profile

Read [references/style-profile.md](references/style-profile.md) and [references/source-exclusions.md](references/source-exclusions.md) before drafting or revising. Read [references/evaluation-rubric.md](references/evaluation-rubric.md) before evaluating a draft. Read [references/corpus-notes.md](references/corpus-notes.md) only when the user asks how the profile was derived or requests corpus statistics.

## Establish the brief

Collect or infer:

- the viewpoint character and immediate objective;
- the obstacle and cost of failure;
- the current power ceiling and what remains unknown;
- the scene type: discovery, confrontation, breakthrough, pursuit, revelation, or aftermath;
- the target length and desired ending hook.

Invent missing details when the user permits creative freedom. Keep all names, systems, objects, factions, cosmology, and plot events original.

## Plan before drafting

Write a private five-beat scene plan:

1. Anchor the viewpoint in one concrete perception or decision.
2. Reveal an abnormal detail that changes the local situation.
3. Escalate through two or three qualitatively different consequences.
4. Deliver a payoff through action, discovery, or irreversible cost.
5. End on a changed question, threat, choice, or scale.

Do not merely increase adjective intensity. Make each escalation alter knowledge, agency, danger, or cost.

## Draft

Apply the profile conditionally:

- Alternate explanatory or spatially expansive sentences with short impact lines.
- Keep most paragraphs focused on one action, perception, reaction, or claim.
- Translate power into visible consequences on bodies, terrain, objects, witnesses, or choices.
- Use observer reactions only when they convey new information about scale or stakes.
- Couple spectacle to character agency; the viewpoint character must decide, risk, infer, or pay.
- Reserve exclamation marks and isolated fragments for real turning points.
- Use a scale ladder instead of stacked grandeur adjectives.
- Let chapter titles be compact and event-bearing; do not reuse source titles.

## Revise in three passes

### Story pass

Verify causal continuity, character agency, readable spatial relations, and a changed situation at the end.

### Rhythm pass

Break monotonous sentence runs. Remove repeated transition markers, reaction formulas, adjective piles, and interchangeable impact sentences.

### Originality pass

Remove source-specific names, cosmology, artifacts, catchphrases, plot structures, and recognizable imagery. If the source EPUB is available, run:

```bash
python3 scripts/check_similarity.py SOURCE.epub CANDIDATE.txt
```

Rewrite any exact overlap of 24 or more normalized characters unless it is unavoidable common language. Treat the script as a warning system, not a complete copyright determination.

Also perform the motif-cluster check in [references/source-exclusions.md](references/source-exclusions.md). Reject renamed combinations of multiple distinctive source elements even when no sentence overlaps.

## Evaluate

Score with [references/evaluation-rubric.md](references/evaluation-rubric.md). Revise any dimension below 3/5. Originality must be 5/5 before delivery.

Return only the requested artifact unless the user asks for the plan, profile, or evaluation.
