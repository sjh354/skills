"""Reusable draw.io flow primitives."""
from xml.sax.saxutils import escape


def attr(value):
    return escape(str(value), {'"': '&quot;'})

STYLE = {
    'screen': 'rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=14;',
    'action': 'rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;',
    'result': 'rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#999999;',
    'decision': 'rhombus;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;',
    'start': 'ellipse;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;',
    'ok': 'ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;',
    'done': 'rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;',
    'stop': 'ellipse;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;',
    'note': 'text;html=1;align=left;verticalAlign=top;fontColor=#666666;fontSize=12;',
    'title': 'text;html=1;align=left;verticalAlign=top;fontSize=20;fontStyle=1;',
}
EDGE = 'edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;fontSize=11;labelBackgroundColor=#ffffff;'


class Flow:
    def __init__(self):
        self.cells = []
        self.ids = {'0', '1'}
        self.edges = []

    def node(self, id_, label, kind, x, y, w, h):
        if id_ in self.ids:
            raise ValueError(f'duplicate cell id: {id_}')
        self.ids.add(id_)
        id_ = attr(id_)
        v = attr(label.replace('\n', '<br>'))
        self.cells.append(f'<mxCell id="{id_}" value="{v}" style="{STYLE[kind]}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

    def edge(self, src, dst, label='', extra='', points=()):
        n = len(self.cells)
        edge_id = f'edge-{n}'
        if edge_id in self.ids:
            raise ValueError(f'duplicate cell id: {edge_id}')
        self.ids.add(edge_id)
        self.edges.append((src, dst))
        pts = ''.join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points)
        geo = f'<Array as="points">{pts}</Array>' if pts else ''
        self.cells.append(f'<mxCell id="{edge_id}" value="{attr(label)}" style="{EDGE}{attr(extra)}" edge="1" parent="1" '
                          f'source="{attr(src)}" target="{attr(dst)}"><mxGeometry relative="1" as="geometry">{geo}</mxGeometry></mxCell>')

    def save(self, path, title):
        if any(src not in self.ids or dst not in self.ids for src, dst in self.edges):
            raise ValueError('edge references an unknown node')
        body = ''.join(self.cells)
        xml = (f'<mxfile host="drawio"><diagram id="flow" name="{attr(title)}">'
               f'<mxGraphModel grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
               f'page="0" pageScale="1" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
               f'{body}</root></mxGraphModel></diagram></mxfile>\n')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(xml.replace('<mxCell', '\n<mxCell'))
