"""Builds the Filistin Ajansı pages from the templates and the frozen edition.

python -I tools/build.py   (from the project root; run tools/geo.py and tools/brand.py first)

tools/tpl/*.html  -> *.html in the project root. Never hand-edit the generated pages:
edit the template, the parts in tools/parts/, or the data in research/, then rebuild.
"""
import json, os, re, html, math
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *p: os.path.join(ROOT, *p)
V = '16'   # asset version: bump on every CSS/JS change (Chrome caches hard)

geo = json.load(open(P('tools', 'out', 'geo.json'), encoding='utf-8'))
logo = json.load(open(P('tools', 'out', 'logo.json'), encoding='utf-8'))
NEWS = json.load(open(P('research', 'news.json'), encoding='utf-8'))
ITEMS = NEWS['items']
PHOTOS = json.load(open(P('research', 'photos.json'), encoding='utf-8')) if os.path.exists(P('research', 'photos.json')) else []
if isinstance(PHOTOS, dict):
    PHOTOS = PHOTOS.get('photos') or PHOTOS.get('items') or []
LOCAL = json.load(open(P('tools', 'out', 'photos-local.json'), encoding='utf-8')) if os.path.exists(P('tools', 'out', 'photos-local.json')) else {}

TODAY = NEWS['edition']['date']
EDITION_TIME = NEWS['edition']['time']
BY_ID = {i['id']: i for i in ITEMS}

# ---------- editorial choices for this edition ----------
MANSET = 'f17'   # Turmus Ayya: its archive photo shows the same hills and olive groves
CANLI = 'f02'

AY = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
GUN = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']

def e(s):
    return html.escape(str(s), quote=True)

def tr_text(s):
    """Typographic Turkish: suffix apostrophes become ’, straight quotes become “ ”."""
    s = re.sub(r"(?<=\w)'(?=\w)", '’', s)
    s = re.sub(r'"([^"]+)"', r'“\1”', s)
    s = re.sub(r"'([^']+)'", r'‘\1’', s)
    return s

def T(s):
    return e(tr_text(s))

def date_tr(d, weekday=False, year=True):
    y, m, dd = map(int, d.split('-'))
    import datetime
    w = GUN[datetime.date(y, m, dd).weekday()]
    out = f'{dd} {AY[m - 1]}' + (f' {y}' if year else '')
    return out + (f' {w}' if weekday else '')

def saat(t):
    return t.replace(':', '.') if t else '—'

def zaman(it):
    """Time for today's records; day and time for earlier ones, so grey is never the only cue."""
    if it['date'] == TODAY:
        return saat(it['time'])
    d = date_tr(it['date'], year=False)
    return f'{d}, {saat(it["time"])}' if it['time'] else d

def num_tr(v):
    return str(v)

CAT = {
    'baskın': ('baskin', 'Baskın'), 'gözaltı': ('gozalti', 'Gözaltı'), 'yerleşimci': ('yerlesimci', 'Yerleşimci saldırısı'),
    'yıkım': ('yikim', 'Yıkım'), 'kapı-kontrol-noktası': ('kapi', 'Kapı ve kontrol noktası'), 'zeytin-hasadı': ('zeytin', 'Zeytin hasadı'),
    'esir': ('esir', 'Esirler'), 'şehit-yaralı': ('kayip', 'Can kaybı ve yaralı'), 'gazze-ateşkes': ('saldiri', 'Ateşkes ihlali'),
    'insani-durum': ('insani', 'İnsani durum'), 'aksa-kudüs': ('aksa', 'Mescid-i Aksa'), 'siyaset': ('siyaset', 'Siyaset ve diplomasi'),
    'ekonomi': ('diger', 'Diğer'), 'kültür': ('diger', 'Diğer'),
}
def sym_of(it):
    s = CAT[it['category']][0]
    if it['category'] == 'şehit-yaralı' and re.search(r'yaral', it['headline_tr']) and not re.search(r'hayatını kaybet|ölü|öldü|toprağa', it['headline_tr']):
        s = 'yarali'
    return s

def isr(sym, cls=''):
    return f'<svg class="isr {cls}" aria-hidden="true" focusable="false"><use href="#i-{sym}"/></svg>'

def ui(sym, cls=''):
    return f'<svg class="isr {cls}" aria-hidden="true" focusable="false"><use href="#u-{sym}"/></svg>'

def first(text):
    """The first sentence: split on a full stop followed by a capital, so 8.895 or 13.30 stay whole."""
    return re.split(r'(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ“"‘])', text.strip(), maxsplit=1)[0]

def place_label(it, short=False):
    g, p = it.get('governorate_tr'), it.get('place_tr')
    if it['region'] == 'dünya':
        return p or 'Dünya'
    if not g:
        return p or {'esirler': 'Esirler', 'gazze': 'Gazze Şeridi', 'kudüs': 'Kudüs'}.get(it['region'], 'Batı Şeria')
    g_short = {'Ramallah ve El Bire': 'Ramallah'}.get(g, g) if short else g
    if p and p not in (g, g_short) and p != 'Ramallah':
        return f'{g_short} · {p}'
    return g_short

def src_link(it, text=None):
    return f'<a href="{e(it["source_url"])}" target="_blank" rel="noopener">{e(text or it["source_name"])}</a>'

def is_today(it):
    return it['date'] == TODAY

def sort_key(it):
    return (it['date'], it['time'] or '00:00')

def by_time(items):
    return sorted(items, key=sort_key, reverse=True)

TODAY_ITEMS = by_time([i for i in ITEMS if is_today(i)])
GOV = {g['id']: g for g in geo['govs']}
GOV_NAME_TO_ID = {g['name']: g['id'] for g in geo['govs']}

# ---------- logo inline ----------
def logo_svg(cls='', title='Filistin Ajansı'):
    m = logo['mark']
    bx, by, bs = m['box']
    tri = ' '.join(f'{x:.1f},{y:.1f}' for x, y in m['tri'])
    wx = logo['box'] + logo['gap']
    top = min(y - r for _, y, r in logo['dots'])
    W = wx + logo['wordW']
    H = logo['box'] - top
    dots = ''.join(f'<circle class="l-dot" cx="{wx + x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>' for x, y, r in logo['dots'])
    return (f'<svg class="{cls}" viewBox="0 {top:.0f} {W:.0f} {H:.0f}" role="img" aria-label="{title}">'
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bs:.1f}" height="{bs:.1f}" fill="none" stroke="currentColor" stroke-width="{m["boxStroke"]}"/>'
            f'<polygon points="{tri}" fill="none" stroke="currentColor" stroke-width="{m["tw"]:.1f}"/>'
            f'<circle class="l-dot l-nokta" cx="{m["centroid"][0]:.1f}" cy="{m["centroid"][1]:.1f}" r="{m["dot"]:.1f}"/>'
            f'<g fill="currentColor"><path d="{logo["l1"]}" transform="translate({wx} 0)"/><path d="{logo["l2"]}" transform="translate({wx + logo["shift2"]} 0)"/></g>'
            f'{dots}</svg>')

