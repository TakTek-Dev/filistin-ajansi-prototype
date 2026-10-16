"""Four logo options for Filistin Ajansı (client round 1: no triangle, several options).

python -I tools/logos.py   (from the project root)

Every option is drawn from Montserrat outlines, so the files do not depend on a webfont.
Each option has: colour lockup, white lockup (for the red header), avatar, favicon.
Writes assets/brand/secenek-*.svg and tools/out/logos.json (inline header versions).
"""
import json, math, os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'research', 'font-src', 'Montserrat-VF.ttf')
RED, BLACK, GREEN, WHITE, INK = '#CE1126', '#111111', '#0B7A3E', '#FFFFFF', '#111111'

_cache = {}
def font(w):
    if w not in _cache:
        _cache[w] = instancer.instantiateVariableFont(TTFont(SRC), {'wght': w})
    return _cache[w]

class Text:
    """Lays out a string in one weight; returns path data, width and per-glyph boxes."""
    def __init__(self, s, w=800, size=100, track=0):
        f = font(w); gs = f.getGlyphSet(); cmap = f.getBestCmap(); hmtx = f['hmtx']
        k = size / f['head'].unitsPerEm
        self.cap = f['OS/2'].sCapHeight * k
        self.xh = f['OS/2'].sxHeight * k
        x = 0; parts = []; self.boxes = []
        kern = {}
        for i, ch in enumerate(s):
            g = cmap[ord(ch)]
            pen = SVGPathPen(gs)
            gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, 0)))
            parts.append(pen.getCommands())
            bp = BoundsPen(gs); gs[g].draw(bp)
            b = bp.bounds or (0, 0, 0, 0)
            self.boxes.append((x + b[0] * k, -b[3] * k, x + b[2] * k, -b[1] * k))
            x += hmtx[g][0] * k + (track if i < len(s) - 1 else 0)
        self.d = ''.join(parts); self.w = x

def svg(vb, body, title='Filistin Ajansı'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="{title}"><title>{title}</title>{body}</svg>'

def leaf(cx, cy, length, angle, fill):
    """An olive leaf: a long vesica, slightly asymmetric, pointed at both ends."""
    L = length; Wd = L * 0.36
    a = math.radians(angle)
    def rot(px, py):
        return (cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a))
    p0 = rot(-L / 2, 0); p1 = rot(L / 2, 0)
    c1 = rot(-L * 0.18, -Wd); c2 = rot(L * 0.22, -Wd * 0.9)
    c3 = rot(L * 0.2, Wd * 0.8); c4 = rot(-L * 0.2, Wd)
    return (f'<path fill="{fill}" d="M{p0[0]:.1f} {p0[1]:.1f}C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p1[0]:.1f} {p1[1]:.1f}'
            f'C{c3[0]:.1f} {c3[1]:.1f} {c4[0]:.1f} {c4[1]:.1f} {p0[0]:.1f} {p0[1]:.1f}Z"/>')

OUT = {}

# ---------------------------------------------------------------- 1 · Ajans
def opt1(variant):
    word = Text('Filistin Ajansı', 800, 100, track=-1)
    S = 132                                         # monogram square
    mono = Text('FA', 900, 92, track=-6)
    mx = (S - mono.w) / 2; my = S / 2 + mono.cap / 2
    gap = 26
    wy = S / 2 + word.cap / 2
    if variant == 'renk':
        sq, mf, wf = RED, WHITE, INK
    else:                                           # white on red
        sq, mf, wf = WHITE, RED, WHITE
    body = (f'<rect width="{S}" height="{S}" fill="{sq}"/>'
            f'<path fill="{mf}" d="{mono.d}" transform="translate({mx:.1f} {my:.1f})"/>'
            f'<path fill="{wf}" d="{word.d}" transform="translate({S + gap} {wy:.1f})"/>')
    return svg(f'0 0 {S + gap + word.w:.0f} {S}', body)

def opt1_avatar(bg=RED, fg=WHITE, size=512):
    mono = Text('FA', 900, size * 0.46, track=-size * 0.03)
    return svg(f'0 0 {size} {size}', f'<rect width="{size}" height="{size}" fill="{bg}"/><path fill="{fg}" d="{mono.d}" transform="translate({(size - mono.w) / 2:.1f} {size / 2 + mono.cap / 2:.1f})"/>')

