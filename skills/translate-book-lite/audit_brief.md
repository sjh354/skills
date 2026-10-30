# Audit brief (opt-in): compare the built book with the original, page by page

You are a read-only auditor. Compare the built translated PDF with the ORIGINAL PDF by looking at
rendered page IMAGES, not text dumps: a header over the wrong column extracts identically to one
over the right column.

Inputs (given in the prompt): `temp_dir` (absolute), `original_pdf` (absolute).
Built PDF: `<temp_dir>/book.pdf`. Context: `<temp_dir>/output.md`, `flat.tex`, `chunk*.math.json`.
Scratch: `<temp_dir>/pages/`. Change nothing except PNGs there.

Render with the skill's script, run as written (use `python3` if `python` does not exist):

    python3 <skill>/scripts/render_pages.py "<temp_dir>/book.pdf" "<temp_dir>/pages" --prefix audit_tr
    python3 <skill>/scripts/render_pages.py "<original_pdf>" "<temp_dir>/pages" --prefix audit_src

Then view the PNGs with the Read tool. Do not write a render script of your own.

## Report

A. **Tables, algorithms and figures**, each: original page, translated page, and either "matches"
   or a numbered list of concrete differences quoting the original cell and the translated cell.
   Look at: column and row counts; group-header spans; row labels; footnote marks and notes;
   superscripts; **symbols in cells** (check marks, crosses, stars: an empty cell where the original
   has a symbol reads as "not applicable"); bold, underline or colour that a caption refers to;
   header alignment; horizontal rules; cells squeezed unreadable.
B. **Whole book**, one line per translated page ("p7: clean" or "p7: <what is wrong>"): heading
   numbers the original does not have or lacks; markup that reached the reader (`\command`, `$`,
   `:::`, `{=latex}`, `[@key]`, `(tab:x)`, `??`, HTML tags, `<!--`, `↩︎`); reference list present;
   authors named on the title page; equations overflowing or colliding with their number; raw
   label strings like `Figure (fig:x)` surviving.
C. Findings ranked by reader impact, each with page and quote.
D. What you could NOT verify. An audit that lists only findings is indistinguishable from one that
   stopped early, so state what you covered.

The caller checks every finding against the original before changing anything. Many findings are
the paper's own spelling (a URL, an unnumbered heading); say what the original does, not only what
the book does.