# ---------- shared parts ----------
def part(name):
    return open(P('tools', 'parts', name), encoding='utf-8').read()

MENU = [('#bati-seria', 'Batı Şeria', 'baskin'), ('#gazze', 'Gazze', 'saldiri'), ('#kudus', 'Kudüs', 'aksa'),
        ('#esirler', 'Esirler', 'esir'), ('#toprak', 'Toprak', 'zeytin'), ('#rakamlar', 'Rakamlar', 'nirengi'), ('#foto', 'Foto', 'diger')]

def ust(current='home'):
    links = ''.join(f'<a href="{h}">{isr(s)}{e(t)}</a>' for h, t, s in MENU)
    return f'''<header class="ust">
  <div class="ust__ic">
    <a class="logo" href="home.html" aria-label="Filistin Ajansı ana sayfa">{logo_svg('logo-svg', 'Filistin Ajansı')}</a>
    <nav class="menu" aria-label="Bölümler">{links}</nav>
    <div class="araclar">
      <button class="ikon-dugme" type="button" data-tema aria-label="Gece paftasına geç">{ui('gece', 'tema-gece')}{ui('gunduz', 'tema-gunduz')}</button>
      <a class="ikon-dugme" href="#ara" aria-label="Arşivde ara">{ui('ara')}</a>
      <a class="dugme" href="#bulten">Bülten</a>
      <button class="ikon-dugme menu-ac" type="button" data-menu aria-label="Menüyü aç" aria-expanded="false" aria-controls="cekmece">{ui('menu')}</button>
    </div>
  </div>
</header>'''

def cekmece():
    links = ''.join(f'<a href="{h}" data-kapat>{isr(s)}{e(t)}</a>' for h, t, s in MENU)
    return f'''<div class="cekmece" id="cekmece" role="dialog" aria-modal="true" aria-label="Menü" hidden>
  <div class="cekmece__ust"><a class="logo" href="home.html" aria-label="Filistin Ajansı ana sayfa">{logo_svg('logo-svg')}</a>
  <button class="ikon-dugme" type="button" data-kapat aria-label="Menüyü kapat">{ui('kapat')}</button></div>
  <nav aria-label="Bölümler">{links}<a href="index.html" data-kapat>{isr('nirengi')}Kimlik kılavuzu</a></nav>
</div>'''

def yaka():
    """Top collar: today's time axis. Each tick is one report, placed at the minute it came in."""
    def pos(t):
        h, m = map(int, t.split(':'))
        return (h * 60 + m) / (24 * 60) * 100
    hours = ''.join(f'<span class="yaka__saat" style="left:{h / 24 * 100:.3f}%">{h:02d}</span>' for h in range(0, 25, 3))
    ticks = ''.join(f'<i style="left:{pos(i["time"]):.3f}%" title="{saat(i["time"])} · {T(place_label(i, True))}"></i>' for i in TODAY_ITEMS if i['time'])
    eh, em = map(int, EDITION_TIME.split('.'))
    now = (eh * 60 + em) / (24 * 60) * 100
    return f'''<div class="yaka">
  <span><b>{date_tr(TODAY, weekday=True)}</b> · Baskı {EDITION_TIME}</span>
  <span class="yaka__cetvel" aria-hidden="true">{hours}<span class="yaka__kayit">{ticks}</span><span class="yaka__simdi" style="left:{now:.3f}%"></span></span>
  <span>Kudüs ve İstanbul UTC+3</span>
</div>'''

def canli():
    it = BY_ID[CANLI]
    return f'''<div class="canli" role="region" aria-label="Son dakika">
  <span class="canli__etiket"><span class="canli-halka">{isr(sym_of(it), 'bugun')}</span><span class="yer">Son dakika</span></span>
  <span class="zaman">{saat(it["time"])}</span>
  <span class="canli__metin"><span class="yer yer--ink">{T(place_label(it, True))}</span> <a href="#k-{it["id"]}">{T(it["headline_tr"])}</a></span>
</div>'''

def alt():
    legend = [('baskin', 'Baskın'), ('gozalti', 'Gözaltı'), ('yerlesimci', 'Yerleşimci saldırısı'), ('yikim', 'Yıkım'),
              ('kapi', 'Kapalı kapı'), ('kapi-acik', 'Açık kapı'), ('kontrol', 'Kontrol noktası'), ('set', 'Toprak set'),
              ('zeytin', 'Zeytin hasadı'), ('kayip', 'Can kaybı'), ('yarali', 'Yaralı'), ('saldiri', 'Saldırı, ateşkes ihlali'),
              ('insani', 'İnsani durum'), ('aksa', 'Mescid-i Aksa'), ('esir', 'Esir'), ('siyaset', 'Siyaset')]
    lg = ''.join(f'<li>{isr(s)}{e(t)}</li>' for s, t in legend)
    return f'''<footer class="kunye" id="kunye">
  <div class="kunye__ust">
    <div>
      <a class="kunye__logo logo" href="home.html" aria-label="Filistin Ajansı ana sayfa">{logo_svg('logo-svg')}</a>
      <p class="kunye__not">Filistin’in ve Batı Şeria’nın haberleri, Türkçe. Her haber yeriyle, saatiyle ve kaynağıyla.</p>
      <p class="kunye__not" style="margin-top:12px"><a href="index.html">Kimlik kılavuzu</a> · <a href="#bulten">Bülten</a></p>
    </div>
    <div>
      <h3>Lejant</h3>
      <ul class="lejant-tablo">{lg}</ul>
    </div>
    <div>
      <h3>Pafta bilgisi</h3>
      <ul>
        <li>Baskı: {date_tr(TODAY)}, {EDITION_TIME}</li>
        <li>Mor baskı: bugünün kayıtları</li>
        <li>Gri: önceki iki gün</li>
        <li>Kesik çizgi: gelişen haber</li>
        <li>Halka: canlı</li>
      </ul>
    </div>
    <div>
      <h3>Kaynaklar</h3>
      <ul>
        <li>WAFA, Anadolu Ajansı, BM OCHA</li>
        <li>Duvar ve Yerleşim Karşıtı Komisyon</li>
        <li>Filistinli Esirler Kulübü, Esir İşleri Kurumu</li>
        <li>Harita: geoBoundaries (CC BY 4.0), OpenStreetMap (ODbL), Natural Earth</li>
      </ul>
    </div>
  </div>
  <div class="kunye__alt">
    <span>© 2026 Filistin Ajansı. Sosyal medya hesapları ve künye yakında.</span>
    <span>Fotoğraflar arşivdir; her karede kaynak ve lisans yazılıdır.</span>
  </div>
</footer>'''