# ---------------------------------------------------------------- 2 · Zeytin
def opt2(variant):
    a = Text('fılıstın', 800, 100, track=-1)        # dotless ı: the tittles become olive leaves
    b = Text('ajansı', 500, 100, track=-1)
    gap = 26
    ink, leafc, sec = (INK, GREEN, RED) if variant == 'renk' else (WHITE, WHITE, WHITE)
    body = f'<path fill="{ink}" d="{a.d}"/>'
    angles = [-58, -122, -58]
    k = 0
    for i, ch in enumerate('fılıstın'):
        if ch == 'ı':
            x0, y0, x1, y1 = a.boxes[i]
            cx = (x0 + x1) / 2; cy = -a.xh - 27
            body += leaf(cx, cy, 44, angles[k], leafc); k += 1
    body += f'<path fill="{sec}" d="{b.d}" transform="translate({a.w + gap:.1f} 0)"/>'
    top = -a.xh - 62
    asc = 76
    return svg(f'0 {top:.0f} {a.w + gap + b.w:.0f} {-top + 22:.0f}', body)

def opt2_avatar(size=512, bg=GREEN, fg=WHITE):
    """The logo's own detail at avatar size: a dotless ı whose tittle is an olive leaf."""
    t = Text('ı', 800, size * .62)
    x0, y0, x1, y1 = t.boxes[0]
    stem_w = x1 - x0
    tx = (size - (x1 - x0)) / 2 - x0
    base = size * .78
    cx = tx + (x0 + x1) / 2
    body = f'<rect width="{size}" height="{size}" fill="{bg}"/><path fill="{fg}" d="{t.d}" transform="translate({tx:.1f} {base:.1f})"/>'
    body += leaf(cx + size * .02, base - t.xh - size * .17, size * .3, -58, fg)
    return svg(f'0 0 {size} {size}', body)

# ---------------------------------------------------------------- 3 · Kubbe
def dome_path(x, y, w, h):
    """Kubbetü's-Sahra in one shape: the wide octagonal hall, the drum, the dome, the finial."""
    base_h = h * 0.40
    drum_h = h * 0.13
    dome_h = h * 0.39
    fin = h * 0.08
    bw, dw = w, w * 0.68
    dx = x + (w - dw) / 2
    y_base = y + h - base_h
    y_drum = y_base - drum_h
    y_top = y_drum - dome_h
    k = dw * 0.07
    d = (f'M{x:.1f} {y + h:.1f}V{y_base:.1f}H{dx:.1f}V{y_drum:.1f}'
         f'C{dx - k:.1f} {y_drum - dome_h * .58:.1f} {dx + dw * .2:.1f} {y_top:.1f} {dx + dw / 2:.1f} {y_top:.1f}'
         f'C{dx + dw * .8:.1f} {y_top:.1f} {dx + dw + k:.1f} {y_drum - dome_h * .58:.1f} {dx + dw:.1f} {y_drum:.1f}'
         f'V{y_base:.1f}H{x + w:.1f}V{y + h:.1f}Z')
    return d, (x + w / 2, y_top), y_base

def opt3(variant):
    word = Text('Filistin Ajansı', 800, 100, track=-1)
    W, H = 150, 150
    d, (fx, fy), yb = dome_path(0, 0, W, H)
    mono = Text('FA', 900, 50, track=-3)
    shell, mf, wf = (RED, WHITE, INK) if variant == 'renk' else (WHITE, RED, WHITE)
    by = yb + (H - yb) / 2 + mono.cap / 2
    body = (f'<path fill="{shell}" d="{d}"/>'
            f'<rect x="{fx - 3:.1f}" y="{fy - 13:.1f}" width="6" height="14" fill="{shell}"/>'
            f'<circle cx="{fx:.1f}" cy="{fy - 16:.1f}" r="5" fill="{shell}"/>'
            f'<path fill="{mf}" d="{mono.d}" transform="translate({(W - mono.w) / 2:.1f} {by:.1f})"/>'
            f'<path fill="{wf}" d="{word.d}" transform="translate({W + 26} {H - (H - yb) / 2 + word.cap / 2:.1f})"/>')
    return svg(f'0 {fy - 24:.0f} {W + 26 + word.w:.0f} {H - fy + 24 + 26:.0f}', body)

