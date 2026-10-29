#!/usr/bin/env python3
"""CSV(stdin, 첫 줄=헤더) -> 표 HTML. 숫자 열은 헤더까지 우측 정렬, **굵게** 지원."""
import csv, re, sys
from html import escape

rows = list(csv.reader(sys.stdin))
num = re.compile(r"^[\s*+\-−]*[\d.,]+\s*[%a-zA-Z가-힣]{0,3}\**$")


ncol = len(rows[0])
numeric = [all(num.match(r[i]) for r in rows[1:] if i < len(r) and r[i].strip()) for i in range(ncol)]


def cell(tag, v, i):
    b = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape(v.strip()))
    return f'<{tag}{" class=n" if numeric[i] else ""}>{b}</{tag}>'


head = "".join(cell("th", v, i) for i, v in enumerate(rows[0]))
body = "".join("<tr>" + "".join(cell("td", v, i) for i, v in enumerate(r)) + "</tr>" for r in rows[1:])
print(f'<table class="tbl"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')