# ---------- the pafta ----------
W, H = geo['sheet']['w'], geo['sheet']['h']
KX, KY, U = geo['proj']['kx'], geo['proj']['ky'], geo['proj']['u']
WB_LON0, WB_LAT0, GSHIFT = geo['proj']['wb']
GZ_LON0, GZ_LAT0, GZX, GZY = geo['proj']['gz']

def wb_xy(lon, lat):
    return ((lon - WB_LON0) * KX + GSHIFT) * U, (WB_LAT0 - lat) * KY * U

def gz_xy(lon, lat):
    return ((lon - GZ_LON0) * KX + GZX) * U, ((GZ_LAT0 - lat) * KY + GZY) * U

def item_xy(it):
    if it.get('lat') is None or not it.get('governorate_tr'):
        return None
    if it['region'] == 'gazze':
        return gz_xy(it['lon'], it['lat'])
    if it['region'] in ('batı-şeria', 'kudüs', 'esirler'):
        return wb_xy(it['lon'], it['lat'])
    return None

LABEL = {  # dx, dy, anchor: hand-placed so labels clear the symbols and the barrier
    'Cenin': (16, 10, 'start'), 'Tubas': (16, 10, 'start'), 'Tulkerem': (-16, 10, 'end'), 'Nablus': (16, 12, 'start'),
    'Kalkilya': (-16, 10, 'end'), 'Selfit': (-16, 12, 'end'), 'Ramallah': (-16, 12, 'end'), 'Eriha': (-16, 10, 'end'),
    'Kudüs': (-18, 12, 'end'), 'Beytüllahim': (-16, 14, 'end'), 'El Halil': (-16, 10, 'end'),
    'Gazze': (16, 10, 'start'), 'Han Yunus': (16, 10, 'start'), 'Refah': (16, 12, 'start'), 'Deyr el-Belah': (20, 6, 'start'), 'Cebaliye': (16, 4, 'start'),
}

def place_labels(plist, marks, size, FS=33):
    """Each town label tries eight positions around its dot and takes the one that covers the
    fewest report symbols and earlier labels: symbols are the news, labels must step aside."""
    taken = []                                   # label boxes already placed
    out = []
    def box(x, y, w, anchor):
        x0 = x if anchor == 'start' else (x - w / 2 if anchor == 'middle' else x - w)
        return (x0 - 3, y - FS * 0.78, x0 + w + 3, y + FS * 0.22)
    def hit(b):
        score = 0
        for mx, my in marks:
            r = size * 0.72 + 9                  # the paper halo plus a hair
            cx = min(max(mx, b[0]), b[2]); cy = min(max(my, b[1]), b[3])
            d2 = (cx - mx) ** 2 + (cy - my) ** 2
            if d2 < r * r:
                score += 10 + (r - d2 ** .5)          # deeper overlaps cost more, so a near miss beats a direct hit
        for t in taken:
            if not (b[2] < t[0] or b[0] > t[2] or b[3] < t[1] or b[1] > t[3]):
                score += 25
        return score
    fx, fy, fw, fh = geo['gzFrame']
    gaza_names = {q['name'] for q in geo['gazaPlaces']}
    def outside(b, name):
        if name in gaza_names:
            return b[0] < fx + 4 or b[2] > fx + fw - 4 or b[1] < fy + 4 or b[3] > fy + fh - 60
        return b[0] < fx + fw + 6 and b[3] > fy - 40     # West Bank labels keep off the inset
    TWO_LINE = {'Deyr el-Belah': ('Deyr', 'el-Belah')}     # long names in the narrow Gaza inset may break, as on printed sheets
    for p in sorted(plist, key=lambda q: -q['size']):
        gz = p['name'] in gaza_names
        fsz = FS * (0.82 if gz else 1)
        lines = TWO_LINE.get(p['name'], (p['name'],)) if gz else (p['name'],)
        longest = max(len(t) for t in lines)
        w = longest * fsz * (0.58 if p['size'] == 3 else 0.54) + (FS * .4 if p['name'] == 'Kudüs' else 0)
        extra_h = (len(lines) - 1) * fsz * 1.05
        r = 7 if p['size'] == 3 else 5
        x, y = p['x'], p['y']
        pref = LABEL.get(p['name'], (14, 10, 'start'))
        k = FS / 31 * (1.35 if FS < 20 else 1)
        cands = [(pref[0] * k, pref[1] * k, pref[2])] + [(a * k, b * k, c) for a, b, c in [(16, 10, 'start'), (-16, 10, 'end'), (12, -14, 'start'), (12, 34, 'start'), (-12, -14, 'end'), (-12, 34, 'end'),
                                                                     (0, -20, 'middle'), (0, 44, 'middle'), (36, 10, 'start'), (-36, 10, 'end'), (30, -22, 'start'), (-30, 42, 'end'),
                                                                     (48, 10, 'start'), (-48, 10, 'end'), (-30, 58, 'end'), (30, 58, 'start'), (0, 64, 'middle'), (0, -40, 'middle'),
                                                                     (44, -8, 'start'), (-44, -8, 'end')]]
        def bx(c):
            b0 = box(x + c[0], y + c[1], w, c[2])
            return (b0[0], b0[1], b0[2], b0[3] + extra_h)
        best = min(cands, key=lambda c: (hit(bx(c)) + (120 if outside(bx(c), p['name']) else 0), cands.index(c)))
        taken.append(bx(best))
        kudus = ' yer-kudus' if p['name'] == 'Kudüs' else (' yer-gz' if gz else '')
        tx, ty = x + best[0], y + best[1]
        if len(lines) == 1:
            label = e(p['name'])
        else:
            label = ''.join(f'<tspan x="{tx:.0f}" dy="{0 if i == 0 else fsz * 1.05:.0f}">{e(t)}</tspan>' for i, t in enumerate(lines))
        out.append(f'<g class="yerlesim{kudus}"><circle cx="{x}" cy="{y}" r="{r}"/>'
                   f'<text x="{tx:.0f}" y="{ty:.0f}" text-anchor="{best[2]}">{label}</text></g>')
    return ''.join(out)

def spread(points, r0=40):
    """Greedy placement: a symbol keeps its true place unless another already sits there,
    then it moves to the nearest free slot on a ring and keeps a leader to the true point."""
    placed = []
    out = []
    for key, (x, y) in points:
        cands = [(x, y)]
        for ring, n in ((1, 6), (2, 12), (3, 18)):
            for k in range(n):
                a = -math.pi / 2 + 2 * math.pi * k / n
                cands.append((x + math.cos(a) * r0 * ring, y + math.sin(a) * r0 * ring))
        for cx, cy in cands:
            if all(math.hypot(cx - px, cy - py) >= r0 * 0.92 for px, py in placed):
                placed.append((cx, cy)); out.append((key, (x, y), (cx, cy))); break
    return out

