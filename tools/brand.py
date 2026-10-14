"""Draws the Filistin Ajansı marks from Alegreya Sans outlines.

python -I tools/brand.py   (from the project root)

The logo is a legend entry: a key box holding the nirengi (triangulation point) symbol,
and the name set like a region label on a map, spaced capitals on two lines.
The three İ dots of FİLİSTİN are kept as separate circles: they are the three known
points the loader triangulates from.
Writes assets/brand/*.svg and tools/out/logo.json (path data for inline use).
"""
import json, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = TTFont(os.path.join(ROOT, 'research', 'font-src', 'AlegreyaSans-ExtraBold.ttf'))
GS, CMAP, HMTX = FONT.getGlyphSet(), FONT.getBestCmap(), FONT['hmtx']

INK, PAPER, MAG = '#121417', '#FBFCFC', '#A3127F'
INK_NIGHT, PAPER_NIGHT, MAG_NIGHT = '#E9EDEF', '#0F1214', '#EE63C8'

TRACK = 150          # letter spacing in font units (0.15 em): a region label, not a headline
CAP = 645
LEAD = 1000          # baseline to baseline of the two lines

def glyph_path(name, dx, dy, flip=True):
    pen = SVGPathPen(GS)
    t = TransformPen(pen, (1, 0, 0, -1 if flip else 1, dx, dy))
    GS[name].draw(t)
    return pen.getCommands()

def glyph_bounds(name):
    bp = BoundsPen(GS); GS[name].draw(bp); return bp.bounds

def set_line(text, y):
    """Returns (paths, dots, width). İ is drawn as I plus a separate round dot."""
    x, paths, dots = 0, [], []
    for i, ch in enumerate(text):
        name = CMAP[ord(ch)]
        adv = HMTX[name][0]
        if ch == 'İ':
            paths.append(glyph_path('I', x, y))
            g = FONT['glyf'][name]
            comp = [c for c in g.components if c.glyphName != 'I'][0]
            b = glyph_bounds(comp.glyphName)
            cx = x + comp.x + (b[0] + b[2]) / 2
            cy = y - (comp.y + (b[1] + b[3]) / 2)
            r = (b[2] - b[0]) / 2
            dots.append((round(cx, 1), round(cy, 1), round(r, 1)))
        else:
            paths.append(glyph_path(name, x, y))
        x += adv + (TRACK if i < len(text) - 1 else 0)
    return ''.join(paths), dots, x

def lsb(ch):
    return glyph_bounds(CMAP[ord(ch)])[0]

# --- wordmark: FİLİSTİN over AJANSI, left edges optically aligned on the stems ---
l1, dots, w1 = set_line('FİLİSTİN', CAP)
l2, _, w2 = set_line('AJANSI', CAP + LEAD)
shift2 = lsb('F') - lsb('A') + 18      # the A's foot sits a hair right of the F stem: optical, not mathematical
l2, _, w2 = set_line('AJANSI', CAP + LEAD)
WORD_H = CAP + LEAD                    # cap top of line 1 to baseline of line 2
WORD_W = max(w1, w2 + shift2)

# --- mark: legend key box with the nirengi point ---
BOX = WORD_H                           # the key box is exactly as tall as the two lines of capitals
STROKE_BOX = 74
STROKE_TRI = 104
DOT = 0.046              # a survey point, not a pupil: the dot stays small so the symbol never reads as an eye
def mark_parts(size=BOX, ox=0, oy=0):
    s = size / BOX
    half = STROKE_BOX * s / 2
    box = (ox + half, oy + half, size - 2 * half)
    # equilateral triangle, side 0.62 of the box, sitting on a baseline at 0.79 of the box
    side = 0.62 * size
    h = side * 3 ** 0.5 / 2
    base_y = oy + 0.785 * size
    cx = ox + size / 2
    tri = [(cx - side / 2, base_y), (cx + side / 2, base_y), (cx, base_y - h)]
    centroid = (cx, base_y - h / 3)
    return box, tri, centroid, STROKE_TRI * s, DOT * size

GAP = round(BOX * 0.30)

def mark_svg(box, tri, cen, tw, dot_r, ink, mag, bg=None, box_stroke=STROKE_BOX, show_box=True):
    bx, by, bs = box
    out = []
    if bg:
        out.append(f'<rect x="{bx - box_stroke/2:.1f}" y="{by - box_stroke/2:.1f}" width="{bs + box_stroke:.1f}" height="{bs + box_stroke:.1f}" fill="{bg}"/>')
    if show_box:
        out.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bs:.1f}" height="{bs:.1f}" fill="none" stroke="{ink}" stroke-width="{box_stroke:.1f}"/>')
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in tri)
    out.append(f'<polygon points="{pts}" fill="none" stroke="{ink}" stroke-width="{tw:.1f}" stroke-linejoin="miter"/>')
    out.append(f'<circle cx="{cen[0]:.1f}" cy="{cen[1]:.1f}" r="{dot_r:.1f}" fill="{mag}"/>')
    return ''.join(out)

