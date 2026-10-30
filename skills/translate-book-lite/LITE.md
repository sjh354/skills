# translate-book-lite

A fork of `translate-book` (same scripts, same pipeline, copied without git history) with a
shorter instruction set. `SKILL.md` holds the workflow; this file records what differs and why.

## What differs from translate-book

| | translate-book | lite | where |
|---|---|---|---|
| Terminology | Korean term + English gloss on first use | academic terms stay English, ordinary words translated | brief rule 2 in `scripts/make_briefs.py`, glossary step in `SKILL.md` |
| Chunk size | 6000 chars | 12000 chars | `scripts/convert.py` (`--chunk-size`) |
| Agent prompt | rules, term table, neighbours, meta schema pasted into every call | one line pointing at `<temp>/briefs/*.md` | `scripts/make_briefs.py` |
| Page-by-page audit agent | always | opt-in | `audit_brief.md` |
| Bare `\checkmark` in a table cell | dropped by pandoc, found by the audit | wrapped in math at ingest | `wrap_table_checkmarks` in `scripts/arxiv_backend.py`, `tests/test_table_checkmarks.py` |
| Unnumbered `\paragraph` taking a number from a body line; wrapped title with a glued formula "not found" | fixed in the original too | same | `scripts/latex_cleanup.py`, `tests/test_split_line_prefixes.py` |
| `SKILL.md` | 93 KB | about 10 KB | `SKILL.md` |
| Advisors, cleanup | on | off; cleanup never deletes translations | `SKILL.md` |

Not changed, because they are tool behaviour rather than instruction: `verify_chunk`, `verify_tables`,
`sidecar_edit`, the build gates and the probes.

## Tests

`python3 -m unittest discover -s tests -p "test_*.py"` from the project root.

- 2714 tests; 43 skipped; 2 fail and failed before the fork: `test_drawn_figures` (a figure-location
  fixture) and `test_bib_web_entries` (an "Accessed" date).
- **Skipped on purpose (40):** tests that assert the wording of the ORIGINAL `SKILL.md` (its step numbers,
  advisor names, the "foreground batches" sentence, the plugin copy of `SKILL.md` under
  `.claude-plugin/`). They are marked `@asserts_original_skill_md` (`tests/_lite_skip.py`), and the four
  classes of `test_plugin_skill_rules.py` are skipped as a whole, because that module ends the
  interpreter when `SKILL.md` uses `python3` or `{baseDir}` outside `python {baseDir}/<script>.py`. Lite
  is not published as a plugin. To run them, point them at the original skill's `SKILL.md`.
- Tests of script behaviour are untouched and all pass.

## Not yet verified

No full paper has been translated with lite. The untried combination is English-kept terms, 12000-char
chunks and file briefs together. If a translator's output is cut off on a long chunk, lower
`--chunk-size` (9000 is a reasonable step).