def pafta(items, cls='pafta', title_id='pafta-baslik', gaza=True, size=40, interactive=True, wb=True, fs=33):
    fx, fy, fw, fh = geo['gzFrame']
    pts = []
    for it in by_time(items):
        xy = item_xy(it)
        if xy and (gaza or it['region'] != 'gazze'):
            pts.append((it['id'], xy))
    placed = spread(pts, r0=size * 1.02)
    marks = []
    for key, (tx, ty), (x, y) in reversed(placed):
        it = BY_ID[key]
        tone = 'bugun' if is_today(it) else 'dun'
        lead = f'<path class="nokta__bag" d="M{tx:.1f} {ty:.1f}L{x:.1f} {y:.1f}"/><circle class="nokta__yer" cx="{tx:.1f}" cy="{ty:.1f}" r="4"/>' if (tx, ty) != (x, y) else ''
        s = sym_of(it)
        label = f'{zaman(it)} · {tr_text(place_label(it, True))} · {tr_text(it["headline_tr"])}'
        inner = (f'{lead}<g class="nokta__isr" transform="translate({x:.1f} {y:.1f})">'
                 f'<circle class="nokta__alan" r="{size * 0.72:.0f}"/>'
                 f'<use href="#i-{s}" x="{-size / 2:.0f}" y="{-size / 2:.0f}" width="{size}" height="{size}"/></g>')
        if interactive:
            if is_today(it) and key != MANSET:
                href = f'#k-{key}'
            elif key == MANSET:
                href = '#manset-baslik'
            elif it['region'] == 'gazze':
                href = '#gazze'
            else:
                href = f'#il-{GOV_NAME_TO_ID.get(it.get("governorate_tr"), "")}'
            marks.append(f'<a class="nokta {tone}" href="{href}" data-id="{key}" data-cat="{s}" aria-label="{e(label)}">{inner}</a>')
        else:
            marks.append(f'<g class="nokta {tone}" data-id="{key}" data-cat="{s}">{inner}</g>')
    places = place_labels((geo['places'] if wb else []) + (geo['gazaPlaces'] if gaza else []), [xy for _, _, xy in placed], size, fs)
    govs_wb = ''.join(f'<path class="il" data-il="{g["id"]}" d="{g["d"]}"/>' for g in geo['govs'] if not g['gaza'])
    govs_gz = ''.join(f'<path class="il" data-il="{g["id"]}" d="{g["d"]}"/>' for g in geo['govs'] if g['gaza'])
    gaza_block = f'''<g class="ek">
      {f'<rect class="ek__cerceve" x="{fx}" y="{fy}" width="{fw}" height="{fh}"/>' if wb else ''}
      <path class="deniz" d="{geo["gzSea"]}" fill="url(#{cls}-su)"/>
      <path class="dis" d="{geo["gzLand"]}" fill="url(#{cls}-ekran)"/>
      <path class="toprak" d="{geo["gz"]}"/>
      {govs_gz}
      <path class="sinir" d="{geo["gz"]}"/>
      <text class="doga-etiket" x="{fx + 26}" y="{fy + fh * 0.36}" transform="rotate(-62 {fx + 26} {fy + fh * 0.36})">Akdeniz</text>
      {f'''<text class="ek__ad" x="{fx + 16}" y="{fy - 16}">GAZZE ŞERİDİ</text>
      <text class="ek__not" x="{fx + fw - 14}" y="{fy + fh - 16}" text-anchor="end">aynı ölçek</text>
      <text class="ek__not" x="{fx + fw - 14}" y="{fy + fh - 44}" text-anchor="end">yeri kaydırıldı</text>''' if wb else ''}
    </g>''' if gaza else ''
    # scale bar: 0–5–10–20 km in sheet units (1 km = 10 units)
    sx, sy = 24, (fy - 150) if gaza else H - 60
    sb = ''.join(f'<rect x="{sx + a * 10}" y="{sy}" width="{(b - a) * 10}" height="9" class="{"siyah" if k % 2 == 0 else "beyaz"}"/>' for k, (a, b) in enumerate([(0, 5), (5, 10), (10, 20)]))
    sb += ''.join(f'<text x="{sx + v * 10}" y="{sy + 34}" text-anchor="middle">{v}</text>' for v in (0, 5, 10, 20)) + f'<text x="{sx + 200 + 14}" y="{sy + 34}">km</text>'
    north = f'<g class="kuzey" transform="translate({sx + 300} {sy - 34})"><path d="M0 -40L16 14L0 4L-16 14Z" class="kuzey__acik"/><path d="M0 -40L0 4L-16 14Z" class="kuzey__dolu"/><text y="44" text-anchor="middle">K</text></g>'
    wb_layers = f'''<rect class="dis" x="{GSHIFT * U:.0f}" y="0" width="{W - GSHIFT * U:.0f}" height="{H}" fill="url(#{cls}-ekran)"/>
    <path class="deniz" d="{geo["deadSea"]}" fill="url(#{cls}-su)"/>
    <path class="toprak" d="{geo["wb"]}"/>
    {govs_wb}
    <path class="nehir" d="{geo["riverEdge"]}"/>
    <path class="yesil-hat" d="{geo["green"]}"/>
    <path class="duvar" id="{cls}-duvar" d="{geo["barrier"]}"/><use class="duvar duvar--dis" href="#{cls}-duvar"/>
    <path class="duvar duvar--plan" d="{geo["barrierPlanned"]}"/>
    <text class="doga-etiket" x="{W - 120}" y="{H * 0.43}" transform="rotate(-88 {W - 120} {H * 0.43})">Ürdün Vadisi</text>
    <text class="doga-etiket" x="{W - 60}" y="{H * 0.8}" transform="rotate(-84 {W - 60} {H * 0.8})">Ölü Deniz</text>''' if wb else ''
    n_today = sum(1 for k, _, _ in placed if is_today(BY_ID[k]))
    desc = f'Batı Şeria ve Gazze Şeridi haritası. Bugünün {n_today} kaydı mor, önceki iki günün kayıtları gri işaretli.'
    return f'''<svg class="{cls}__svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="{title_id}" aria-describedby="{title_id}-d">
    <desc id="{title_id}-d">{e(desc)}</desc>
    <defs>
      <pattern id="{cls}-ekran" width="11" height="11" patternUnits="userSpaceOnUse"><circle cx="5.5" cy="5.5" r="1.25" class="ekran"/></pattern>
      <pattern id="{cls}-su" width="12" height="8" patternUnits="userSpaceOnUse"><path d="M0 4H12" class="su-cizgi"/></pattern>
    </defs>
    {wb_layers}
    {gaza_block}

    <g class="yerlesimler">{places}</g>
    <g class="noktalar">{"".join(marks)}</g>
  </svg>'''

