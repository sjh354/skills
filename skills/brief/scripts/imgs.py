#!/usr/bin/env python3
"""이미지 그리드 HTML. 사용: imgs.py COLS 경로[|캡션] ... (경로는 덱 html 기준 상대/절대)"""
import sys
from html import escape

cols, items = sys.argv[1], sys.argv[2:]
figs = []
for it in items:
    path, _, cap = it.partition("|")
    figs.append(f'<figure><img src="{escape(path)}">' + (f"<figcaption>{escape(cap)}</figcaption>" if cap else "") + "</figure>")
print(f'<div class="imgs" style="--cols:{cols}">' + "".join(figs) + "</div>")
