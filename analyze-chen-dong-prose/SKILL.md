---
name: analyze-chen-dong-prose
description: Analyze Chinese prose against aggregate narrative and language traits derived from the user-supplied novel 《遮天》, including sentence rhythm, paragraph structure, dialogue density, scale construction, progressive revelation, combat feedback, serialized chapter hooks, and exact-overlap risk. Use for author-specific literary analysis, corpus measurement, passage comparison, style diagnosis, or explaining why a draft does or does not resemble the analyzed work. Do not use to generate a high-fidelity imitation of a living author's style.
---

# Analyze Chen Dong Prose

Analyze rather than imitate. Base claims on measurable evidence and the supplied framework. Separate corpus facts, interpretive inferences, and uncertain judgments.

## Choose the task

### Analyze an EPUB

Run:

```bash
python3 scripts/analyze_epub.py SOURCE.epub --output analysis.json
```

Compare the output with [references/corpus-statistics.md](references/corpus-statistics.md). Explain edition differences and parsing limitations.

### Analyze a passage

Read [references/analysis-rubric.md](references/analysis-rubric.md). Measure or estimate each dimension, cite short user-provided excerpts only when necessary, and label each conclusion as:

- measured;
- strongly evidenced;
- plausible interpretation;
- unsupported.

Do not reduce style to adjective lists. Explain how linguistic choices perform narrative work.

### Compare a draft

Score the draft against the rubric. Identify no more than five high-impact differences. Recommend abstract changes such as sentence-function contrast, scale sequencing, clearer action consequences, or stronger chapter turns.

Do not rewrite the passage as a high-fidelity imitation. If the user wants original genre writing using abstract traits, route to `$write-epic-xianxia`.

### Check exact overlap

When the source EPUB is available, run:

```bash
python3 scripts/check_similarity.py SOURCE.epub CANDIDATE.txt
```

Treat exact overlap of 24 or more normalized characters as a review trigger. Common phrases can produce false positives; absence of a match does not prove originality.

## Reporting format

Return:

1. scope and evidence;
2. measured observations;
3. narrative interpretation;
4. strongest similarities;
5. strongest differences;
6. uncertainty and limitations.

Never package the source text or reproduce long excerpts.