def pafta_block():
    window = by_time([i for i in ITEMS])
    return f'''<div class="pafta" id="pafta">
    <div class="pafta__ust">
      <h2 class="pafta__ad" id="pafta-baslik"><span class="yer yer--ink">Batı Şeria</span><span class="pafta__alt">ve Gazze Şeridi</span></h2>
      <p class="pafta__not num">Son üç gün</p>
    </div>
    {pafta(window)}
    <div class="pafta__alt-bilgi">
      <div class="olcek" style="--olcek:{200 / W * 100:.3f}%" aria-label="Ölçek: 20 kilometre">
        <span class="olcek__cubuk"><i></i><i></i><i style="flex:2"></i></span>
        <span class="olcek__etiket num"><span>0</span><span>5</span><span>10</span><span>20 km</span></span>
      </div>
      <span class="pafta__kuzey" aria-label="Kuzey yukarıda">{ui('kuzey')}<b>K</b></span>
    </div>
    <ul class="lejant__cizgiler" aria-label="Haritadaki çizgiler ve tonlar">
      <li><i class="c-yesil"></i>Yeşil Hat (1949)</li>
      <li><i class="c-duvar"></i>Ayırma duvarı</li>
      <li><i class="c-plan"></i>Planlanan duvar</li>
      <li><i class="c-mor"></i>Bugün</li>
      <li><i class="c-gri"></i>12–13 Ekim</li>
    </ul>
  </div>'''

def serit():
    """The legend strip: one filter for the feed and the sheet, read like the key along a map's foot."""
    cats = Counter(sym_of(i) for i in TODAY_ITEMS)
    order = ['baskin', 'gozalti', 'yerlesimci', 'zeytin', 'yikim', 'kapi', 'kayip', 'yarali', 'saldiri', 'insani', 'aksa', 'esir', 'siyaset', 'diger']
    names = {'baskin': 'Baskın', 'gozalti': 'Gözaltı', 'yerlesimci': 'Yerleşimci saldırısı', 'zeytin': 'Zeytin hasadı', 'yikim': 'Yıkım',
             'kapi': 'Kapı, kontrol noktası', 'kayip': 'Can kaybı', 'yarali': 'Yaralı', 'saldiri': 'Ateşkes ihlali', 'insani': 'İnsani durum',
             'aksa': 'Mescid-i Aksa', 'esir': 'Esirler', 'siyaset': 'Siyaset', 'diger': 'Diğer'}
    btns = ''.join(f'<li><button type="button" class="lejant__oge" data-filtre="{s}" aria-pressed="false">{isr(s, "bugun")}<span>{names[s]}</span><b class="num">{cats[s]}</b></button></li>' for s in order if cats[s])
    return f'''<div class="lejant" role="group" aria-labelledby="lejant-ad">
    <p class="lejant__ad" id="lejant-ad"><span class="yer yer--ink">Lejant</span><span>Bugünün {len(TODAY_ITEMS)} kaydı, türe göre. Birini seçin: harita ve akış süzülür.</span></p>
    <ul>{btns}</ul>
  </div>'''

# ---------- lead + feed ----------
def photo_for(item_id, prefer=None):
    for p in PHOTOS:
        if (prefer and p.get('id') == prefer) or (not prefer and item_id in (p.get('fits_items') or [])):
            if p.get('id') in LOCAL:
                return p
    return None

def figure(p, cls='', sizes='(min-width: 1180px) 40vw, 100vw', eager=False):
    if not p:
        return ''
    loc = LOCAL[p['id']]
    w, h = loc['w'], loc['h']
    load = 'eager" fetchpriority="high' if eager else 'lazy'
    cap = tr_text(p.get('caption_tr', ''))
    return (f'<figure class="foto {cls}"><img src="{loc["src"]}" srcset="{loc["srcset"]}" sizes="{sizes}" width="{w}" height="{h}" alt="{e(cap)}" loading="{load}" decoding="async">'
            f'<figcaption><span class="foto__arsiv">Arşiv</span> {e(cap)} <span class="foto__kredi">{isr("nirengi")}{e(p.get("place_tr", ""))} · {e(p.get("author", ""))} · {e(p.get("license", ""))} · Wikimedia Commons</span></figcaption></figure>')

def manset():
    it = BY_ID[MANSET]
    p = photo_for(it['id'])
    lede = tr_text(first(it['summary_tr']))
    return f'''<article class="manset" aria-labelledby="manset-baslik">
    <div class="manset__metin">
      <h1 id="manset-baslik"><a href="{e(it["source_url"])}" target="_blank" rel="noopener">{T(it["headline_tr"])}</a></h1>
      <p class="manset__yer">{isr(sym_of(it), 'bugun isr--iri')}<span class="yer">{T(place_label(it))}</span><span class="zaman">{saat(it["time"])}</span></p>
      <p class="manset__ozet">{e(lede)}</p>
      <p class="kaynak">Kaynak: {src_link(it)}, {date_tr(it["date"])}</p>
    </div>
    {figure(p, 'manset__foto', eager=True)}
  </article>'''

def kayit(it, rich=False, h='h3', anchor=False):
    s = sym_of(it)
    tone = 'bugun' if is_today(it) else 'dun'
    cls = ' gelisen' if it['kind'] == 'son-dakika' else ''
    extra = f'<p class="kayit__ozet">{T(first(it["summary_tr"]))}</p>' if rich else ''
    ida = f' id="k-{it["id"]}"' if anchor else ''
    wide = '' if is_today(it) else ' kayit--gun'
    return (f'<li class="kayit{wide}"{ida} data-id="{it["id"]}" data-cat="{s}">'
            f'<span class="zaman">{zaman(it)}</span>{isr(s, tone + cls)}'
            f'<div class="kayit__metin"><{h} class="kayit__baslik"><a href="{e(it["source_url"])}" target="_blank" rel="noopener">{T(it["headline_tr"])}</a></{h}>'
            f'<span class="yer">{T(place_label(it, True))}</span>{extra}</div></li>')

def akis():
    items = [i for i in TODAY_ITEMS if i['id'] != MANSET]
    first, rest = items[:6], items[6:]
    return f'''<section class="akis" aria-labelledby="akis-baslik">
    <div class="akis__ust"><h2 id="akis-baslik">Akış</h2><span class="num">{date_tr(TODAY, year=False)} · {len(TODAY_ITEMS)} kayıt</span></div>
    <ol class="akis__liste">{"".join(kayit(i, anchor=True) for i in first)}</ol>
    <details class="akis__devam"><summary>Günün kalan {len(rest)} kaydı</summary><ol class="akis__liste">{"".join(kayit(i, anchor=True) for i in rest)}</ol></details>
    <p class="akis__bos" hidden>Bu türde bugün kayıt yok. <button type="button" data-filtre-sifirla>Süzgeci kaldır</button></p>
  </section>'''

