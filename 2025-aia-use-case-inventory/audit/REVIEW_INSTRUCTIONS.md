# Audit Review Instructions

All audit outputs should be concise, evidence-based, and written to the `audit/` tree.

## Source Reviewers

Each source reviewer owns exactly one output file in `audit/reviews/`.

Required structure:

1. `Source`
2. `Counts`
3. `Findings`
4. `Recommended follow-up`

Within `Findings`, focus on:
- source row count vs loaded DB row count
- whether the loaded rows preserve the source meaning
- whether tags look directionally correct for the file
- concrete examples of mislabeled or suspicious rows
- any header, parsing, or schema issues

Do not edit the database.
Do not edit any other agent's files.

## Consistency Reviewers

Each consistency reviewer owns exactly one output file in `audit/consistency/`.

Required structure:

1. `Check`
2. `Method`
3. `Findings`
4. `Examples`
5. `Recommended follow-up`

Keep results queryable and specific. Prefer file names, row ids, and short SQL evidence over broad prose.
