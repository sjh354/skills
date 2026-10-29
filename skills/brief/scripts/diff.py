#!/usr/bin/env python3
"""diff(stdin) -> 빨강/초록 블록 HTML(stdout). 파일명·헤더는 버리고 hunk·빈 줄 사이만 한 줄 띄운다(-/+ 블록은 붙임). 예: git diff -U0 | diff.py"""
import sys
from html import escape

HEADERS = ("diff ", "index ", "--- a/", "+++ b/", "--- /dev", "+++ /dev", "Binary files ", "GIT binary patch")
rows = []
for ln in sys.stdin.read().splitlines():
    if ln.startswith(HEADERS):
        continue
    if ln.startswith("@@") or not ln.strip():
        if rows and rows[-1] != "gap":
            rows.append("gap")
        continue
    c = "add" if ln.startswith("+") else "del" if ln.startswith("-") else "ctx"
    rows.append(f'<span class="{c}">{escape(ln)}</span>')
while rows and rows[-1] == "gap":
    rows.pop()
print('<pre class="diff">' + "".join('<span class="gap"> </span>' if r == "gap" else r for r in rows) + "</pre>")