# ---------- İl il: north to south ----------
WB_ORDER = ['cenin', 'tubas', 'tulkerem', 'nablus', 'kalkilya', 'selfit', 'ramallah', 'eriha', 'kudus', 'beytullahim', 'el-halil']

def dms(lat):
    d = int(lat); m = round((lat - d) * 60)
    if m == 60: d, m = d + 1, 0
    return f'{d}°{m:02d}′'

def locator(gid):
    g = GOV[gid]
    return (f'<svg class="bulucu" viewBox="380 0 700 1371" aria-hidden="true" focusable="false"><use href="#bulucu-taban" x="380" y="0" width="700" height="1371"/>'
            f'<path class="secili" d="{g["lo"]}" fill="url(#bulucu-tarama)"/></svg>')

def locator_defs():
    wb_govs = ''.join(g['lo'] for g in geo['govs'] if not g['gaza'])
    return (f'<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
            f'<pattern id="bulucu-tarama" width="64" height="64" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V64" class="tarama"/></pattern>'
            f'<symbol id="bulucu-taban" viewBox="380 0 700 1371"><path class="bulucu__zemin" d="{geo["wbLo"]}"/><path class="bulucu__iller" d="{wb_govs}"/></symbol>'
            f'</defs></svg>')

def ilil():
    rows = []
    for gid in WB_ORDER:
        g = GOV[gid]
        items = by_time([i for i in ITEMS if GOV_NAME_TO_ID.get(i.get('governorate_tr')) == gid])
        lat_lo, lat_hi = g['lat']
        counts = Counter(sym_of(i) for i in items if is_today(i))
        cnt = ''.join(f'<li>{isr(s, "bugun")}<b class="num">{n}</b></li>' for s, n in counts.most_common())
        if items:
            lead, others = items[0], items[1:4]
            body = (f'<article class="il__manset"><h3><a href="{e(lead["source_url"])}" target="_blank" rel="noopener">{T(lead["headline_tr"])}</a></h3>'
                    f'<p class="il__ust">{isr(sym_of(lead), "bugun" if is_today(lead) else "dun")}<span class="yer">{T(lead.get("place_tr") or g["name"])}</span>'
                    f'<span class="zaman">{zaman(lead)}</span></p>'
                    f'<p>{T(first(lead["summary_tr"]))}</p></article>'
                    + (f'<ol class="il__diger">{"".join(kayit(i) for i in others)}</ol>' if others else '<p class="il__sessiz">Son üç günde başka kayıt yok.</p>'))
        else:
            body = '<p class="il__sessiz il__sessiz--tek">Son üç günde bu ilden kayıt gelmedi.</p>'
        rows.append(f'''<li class="il" id="il-{gid}" data-lat="{(lat_lo + lat_hi) / 2:.3f}" data-il="{gid}">
      <div class="il__kimlik">{locator(gid)}<div><h3 class="il__ad">{e(g["name"])}</h3><p class="il__enlem num">{dms(lat_hi)}–{dms(lat_lo)} K</p>
      {f'<ul class="il__sayac" aria-label="Bugünün kayıtları">{cnt}</ul>' if cnt else ''}</div></div>
      <div class="il__icerik">{body}</div>
    </li>''')
    ticks = []
    for k in range(0, 15):
        lat = 32.55 - k * (1.2 / 14)
        ticks.append(f'<li style="top:{k / 14 * 100:.2f}%"><span class="num">{dms(lat)}</span></li>')
    return f'''<section class="ilil ic bant" id="bati-seria" aria-labelledby="ilil-baslik">
  <div class="baslik"><h2 id="ilil-baslik">İl il Batı Şeria</h2><p>Kuzeyden güneye, Cenin’den El Halil’e. Okudukça güneye inersiniz.</p></div>
  {locator_defs()}
  <div class="ilil__govde">
    <aside class="enlem" aria-hidden="true"><div class="enlem__ic"><ol class="enlem__cetvel">{"".join(ticks)}</ol><span class="enlem__imlec"><b class="num">32°27′ K</b><i>Cenin</i></span></div></aside>
    <ol class="ilil__liste">{"".join(rows)}</ol>
  </div>
</section>'''

# ---------- Toprak: olive harvest and the roads ----------
def nums(item_id):
    return BY_ID[item_id].get('numbers', [])

def toprak():
    f46 = BY_ID['f46']; f09 = BY_ID['f09']
    total, harvest = 219, 136
    # one orchard mark per recorded attack, 1–12 October; harvest-linked ones overprinted
    cells = ''.join(f'<i class="{"h" if k < harvest else ""}"></i>' for k in range(total))
    years = [('2022', 136, ''), ('2023', 333, ''), ('2024', 407, ''), ('2025', 441, '+'), ('2026 · 1–12 Ekim', 136, '')]
    mx = 460
    bars = ''.join(f'<li class="{"simdi" if y.startswith("2026") else ""}"><span class="num">{y}</span><i style="--w:{v / mx * 100:.2f}%"></i><b class="num">{v}{plus}</b></li>' for y, v, plus in years)
    gates_total, gates_new = 917, 244
    gate_ticks = ''.join(f'<i{" class=\"y\"" if k >= gates_total - gates_new else ""}></i>' for k in range(gates_total))
    stories = by_time([i for i in ITEMS if i['category'] in ('zeytin-hasadı',) and i.get('governorate_tr')])[:6]
    gates = by_time([i for i in ITEMS if i['category'] == 'kapı-kontrol-noktası'])
    return f'''<section class="toprak ic bant" id="toprak" aria-labelledby="toprak-baslik">
  <div class="baslik"><h2 id="toprak-baslik">Toprak: zeytin hasadı 2026</h2><p>Ekim, hasat ayı. Hasat aynı zamanda saldırıların en yoğun olduğu dönem.</p></div>
  <div class="toprak__govde">
    <figure class="zeytinlik">
      <div class="zeytinlik__alan" role="img" aria-label="219 işaretten oluşan alan: her işaret bir saldırı; 136'sı zeytin hasadıyla bağlantılı">{cells}</div>
      <figcaption>
        <p class="buyuk-rakam num">219</p>
        <p><b>saldırı, 1–12 Ekim.</b> Her işaret bir kayıt. Mor olan <b class="num">136</b> saldırı doğrudan zeytin hasadıyla bağlantılı: toplayanlara saldırı, araziye erişimin engellenmesi, ürün hırsızlığı, ağaç tahribi.</p>
        <p class="kaynak">Kaynak: {src_link(f46, "Duvar ve Yerleşim Karşıtı Komisyon")}, ön sayım, 12 Ekim 2026</p>
      </figcaption>
    </figure>
    <div class="hasat-yillar">
      <h3>Hasat dönemi saldırıları</h3>
      <ol>{bars}</ol>
      <p class="kaynak">Çubuklar ölçekli. 2026 satırı yalnız ilk 12 günün ön sayımı. Kaynak: Duvar ve Yerleşim Karşıtı Komisyon</p>
    </div>
    <p class="filtre-bag"><a href="#pafta" data-filtre-git="zeytin">{isr('zeytin', 'bugun')}Bugünün zeytin hasadı kayıtları haritada ve akışta <b class="num">{sum(1 for i in TODAY_ITEMS if sym_of(i) == 'zeytin')}</b>{ui('ok')}</a> <span class="kaynak">Önceki günlerin kayıtları il il bölümünde.</span></p>
  </div>
  <div class="kapilar">
    <div class="kapilar__ust"><h3>Yolun ölçeği</h3><p><b class="num">917</b> askeri kontrol noktası ve kapı. Her çizgi bir engel; mor olan <b class="num">244</b> kapı 7 Ekim 2023’ten sonra kuruldu.</p></div>
    <div class="kapilar__cetvel" role="img" aria-label="917 çizgi: her biri bir kontrol noktası ya da kapı, son 244'ü 7 Ekim 2023 sonrası">{gate_ticks}</div>
    <div class="kapilar__etiket num"><span>0</span><span>250</span><span>500</span><span>750</span><span>917</span></div>
    <p class="kaynak">Kaynak: Duvar ve Yerleşim Karşıtı Komisyon, Temmuz 2026 ({src_link(f09, "WAFA")} aktarımı)</p>
    <p class="filtre-bag"><a href="#pafta" data-filtre-git="kapi">{isr('kapi', 'bugun')}Bugünün kapı ve kontrol noktası kayıtları <b class="num">{sum(1 for i in TODAY_ITEMS if sym_of(i) == 'kapi')}</b>{ui('ok')}</a></p>
  </div>
</section>'''

