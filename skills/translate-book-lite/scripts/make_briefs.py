#!/usr/bin/env python3
"""Write one brief file per chunk (or per table sidecar) for the translator agents.

The main agent used to paste the full rules, term table, neighbour excerpts and
meta schema into every Agent call: ~2.5k tokens of output per chunk, repeated.
Here a script assembles all of it into `<temp_dir>/briefs/` and the Agent
prompt is one line pointing at the file. The translator reads it with Read,
which is not a command and so cannot be refused the way a fetch script can.

  make_briefs.py <temp_dir> --lang ko                 # chunks the planner queues
  make_briefs.py <temp_dir> --lang ko --tables        # sidecars that hold table floats
  make_briefs.py <temp_dir> --lang ko --chunks chunk0004 chunk0009   # explicit
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

LANG_NAMES = {
    'ko': 'Korean (한국어)', 'zh': 'Chinese (中文)', 'ja': 'Japanese (日本語)',
    'en': 'English', 'fr': 'French', 'de': 'German', 'es': 'Spanish',
    'pt': 'Portuguese', 'ru': 'Russian', 'it': 'Italian', 'vi': 'Vietnamese',
}

RULES = """\
## Rules

1. **Keep the Markdown structure.** Headings, links, lists, image references
   `![alt](path)` (path untouched, alt may be translated), footnote marks `[^n]`,
   code spans, URLs. Translate every heading too, at the same level.
2. **Terminology policy: academic and technical terms stay in English; translate only
   ordinary words.** A term of art that a reader in the field would search for
   (retriever, pruning, backbone, hard negative, attention, fine-tuning, ...) is written
   in English exactly as the source writes it, with the target language's particles
   attached naturally. Everything else (verbs, adjectives, general nouns, connectives,
   sentence structure) is translated. Terms in the table below follow the table;
   a table row whose "target" is the English word means "leave it in English". Do NOT add
   a parenthetical gloss for an English term, and do not invent translations for terms
   that are not in the table: if unsure whether something is a term of art, keep English.
3. **Numbers exactly as written**: `58.9` not `58,9`, `60,000` not `60.000`, no space
   before `%`. Do not convert magnitudes (`0.5 billion` stays `0.5 billion`, never 5억
   or 五亿). Only the words around a number are translated.
4. **Placeholders are sacred.** Tokens like `⟦M0042⟧`, `⟦C0007⟧`, `⟦T0003⟧` stand for
   formulas, citations and tables and are restored automatically. Copy each one
   character for character, exactly once, in the same place; never translate, renumber,
   split across lines, invent or drop one.
5. **Read like a native text, not a translation.** Split sentences that are too long;
   avoid stacked nominalisations and calqued pronouns (it/this); do not add or remove
   information.
6. **If the source itself is defective** (a dangling clause, an obvious typo that makes
   a reader pause), translate faithfully and add a short note right after it in the form
   `*[역주: ...]*` (or the equivalent in the target language). Use sparingly.
7. **Raw HTML tags** (`<img alt="...">`): inside attribute values replace `"` `'` `<`
   `>` `&` with `&quot;` `&#39;` `&lt;` `&gt;` `&amp;`. Never touch `src`/`href`.
8. **Output only the translation.** No preface, no closing remark, no code fence around
   the file. Do not delete or "tidy" lines of raw LaTeX at the top of a chunk
   (`\\pdfoutput=1`, `\\maketitle`): copy them as they are.
9. **Write files with the Write tool, never through the shell** (a heredoc strips
   backslashes). Any scratch file you need must have this chunk's id in its name.
"""

TABLE_RULES = """\
## Rules for table floats

The file holds raw LaTeX tables behind `⟦T####⟧` placeholders. Translate WORDS only:
the body of `\\caption{...}` (and its optional `[...]`); column-header cells and row
labels that are ordinary words (Method, Model, Size, Param., Avg, Total, Time, ...);
cell VALUES that are ordinary words (Mean, Average, Yes, No) as well, because a
build gate refuses a table that still carries them; prose inside `tablenotes`.
Apply the terminology policy: technical terms stay English.

Leave untouched: every number; every model, benchmark, dataset, method and metric name
(DRAMA, BEIR, nDCG@10, ...); language codes; abbreviations you cannot expand with
certainty (L-FT, EOS); all LaTeX structure (`&` and `\\\\` counts, `\\multicolumn`,
`\\multirow`, column specs, rules); `\\cite{}`, `\\label{}`, `\\ref{}` keys.

