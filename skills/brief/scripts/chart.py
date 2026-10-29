#!/usr/bin/env python3
"""JSON(stdin 또는 파일) -> 막대/선 차트 SVG(stdout). 좌표는 값에서만 계산한다."""
import json, math, sys
from xml.sax.saxutils import escape

W, H = 640, 400
L, R, T, B = 76, 24, 52, 64
PW, PH = W - L - R, H - T - B


def nice_ticks(lo, hi, n=5):
    span = (hi - lo) or 1
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    start = math.floor(lo / step) * step
    ticks = []
    v = start
    while v < hi + step * 0.999:
        ticks.append(round(v, 10))
        v += step
        if ticks[-1] >= hi:
            break
    return ticks


def fmt(v):
    return f"{v:g}"


def render(spec):
    kind = spec.get("type", "bar")
    labels = spec["labels"]
    series = spec["series"]
    vals = [v for s in series for v in s["values"]]
    lo = spec.get("ymin", 0 if kind == "bar" else min(vals))
    hi = spec.get("ymax", max(vals))
    if kind == "bar":
        lo = min(lo, 0)
    ticks = nice_ticks(lo, hi)
    lo, hi = ticks[0], ticks[-1]

    def y(v):
        return T + PH * (1 - (v - lo) / (hi - lo))

    n, k = len(labels), len(series)
    band = PW / n
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
           f'style="font-family:inherit;font-size:19px;fill:var(--ink)">']
    if spec.get("title"):
        out.append(f'<text x="{L}" y="26" style="font-weight:700;font-size:22px">{escape(spec["title"])}</text>')
    unit = spec.get("unit", "")
    for t in ticks:
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{y(t):.1f}" y2="{y(t):.1f}" style="stroke:var(--grid)"/>')
        out.append(f'<text x="{L-8}" y="{y(t)+5:.1f}" text-anchor="end" style="fill:var(--muted)">{fmt(t)}</text>')
    if unit:
        out.append(f'<text x="{L-8}" y="{T-12}" text-anchor="end" style="fill:var(--muted)">{escape(unit)}</text>')
    out.append(f'<line x1="{L}" x2="{L}" y1="{T}" y2="{T+PH}" style="stroke:var(--ink)"/>')
    base = y(max(lo, 0)) if kind == "bar" else T + PH
    out.append(f'<line x1="{L}" x2="{W-R}" y1="{base:.1f}" y2="{base:.1f}" style="stroke:var(--ink)"/>')

    for i, lab in enumerate(labels):
        cx = L + band * (i + 0.5)
        out.append(f'<text x="{cx:.1f}" y="{T+PH+28}" text-anchor="middle">{escape(str(lab))}</text>')

    by_cat = kind == "bar" and k == 1 and spec.get("color_by") != "series"
    for j, s in enumerate(series):
        col = f"var(--c{j % 6 + 1})"
        if kind == "bar":
            bw = band * 0.7 / k
            for i, v in enumerate(s["values"]):
                x = L + band * i + band * 0.15 + bw * j
                top, bot = sorted((y(v), y(0)))
                c = f"var(--c{i % 6 + 1})" if by_cat else col
                out.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{bot-top:.1f}" style="fill:{c}"/>')
                out.append(f'<text x="{x+bw/2:.1f}" y="{top-6:.1f}" text-anchor="middle" style="font-size:19px">{fmt(v)}</text>')
        else:
            pts = [(L + band * (i + 0.5), y(v)) for i, v in enumerate(s["values"])]
            out.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" style="fill:none;stroke:{col};stroke-width:3"/>')
            for (a, b), v in zip(pts, s["values"]):
                out.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4.5" style="fill:{col}"/>')
                out.append(f'<text x="{a:.1f}" y="{b-10:.1f}" text-anchor="middle" style="font-size:19px">{fmt(v)}</text>')

    if k > 1:
        x = L
        for j, s in enumerate(series):
            out.append(f'<rect x="{x}" y="{H-18}" width="14" height="14" style="fill:var(--c{j % 6 + 1})"/>')
            out.append(f'<text x="{x+20}" y="{H-6}">{escape(s["name"])}</text>')
            x += 44 + 15 * len(s["name"])
    out.append("</svg>")
    return "\n".join(out)


def _selfcheck():
    import re
    svg = render({"type": "bar", "labels": ["a", "b"], "series": [{"name": "s", "values": [10, 20]}]})
    h = [float(m) for m in re.findall(r'<rect [^>]*height="([\d.]+)"', svg)]
    assert abs(h[1] / h[0] - 2) < 0.02, h
    assert nice_ticks(0, 87)[-1] >= 87


if __name__ == "__main__":
    if sys.argv[1:] == ["--selfcheck"]:
        _selfcheck()
        print("ok")
    else:
        print(render(json.load(open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin)))