def lockup(ink, mag, dotc, title='Filistin Ajansı', bg=None, pad=0):
    box, tri, cen, tw, dr = mark_parts()
    wx = BOX + GAP
    W, H = wx + WORD_W, BOX
    body = mark_svg(box, tri, cen, tw, dr, ink, mag)
    body += f'<g fill="{ink}"><path d="{l1}" transform="translate({wx} 0)"/><path d="{l2}" transform="translate({wx + shift2} 0)"/></g>'
    body += ''.join(f'<circle cx="{wx + x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{dotc}"/>' for x, y, r in dots)
    top = min(y - r for _, y, r in dots)          # the İ dots rise above the cap line
    vb_y = min(0, top) - pad
    vb = f'{-pad} {vb_y:.0f} {W + 2 * pad:.0f} {H - vb_y + pad:.0f}'
    bgr = f'<rect x="{-pad}" y="{vb_y:.0f}" width="{W + 2*pad:.0f}" height="{H - vb_y + pad:.0f}" fill="{bg}"/>' if bg else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="{title}"><title>{title}</title>{bgr}{body}</svg>'

def one_line(ink, mag, dotc, title='Filistin Ajansı'):
    lt, dts, wt = set_line('FİLİSTİN AJANSI', CAP)
    size = CAP + 260
    box, tri, cen, tw, dr = mark_parts(size, 0, CAP - size + 130)
    wx = size + round(size * 0.32)
    top = min(y - r for _, y, r in dts)
    vb_y = min(box[1] - STROKE_BOX, top)
    body = mark_svg(box, tri, cen, tw, dr, ink, mag, box_stroke=STROKE_BOX * size / BOX)
    body += f'<path fill="{ink}" d="{lt}" transform="translate({wx} 0)"/>'
    body += ''.join(f'<circle cx="{wx + x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{dotc}"/>' for x, y, r in dts)
    h = (CAP + 130) - vb_y + STROKE_BOX / 2
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {vb_y:.0f} {wx + wt:.0f} {h:.0f}" role="img" aria-label="{title}"><title>{title}</title>{body}</svg>'

def mark_only(ink, mag, bg=None, size=512, inset=0.16, box=False, title='Filistin Ajansı', dot_k=1.0, tri_k=1.08):
    s = size * (1 - 2 * inset)
    o = size * inset
    bx, tri, cen, tw, dr = mark_parts(s, o, o)
    body = (f'<rect width="{size}" height="{size}" fill="{bg}"/>' if bg else '') + mark_svg(bx, tri, cen, tw * tri_k, dr * dot_k, ink, mag, box_stroke=STROKE_BOX * s / BOX, show_box=box)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" role="img" aria-label="{title}"><title>{title}</title>{body}</svg>'

out_dir = os.path.join(ROOT, 'assets', 'brand')
os.makedirs(out_dir, exist_ok=True)
files = {
    'logo.svg': lockup(INK, MAG, MAG),
    'logo-gece.svg': lockup(INK_NIGHT, MAG_NIGHT, MAG_NIGHT),
    'logo-mono-siyah.svg': lockup(INK, INK, INK),
    'logo-mono-beyaz.svg': lockup('#FFFFFF', '#FFFFFF', '#FFFFFF'),
    'logo-tek-satir.svg': one_line(INK, MAG, MAG),
    'logo-tek-satir-gece.svg': one_line(INK_NIGHT, MAG_NIGHT, MAG_NIGHT),
    'isaret.svg': mark_only(INK, MAG, box=True, inset=0.06),
    'isaret-avatar.svg': mark_only('#FFFFFF', '#FFFFFF', bg=MAG, inset=0.2),
    'isaret-avatar-gece.svg': mark_only(MAG_NIGHT, '#FFFFFF', bg='#0F1214', inset=0.2),
    'favicon.svg': mark_only('#FFFFFF', '#FFFFFF', bg=MAG, size=64, inset=0.08, dot_k=1.7, tri_k=1.45),
}
for n, svg in files.items():
    open(os.path.join(out_dir, n), 'w', encoding='utf-8').write(svg)

box, tri, cen, tw, dr = mark_parts()
json.dump({
    'box': BOX, 'gap': GAP, 'wordW': WORD_W, 'cap': CAP, 'lead': LEAD, 'shift2': shift2,
    'l1': l1, 'l2': l2, 'dots': dots, 'mark': {'box': box, 'tri': tri, 'centroid': cen, 'tw': tw, 'dot': dr, 'boxStroke': STROKE_BOX},
}, open(os.path.join(ROOT, 'tools', 'out', 'logo.json'), 'w', encoding='utf-8'))
print('wrote', len(files), 'files; word', WORD_W, 'x', WORD_H, 'dots', dots)