Edit ONLY through the guarded tool; never write a script of your own and never edit the
JSON by hand:

    python3 {skill}/scripts/sidecar_edit.py read  "{sidecar}"
    # write the replacement LaTeX of ONE table to a file named with "{chunk}" in it, in
    # your scratch directory, with the Write tool; then
    python3 {skill}/scripts/sidecar_edit.py write "{sidecar}" --token T#### \\
        --expect <sha256 from your latest read> --latex-file <that file>

The sha256 changes after every accepted write: read again before the next token. If a
write is refused, re-read and redo the edit from the fresh text. Report which tokens
you changed.
"""


def run(script, *args):
    out = subprocess.run([sys.executable, os.path.join(HERE, script), *args],
                         capture_output=True, text=True)
    return out.stdout.strip()


def planned_chunks(temp_dir):
    plan = json.loads(run('run_state.py', 'plan', temp_dir))
    return plan['translation_chunk_ids']


def table_sidecars(temp_dir):
    found = []
    for name in sorted(os.listdir(temp_dir)):
        if not name.endswith('.math.json'):
            continue
        try:
            data = json.load(open(os.path.join(temp_dir, name), encoding='utf-8'))
        except (OSError, ValueError):
            continue
        spans = data.get('spans', data) if isinstance(data, dict) else data
        if any(isinstance(s, dict) and s.get('kind') == 'float' for s in spans):
            found.append(name[:-len('.math.json')])
    return found


def chunk_brief(temp_dir, chunk, lang):
    terms = run('glossary.py', 'print-terms-for-chunk', temp_dir, chunk + '.md')
    context = run('chunk_context.py', temp_dir, chunk + '.md')
    meta = run('meta.py', 'prompt-block')
    parts = [
        '# Translation brief for %s' % chunk, '',
        'Translate `%s/%s.md` into %s and write it to `%s/output_%s.md`; then write the '
        'meta file `%s/output_%s.meta.json`.' % (
            temp_dir, chunk, LANG_NAMES.get(lang, lang),
            temp_dir, chunk, temp_dir, chunk), '',
        RULES,
    ]
    if terms:
        parts += ['## Term table', '',
                  'A term listed here (source column or alias column) is rendered exactly '
                  'as the target column says. A target equal to the source means: keep it '
                  'in English.', '', terms, '']
    if context:
        parts += ['## Neighbouring text (read-only)', '',
                  'Only for pronouns, names and cross-chunk references. Do not translate '
                  'it and do not copy it into the output.', '', context, '']
    parts += ['## Meta file', '', meta, '',
              'A filled example for `new_entities`: `{"source": "retriever", '
              '"target_proposal": "retriever", "category": "concept", "evidence": '
              '"<verbatim quote of at most 200 characters>"}`. `used_term_sources` holds '
              'plain strings. An empty meta is a correct answer. An `evidence` string is '
              'checked against the chunk: copy the span exactly, placeholders and '
              'citation brackets included, escape backslashes in JSON; if you cannot copy '
              'one exactly, leave it empty.', '',
              'Finish by replying with one line: the two files written.']
    return '\n'.join(parts)


def table_brief(temp_dir, chunk, lang, skill):
    sidecar = os.path.join(temp_dir, chunk + '.math.json')
    terms = run('glossary.py', 'print-terms-for-chunk', temp_dir, chunk + '.md')
    parts = ['# Table brief for %s' % chunk, '',
             'Translate the table words of `%s` into %s.' % (
                 sidecar, LANG_NAMES.get(lang, lang)), '',
             TABLE_RULES.replace('{skill}', skill).replace('{sidecar}', sidecar)
             .replace('{chunk}', chunk)]
    if terms:
        parts += ['## Term table', '', terms]
    return '\n'.join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('temp_dir')
    ap.add_argument('--lang', required=True)
    ap.add_argument('--tables', action='store_true',
                    help='write table briefs for sidecars that hold float tables')
    ap.add_argument('--chunks', nargs='*', help='explicit chunk ids instead of the plan')
    args = ap.parse_args()

    temp_dir = os.path.abspath(args.temp_dir)
    out_dir = os.path.join(temp_dir, 'briefs')
    os.makedirs(out_dir, exist_ok=True)
    skill = os.path.dirname(HERE)

    chunks = args.chunks or (table_sidecars(temp_dir) if args.tables
                             else planned_chunks(temp_dir))
    written = []
    for chunk in chunks:
        if args.tables:
            text, name = table_brief(temp_dir, chunk, args.lang, skill), \
                'tables_%s.md' % chunk
        else:
            text, name = chunk_brief(temp_dir, chunk, args.lang), '%s.md' % chunk
        path = os.path.join(out_dir, name)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text + '\n')
        written.append(path)
    print(json.dumps({'briefs': written}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