# ---------- Gazze ----------
def gazze():
    items = by_time([i for i in ITEMS if i['region'] == 'gazze'])
    f15, f11 = BY_ID['f15'], BY_ID['f11']
    fx, fy, fw, fh = geo['gzFrame']
    pad = 30
    sub = pafta([i for i in ITEMS if i['region'] == 'gazze'], cls='gazze-pafta', title_id='gazze-pafta-baslik', size=26, interactive=False, wb=False, fs=15)
    sub = sub.replace(f'viewBox="0 0 {W} {H}"', f'viewBox="{fx + 8} {fy + 6} {fw - 16} {fh - 12}"')
    figs = [('74.392', 'kişi 7 Ekim 2023’ten bu yana hayatını kaybetti', f15), ('1.501', 'kişi 11 Ekim 2025 ateşkesinden bu yana hayatını kaybetti', f15),
            ('2.027', 'hasta tedavi ya da tahliye beklerken öldü', f11), ('227 / 574', 'sağlık merkezi bugün çalışıyor', f11)]
    stats = ''.join(f'<tr><th scope="row" class="num">{v}</th><td>{t}<span class="kaynak">{src_link(it)}</span></td><td class="num">{date_tr(it["date"], year=False)}</td></tr>' for v, t, it in figs)
    return f'''<section class="gazze ic bant" id="gazze" aria-labelledby="gazze-baslik">
  <div class="baslik"><h2 id="gazze-baslik">Gazze Şeridi</h2><p>Ateşkesin birinci yılı: sayılar Gazze sağlık kaynaklarından, her biri tarihiyle.</p></div>
  <div class="gazze__govde">
    <div class="gazze__harita"><h3 class="sr" id="gazze-pafta-baslik">Gazze Şeridi, son üç günün kayıtları</h3>{sub}</div>
    <table class="lejant-cizelge gazze__rakam"><caption class="sr">Gazze sayıları</caption><thead><tr><th scope="col">Sayı</th><th scope="col">Ne</th><th scope="col">Tarih</th></tr></thead><tbody>{stats}</tbody></table>
    <ol class="gazze__haber">{"".join(kayit(i, rich=True) for i in items if i['id'] not in ('f15', 'f11', 'f45'))}</ol>
  </div>
</section>'''

# ---------- Esirler, Kudüs ----------
def esirler():
    f13, f43 = BY_ID['f13'], BY_ID['f43']
    rows = [('9.400', 'Filistinli İsrail hapishanelerinde', '14 Ekim', f13), ('3.101', 'idari tutuklu, suçlama ve yargılama olmadan', '1 Ekim', f13),
            ('350', 'çocuk esir', '1 Ekim', f13), ('91', 'kadın esir', '1 Ekim', f13),
            ('26.000+', 'gözaltı, 7 Ekim 2023’ten bu yana Batı Şeria’da', '6 Ekim', f13), ('80', 'serbest bırakılan esir yeniden gözaltında ya da sorguda', '13 Ekim', f43)]
    tab = ''.join(f'<tr><th scope="row" class="num">{v}</th><td>{t}</td><td class="num">{d}</td></tr>' for v, t, d, _ in rows)
    items = by_time([i for i in ITEMS if i['region'] == 'esirler' or i['category'] == 'esir'])
    return f'''<section class="esirler" id="esirler" aria-labelledby="esirler-baslik">
  <div class="baslik"><h2 id="esirler-baslik">Esirler</h2></div>
  <table class="lejant-cizelge"><caption class="sr">Esir sayıları</caption><thead><tr><th scope="col">Sayı</th><th scope="col">Kim</th><th scope="col">Tarih</th></tr></thead><tbody>{tab}</tbody></table>
  <p class="kaynak">Kaynak: Esir İşleri Kurumu, Filistinli Esirler Kulübü, Addameer ortak verisi ({src_link(f13, "WAFA")})</p>
  <ol class="esirler__haber">{"".join(kayit(i) for i in items if i['id'] not in ('f13',))}</ol>
</section>'''

