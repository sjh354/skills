---
name: translate-book-lite
description: Lean fork of translate-book. Translates an arXiv paper (or PDF/DOCX/EPUB) into Korean or another language as a printable book, keeping academic terms in English and translating only ordinary words. Reads the LaTeX source so equations, tables and figures survive. Larger chunks, file-based agent briefs, the page-by-page audit is opt-in.
allowed-tools: Read, Edit(./**), Bash(python *), Bash(python3 *), Glob, Grep, Agent, AskUserQuestion
---

# translate-book-lite

Same pipeline and scripts as `translate-book`, with a shorter instruction set. Differences:

| | translate-book | lite |
|---|---|---|
| Terminology | Korean term + English gloss on first use | **academic terms stay English, only ordinary words are translated** |
| Chunk size | 6000 chars | **12000 chars** |
| Agent prompts | rules + term table pasted into every call | **one brief file per chunk** (`make_briefs.py`), the prompt is one line |
| Page-by-page audit agent | always | **only when asked** (`{baseDir}/audit_brief.md`) |
| Check-mark cells (`\checkmark`) | dropped by pandoc, found by the audit | **fixed at ingest** |
| Advisors, referee prose, cleanup | on | off; cleanup never deletes translations |

Look things up instead of reading the logs whole:
`python3 {baseDir}/scripts/kb.py find "<symptom or command>"`.

## How to run commands

- Every command below is one of this skill's scripts, by absolute path. Run each as written.
  This machine may have only `python3`; use whichever of `python`/`python3` exists.
- **Never `cd` into the temp dir and never leave the project root.** `config.txt` records the
  source PDF by a relative path; a build run from elsewhere prints "Sections: not numbered"
  and ships a book without section numbers. Use absolute paths, no `cd`, no pipes.
- Files go through Read/Write/Edit/Glob/Grep, not `cat`/`echo`/heredocs (a heredoc strips
  backslashes out of LaTeX). A check no script gives: write a `.py` file to the scratchpad and
  run it with `python3 -I`; never `python -c`.
- Agent calls may return at once and report later: wait for the completion notices and do
  not poll. A report is not evidence; the file it wrote is (step 4).

## Workflow

### 0. Preflight
`python3 {baseDir}/scripts/doctor.py --strict`. A `MISSING` line (pandoc, PyMuPDF): stop and
tell the user what to install; nothing is converted. `absent` lines (Calibre = no EPUB, fonts,
advisor agents) are reported and ignored. The `translator` agent should exist
(`python3 {baseDir}/scripts/install_advisors.py` installs it); otherwise use general-purpose.

### 1. Parameters
file path (ask if missing); target language (default `ko`); concurrency 8; chunk size 12000;
custom instructions. A licence matters only if the user will publish the translation.

### 2. Convert
For an arXiv paper the LaTeX-source backend is the only one that keeps equations. It downloads
from arxiv.org, so ask once before passing `--allow-network`:
`python3 {baseDir}/scripts/convert.py "<pdf>" --olang <lang> --allow-network`
Creates `<name>_temp/` (chunks, `*.math.json` sidecars, `flat.tex`, `manifest.json`).
The reference list becomes its own chunk, already copied, never translated.
Without `--allow-network` the PDF goes through Calibre, which loses every equation.

### 3. Glossary (decide terminology BEFORE translating)
Read every chunk if there are at most 8, otherwise the first, the last and six evenly spaced.
Write `<temp>/glossary.json` (v2 schema: `terms[]` with `id, source, target, category, aliases,
gender, confidence, frequency, evidence_refs, notes`, plus `high_frequency_top_n: 20` and
`applied_meta_hashes: {}`).

- **Terms of art: `target` = the English `source`.** Anything a reader in the field would search
  for: method, model, metric and dataset names, and the field's vocabulary (retriever, pruning,
  backbone, hard negative, fine-tuning, attention, ...). Include inflected forms as `aliases`.
- **Ordinary words: not in the glossary**, except where one choice must stay consistent across
  chunks (e.g. "task" -> one Korean word). One word, one job; one term, one spelling.
- A term kept in English also keeps its bare/compound relatives in English (`power law` if
  `truncated power law` stays English).
Then `python3 {baseDir}/scripts/glossary.py count-frequencies "<temp>"`. Settle the glossary
now: every later edit re-translates each chunk that uses the term.

### 4. Plan, dry run, translate
1. `python3 {baseDir}/scripts/run_state.py plan "<temp>"`. `record_only_chunk_ids` (the
   reference list) go through verify (below) and `run_state.py record`.
2. `python3 {baseDir}/tests/dry_run.py "<temp>" --lang <lang>`: builds the untranslated
   paper to expose structural defects while they are cheap. Expected, ignore: "N failed"
   (chunks are untranslated), no EPUB without Calibre, a table-count warning when headers
   nest `tabular`s, an equation-count mismatch when the source has `\nonumber`.
   Anything else: read the output in full and decide before translating.
3. Briefs: `python3 {baseDir}/scripts/make_briefs.py "<temp>" --lang <lang>` writes
   `<temp>/briefs/chunkNNNN.md` (rules, term table, neighbour text, meta schema).
4. Dispatch one `translator` agent per chunk, up to 8 per message. The whole prompt is:
   `Follow the brief at <temp>/briefs/chunkNNNN.md exactly. It names every file to read and write.`
5. As each chunk lands, in this order:
   `python3 {baseDir}/scripts/verify_chunk.py "<temp>" --lang <lang> --strict chunkNNNN ...`
   then, for passes, `run_state.py record "<temp>" chunkNNNN ...`, then step 5.
   A failure is re-dispatched (not patched) with the finding quoted: "Your previous
   translation of chunkNNNN.md was rejected: <finding>. Follow the brief and rewrite the whole
   file." Two rejections: stop and report that chunk.

### 5. Merge the meta
`merge_meta.py prepare-merge "<temp>"`; resolve any `decisions_needed`; write
`<temp>/merge_decisions.json` (`{"auto_apply": [...], "decisions": [...], "consumed_chunk_ids":
[...]}`) with Write; `merge_meta.py apply-merge "<temp>" --decisions "<temp>/merge_decisions.json"`.
Empty proposals still need the apply, or the hashes are never recorded. Read `auto_apply`
first: a new term spelled differently from a canonical one is a defect in the making.

### 6. Tables (captions, headers and ordinary-word cells are invisible to chunk translators)
1. `python3 {baseDir}/scripts/verify_tables.py snapshot "<temp>"`  (BEFORE anything edits them)
2. `python3 {baseDir}/scripts/make_briefs.py "<temp>" --lang <lang> --tables`
3. One `translator` agent per listed sidecar: `Follow the brief at <temp>/briefs/tables_chunkNNNN.md exactly.`
   They edit only through `sidecar_edit.py` (guarded against stale and renumbering writes).
4. `python3 {baseDir}/scripts/verify_tables.py check "<temp>" --strict`.
After any sidecar edit **delete `<temp>/output.md`** before building, or the book keeps the old text.

### 7. Whole-book gate
`verify_chunk.py "<temp>" --lang <lang> --strict --quiet` (every chunk must pass);
`merge_meta.py status "<temp>"`; `referee.py tally "<temp>" --lang <lang>` then `record`.

### 8. Title and build (from the project root)
Read `original_title` in `<temp>/config.txt`, translate it, then
`python3 {baseDir}/scripts/merge_and_build.py --temp-dir "<temp>" --title "<translated title>"`.
The build refuses on: tables or math that did not render, a placeholder a translator dropped,
untranslated table captions, headers or ordinary-word cells (fix through `sidecar_edit.py`,
delete `output.md`, rebuild with `--force-html`). Outputs: `book.pdf`, `book.docx`,
`book.html`, `book_doc.html`, `book.epub` (only with Calibre), `output.md`.

### 9. Probes (always; seconds, almost no tokens)
```
python3 {baseDir}/tests/table_probe.py "<temp>" --lang <lang> --strict
python3 {baseDir}/tests/consistency_probe.py "<temp>" --lang <lang> --strict
python3 {baseDir}/tests/leak_probe.py "<temp>" --strict
python3 {baseDir}/tests/inventory_probe.py "<temp>" --lang <lang> --strict
python3 {baseDir}/tests/source_probe.py "<temp>" --strict
python3 {baseDir}/tests/format_probe.py "<temp>" --lang <lang> --strict
```
Known benign failures: `format_probe` "epub was never produced" without Calibre; `source_probe`
"equation count" when the source says `\nonumber`. `consistency_probe` "data values lost" means a
translator respelled a number (e.g. `0.5 billion` -> 5억): restore the source spelling in
`output_chunkNNNN.md`, re-verify, `run_state.py record` it, delete `output.md`, rebuild.
Split renderings (two words for one term) are fixed the same way, in the chunk outputs, never in
`output.md` (a re-merge overwrites it).

### 10. Audit (opt-in)
Not run by default. Offer it in the final report when the paper has many tables or symbol cells
(check marks, bold/underline meaning), or run it when the user asks: spawn one general-purpose
agent with `Follow {baseDir}/audit_brief.md. temp_dir=<abs temp>, original_pdf=<abs original>.`
It renders both PDFs and compares pages as images. Check each finding against the ORIGINAL before
changing anything: a finding is a lead, not a verdict. Fix causes upstream (glossary, brief, ingest
code), not the page.

### 11. Report
Say, separately: files and sizes; chunks translated and retried; title; what each gate said,
with numbers; known benign failures; residual defects. Do not claim anything unchecked.
Do not delete the temp dir: chunk translations are not cheap to regenerate. If the user wants it
cleaned, `merge_and_build.py --temp-dir "<temp>" --cleanup-only` keeps sidecars and `output.md`.

## Repairs (never re-convert)
Re-converting renumbers every placeholder and discards the translation. Fix in place: back up
`chunk*.md`, `output_chunk*.md`, `*.math.json`; patch the translated chunk and its source together;
`repair.py rehash "<temp>"`; `run_state.py record`; check `run_state.py plan` queues nothing;
delete `output.md`; rebuild with `--force-html`.

## Findings
New tool behaviour or a method that cost rework goes into `{baseDir}/KNOWLEDGE.md` (K) or
`KNOWHOW.md` (H) with a row in the symptom index; `python3 {baseDir}/scripts/kb.py check` must pass.
An empty diff is fine.