def opt3_avatar(size=512, bg=RED, fg=WHITE):
    W, H = size * .62, size * .56
    x = (size - W) / 2; y = (size - H) / 2 + size * .07
    d, (fx, fy), yb = dome_path(x, y, W, H)
    mono = Text('FA', 900, size * .17, track=-size * .01)
    return svg(f'0 0 {size} {size}', f'<rect width="{size}" height="{size}" fill="{bg}"/><path fill="{fg}" d="{d}"/>'
               f'<rect x="{fx - size * .011:.1f}" y="{fy - size * .05:.1f}" width="{size * .022:.1f}" height="{size * .052:.1f}" fill="{fg}"/>'
               f'<circle cx="{fx:.1f}" cy="{fy - size * .058:.1f}" r="{size * .018:.1f}" fill="{fg}"/>'
               f'<path fill="{bg}" d="{mono.d}" transform="translate({(size - mono.w) / 2:.1f} {yb + (y + H - yb) / 2 + mono.cap / 2:.1f})"/>')

# ---------------------------------------------------------------- 4 · Kufiye
def kufiye_badge(x, y, S, uid, light=False):
    """Black badge, the keffiyeh fishnet in white, the keffiyeh's band in red along the foot."""
    net = WHITE
    body = (f'<defs><clipPath id="k{uid}"><rect x="{x}" y="{y}" width="{S}" height="{S}"/></clipPath>'
            f'<pattern id="n{uid}" width="{S / 6:.2f}" height="{S / 6:.2f}" patternUnits="userSpaceOnUse" patternTransform="translate({x} {y}) rotate(45)">'
            f'<path d="M0 0H{S / 6:.2f}M0 0V{S / 6:.2f}" stroke="{net}" stroke-width="{S * .012:.2f}" opacity=".9"/>'
            f'<circle cx="{S / 12:.2f}" cy="{S / 12:.2f}" r="{S * .012:.2f}" fill="{net}"/></pattern></defs>'
            f'<rect x="{x}" y="{y}" width="{S}" height="{S}" fill="{BLACK}"/>'
            f'<rect x="{x}" y="{y}" width="{S}" height="{S * .72:.1f}" fill="url(#n{uid})" opacity=".55" clip-path="url(#k{uid})"/>'
            f'<rect x="{x}" y="{y + S * .76:.1f}" width="{S}" height="{S * .07:.1f}" fill="{RED}"/>'
            f'<rect x="{x}" y="{y + S * .87:.1f}" width="{S}" height="{S * .03:.1f}" fill="{RED}"/>')
    mono = Text('FA', 900, S * .5, track=-S * .03)
    plate_w = mono.w + S * .14
    body += f'<rect x="{x + (S - plate_w) / 2:.1f}" y="{y + S * .17:.1f}" width="{plate_w:.1f}" height="{S * .46:.1f}" fill="{BLACK}"/>'
    body += f'<path fill="{WHITE}" d="{mono.d}" transform="translate({x + (S - mono.w) / 2:.1f} {y + S * .40 + mono.cap / 2:.1f})"/>'
    return body

def opt4(variant):
    word = Text('FİLİSTİN AJANSI', 800, 76, track=10)
    S = 132
    wf = INK if variant == 'renk' else WHITE
    body = kufiye_badge(0, 0, S, variant) + f'<path fill="{wf}" d="{word.d}" transform="translate({S + 26} {S / 2 + word.cap / 2:.1f})"/>'
    return svg(f'0 0 {S + 26 + word.w:.0f} {S}', body)

def opt4_avatar(size=512):
    return svg(f'0 0 {size} {size}', kufiye_badge(0, 0, size, 'av'))

# ---------------------------------------------------------------- write
OPTIONS = {
    '1': ('Ajans', opt1, lambda: opt1_avatar()),
    '2': ('Zeytin', opt2, lambda: opt2_avatar()),
    '3': ('Kubbe', opt3, lambda: opt3_avatar()),
    '4': ('Kufiye', opt4, lambda: opt4_avatar()),
}
d = os.path.join(ROOT, 'assets', 'brand')
os.makedirs(d, exist_ok=True)
for k, (name, fn, av) in OPTIONS.items():
    files = {f'secenek-{k}.svg': fn('renk'), f'secenek-{k}-beyaz.svg': fn('beyaz'), f'secenek-{k}-avatar.svg': av()}
    for n, s in files.items():
        open(os.path.join(d, n), 'w', encoding='utf-8').write(s)
    OUT[k] = {'name': name, 'renk': files[f'secenek-{k}.svg'], 'beyaz': files[f'secenek-{k}-beyaz.svg'], 'avatar': files[f'secenek-{k}-avatar.svg']}
os.makedirs(os.path.join(ROOT, 'tools', 'out'), exist_ok=True)
json.dump(OUT, open(os.path.join(ROOT, 'tools', 'out', 'logos.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('logos:', ', '.join(f'{k} {v[0]}' for k, v in OPTIONS.items()))