def kudus():
    items = by_time([i for i in ITEMS if i['region'] == 'kudüs' or (i.get('governorate_tr') == 'Kudüs' and i['region'] != 'esirler')])
    f12, f33 = BY_ID['f12'], BY_ID['f33']
    return f'''<section class="kudus" id="kudus" aria-labelledby="kudus-baslik">
  <div class="baslik"><h2 id="kudus-baslik">Kudüs</h2></div>
  <table class="lejant-cizelge"><caption class="sr">Kudüs sayıları</caption><thead><tr><th scope="col">Sayı</th><th scope="col">Ne</th><th scope="col">Tarih</th></tr></thead><tbody>
    <tr><th scope="row" class="num">23.280</th><td>yıkım kararı yürürlükte <span class="kaynak">{src_link(f12)}</span></td><td class="num">14 Ekim</td></tr>
    <tr><th scope="row" class="num">%1</th><td>ruhsat başvurularından olumlu sonuçlanan, en fazla <span class="kaynak">{src_link(f12)}</span></td><td class="num">14 Ekim</td></tr>
    <tr><th scope="row" class="num">888+</th><td>İsrailli, bir önceki hafta Mescid-i Aksa’ya girdi <span class="kaynak">{src_link(f33, "Kuds Haber Ağı")}</span></td><td class="num">13 Ekim</td></tr>
  </tbody></table>
  <ol class="kudus__haber">{"".join(kayit(i) for i in items)}</ol>
</section>'''

# ---------- Rakamlar: numbers with leader lines to their sources ----------
def rakamlar():
    picks = [('790.000', 'yerleşimci Batı Şeria’da', 'f22', 'Filistin Merkezi İstatistik Bürosu', '31 Temmuz 2026'),
             ('647', 'yerleşimci saldırısı, yalnız Eylül 2026’da', 'f39', 'Duvar ve Yerleşim Karşıtı Komisyon', '30 Eylül 2026'),
             ('23', 'cami 2023’ten bu yana kundaklandı ya da kundaklanmaya çalışıldı', 'f01', 'Duvar ve Yerleşim Karşıtı Komisyon', '11 Ekim 2026'),
             ('9.334', 'zeytin ağacı yalnız Eylül 2026’da zarar gördü', 'f46', 'Duvar ve Yerleşim Karşıtı Komisyon', '30 Eylül 2026'),
             ('21.000+', 'hasta Gazze’den tıbbi tahliye bekliyor', 'f11', 'Filistin Tıbbi Yardım Derneği', '14 Ekim 2026'),
             ('118', 'çoban topluluğu 2023–2025 arasında yerinden edildi', 'f22', 'Filistin Merkezi İstatistik Bürosu', '14 Ekim 2026')]
    lis = ''.join(f'<li><b class="num">{v}</b><span class="rakam__metin">{t}</span><span class="rakam__bag" aria-hidden="true"></span><span class="kaynak">{src_link(BY_ID[i], s)}<br><span class="num">{d}</span></span></li>' for v, t, i, s, d in picks)
    return f'''<section class="rakamlar ic bant" id="rakamlar" aria-labelledby="rakamlar-baslik">
  <div class="baslik"><h2 id="rakamlar-baslik">Rakamlarla bugün</h2><p>Her sayının altında kaynağı ve tarihi var. Kaynağı olmayan sayı burada yer almaz.</p></div>
  <ol class="rakamlar__liste">{lis}</ol>
</section>'''

def foto():
    want = ['p24', 'p32', 'p23', 'p20', 'p26', 'p07']    # olives by hand, the wall, Kalandiya, the Dome, Gaza, Beyta
    pid = {p['id']: p for p in PHOTOS}
    picks = [pid[k] for k in want if k in pid and k in LOCAL]
    figs = ''.join(figure(p, 'galeri__oge', sizes='(min-width: 900px) 33vw, 100vw') for p in picks)
    return f'''<section class="galeri ic bant" id="foto" aria-labelledby="foto-baslik">
  <div class="baslik"><h2 id="foto-baslik">Fotoğraf arşivi</h2><p>Bu prototipteki kareler arşivdir; olay anında çekilmedi. Her karede çeken ve lisansı yazılı.</p></div>
  <div class="galeri__izgara">{figs}</div>
</section>'''

def analiz():
    topics = [BY_ID['f30'], BY_ID['f43']]
    cards = ''.join(f'''<article class="analiz__oge"><h3>{T(t["headline_tr"])}</h3><p class="analiz__yazar">[Yazar adı] · Analiz</p><p class="yer-tutucu">[Yorum metni: yazar bekleniyor. Konu bugünün kayıtlarından seçildi.]</p><p class="kaynak">Konu kaynağı: {src_link(t)}</p></article>''' for t in topics)
    return f'''<section class="analiz ic bant" id="analiz" aria-labelledby="analiz-baslik">
  <div class="baslik"><h2 id="analiz-baslik">Analiz</h2><p>Yazar adları ve yorum metinleri yer tutucudur; konular günün kayıtlarından.</p></div>
  <div class="analiz__izgara">{cards}
    <form class="bulten" id="bulten" action="#" onsubmit="return false">
      <h3>Günün paftası e-postanızda</h3>
      <p>Her akşam 20.00’de: günün kayıtları, haritası ve kaynakları.</p>
      <label for="bulten-eposta">E-posta adresi</label>
      <div class="bulten__satir"><input id="bulten-eposta" type="email" autocomplete="email" placeholder="ad@ornek.com" required><button class="dugme" type="submit">Abone ol</button></div>
      <p class="bulten__durum" role="status" aria-live="polite"></p>
    </form>
  </div>
</section>'''

def yukleyici():
    """Loader: three known points (the İ dots) sight the fourth (the nirengi) and the name settles into the header."""
    m = logo['mark']
    return f'<div class="yukleyici" aria-hidden="true"><div class="yukleyici__sahne">{logo_svg("yukleyici__logo")}<svg class="yukleyici__isinlar"></svg></div></div>'

def build_home():
    tpl = open(P('tools', 'tpl', 'home.html'), encoding='utf-8').read()
    rep = {
        'V': V, 'LEJANT': part('lejant.html'), 'YUKLEYICI': yukleyici(), 'YAKA': yaka(), 'UST': ust(), 'CANLI': canli(),
        'MANSET': manset(), 'SERIT': serit(), 'AKIS': akis(), 'PAFTA': pafta_block(), 'ILIL': ilil(), 'TOPRAK': toprak(), 'GAZZE': gazze(),
        'ESIRLER': esirler(), 'KUDUS': kudus(), 'RAKAMLAR': rakamlar(), 'FOTO': foto(), 'ANALIZ': analiz(), 'ALT': alt(), 'CEKMECE': cekmece(),
    }
    out = re.sub(r'\{\{(\w+)\}\}', lambda m: rep[m.group(1)], tpl)
    out = out.replace('<!doctype html>', '<!doctype html>\n<!-- generated by tools/build.py from tools/tpl/home.html — do not edit by hand -->', 1)
    open(P('home.html'), 'w', encoding='utf-8').write(out)
    return len(out)

if __name__ == '__main__':
    print('home.html', build_home(), 'bytes')
    if os.path.exists(P('tools', 'tpl', 'index.html')):
        import importlib.util
        spec = importlib.util.spec_from_file_location('kilavuz', P('tools', 'kilavuz.py'))
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        print('index.html', mod.build(globals()), 'bytes')
