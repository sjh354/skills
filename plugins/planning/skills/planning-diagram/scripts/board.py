"""Reusable Excalidraw board primitives."""
import json, random

INK, MUTED, LINE, FILL, ACCENT, BADGE = '#1e1e1e', '#868e96', '#ced4da', '#f1f5f9', '#1e3a5f', '#e03131'


def _base(kind, x, y, w, h, **kw):
    e = dict(id=f'{kind}-{random.getrandbits(40):x}', type=kind, x=x, y=y, width=w, height=h, angle=0,
             strokeColor=INK, backgroundColor='transparent', fillStyle='solid', strokeWidth=1,
             strokeStyle='solid', roughness=1, opacity=100, groupIds=[], frameId=None, roundness=None,
             seed=random.getrandbits(31), version=1, versionNonce=random.getrandbits(31), isDeleted=False,
             boundElements=None, updated=1, link=None, locked=False)
    e.update(kw)
    return e


def text_width(s, size):
    return max(sum(size * (1.0 if ord(c) > 0x2E80 else 0.58) for c in line) for line in s.split('\n'))


class Board:
    def __init__(self):
        self.el = []

    def rect(self, x, y, w, h, fill=None, dashed=False, stroke=INK, round_=True, width=1):
        self.el.append(_base('rectangle', x, y, w, h, backgroundColor=fill or 'transparent', strokeColor=stroke,
                             strokeStyle='dashed' if dashed else 'solid', strokeWidth=width,
                             roundness={'type': 3} if round_ else None))

    def ellipse(self, x, y, w, h, fill=None, stroke=INK):
        self.el.append(_base('ellipse', x, y, w, h, backgroundColor=fill or 'transparent', strokeColor=stroke))

    def text(self, x, y, s, size=16, color=INK, align='left'):
        w, lines = text_width(s, size), s.count('\n') + 1
        self.el.append(_base('text', x, y, w, size * 1.25 * lines, strokeColor=color, text=s, originalText=s,
                             fontSize=size, fontFamily=2, textAlign=align, verticalAlign='top',
                             containerId=None, autoResize=True, lineHeight=1.25))
        return w

    def button(self, x, y, w, h, label, primary=False, size=15):
        self.rect(x, y, w, h, fill=ACCENT if primary else '#ffffff', stroke=ACCENT if primary else INK)
        tw = text_width(label, size)
        self.text(x + (w - tw) / 2, y + (h - size * 1.25) / 2, label, size, '#ffffff' if primary else INK)

    def field(self, x, y, w, h, placeholder, size=15):
        self.rect(x, y, w, h, fill='#ffffff')
        self.text(x + 10, y + (h - size * 1.25) / 2, placeholder, size, MUTED)

    def arrow(self, x1, y1, x2, y2, color=MUTED):
        self.el.append(_base('arrow', x1, y1, x2 - x1, y2 - y1, strokeColor=color, points=[[0, 0], [x2 - x1, y2 - y1]],
                             lastCommittedPoint=None, startBinding=None, endBinding=None,
                             startArrowhead=None, endArrowhead='arrow', roundness={'type': 2}))

    def lines(self, x, y, w, n, gap=14):
        for i in range(n):
            self.rect(x, y + i * gap, w * (0.62 if i % 5 == 4 else 1), 5, fill=LINE, stroke=LINE, round_=False)

    def badge(self, x, y, n):
        self.ellipse(x, y, 28, 28, fill=BADGE, stroke=BADGE)
        self.text(x + 9, y + 4, str(n), 16, '#ffffff')

    def title(self, s, sub):
        self.text(0, -78, s, 28)
        self.text(0, -38, sub, 15, MUTED)

    def save(self, path):
        doc = dict(type='excalidraw', version=2, source='https://excalidraw.com', elements=self.el,
                   appState=dict(gridSize=None, viewBackgroundColor='#ffffff'), files={})
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
