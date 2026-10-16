"""Builds the Filistin Ajansı pages (round 2: the Turkish news-portal canon the client asked for).

python -I tools/build.py   (from the project root; run tools/logos.py and tools/photos.py first)

tools/tpl/home.html  -> home.html   (Turkish homepage, close to the Hürriyet arrangement)
tools/tpl/index.html -> index.html  (Arabic page presenting the four logo options)
Never hand-edit the generated pages: edit the templates or the data, then rebuild.
"""
import json, os, re, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *p: os.path.join(ROOT, *p)
V = '38'   # asset version: bump on every CSS/JS change

NEWS = json.load(open(P('research', 'news.json'), encoding='utf-8'))
ITEMS = NEWS['items']
BY_ID = {i['id']: i for i in ITEMS}
PH = json.load(open(P('research', 'photos.json'), encoding='utf-8'))
PH = PH['photos'] if isinstance(PH, dict) else PH
PHOTO = {p['id']: p for p in PH}
LOCAL = json.load(open(P('tools', 'out', 'photos-local.json'), encoding='utf-8'))
LOGOS = json.load(open(P('tools', 'out', 'logos.json'), encoding='utf-8'))
TODAY = NEWS['edition']['date']
EDITION_TIME = NEWS['edition']['time']

AY = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
GUN = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']

# ---------- editorial plan for this edition: every photo shows the place or subject of its story ----------
# No photo appears twice on the page. A story without a picture of its own place gets no picture:
# it goes into a headline list instead of borrowing someone else's photo.
SLIDER = [('f17', 'p03'), ('f14', 'p04'), ('f15', 'p26'), ('f16', 'p07'), ('f33', 'p21'),
          ('f13', 'p34'), ('f02', 'p09'), ('f11', 'p29'), ('f23', 'p16'), ('f29', 'p01')]
SICAK = [('Zeytin hasadı', 'f46', 'p24'), ('Gazze’de kış', 'f30', 'p27'), ('Arap Birliği', 'f28', 'p31')]
ALT_SIRA = [('f37', 'p30'), ('f06', 'p15'), ('f19', 'p18'), ('f35', 'p12')]
BOLUM = {
    'bati-seria': {'ad': 'Batı Şeria', 'diger': 'Batı Şeria’dan diğer haberler', 'buyuk': ('f03', 'p11'),
                   'yan': [('f04', 'p14'), ('f44', 'p13'), ('f47', 'p10')], 'yan_liste': ['f07', 'f08', 'f09'],
                   'sira': [],
                   'liste': ['f01', 'f18', 'f21', 'f26', 'f34', 'f36', 'f40', 'f48']},
    'kudus': {'ad': 'Kudüs', 'diger': 'Kudüs’ten diğer haberler', 'buyuk': ('f32', 'p22'),
              'yan': [('f20', 'p19'), ('f24', 'p05')], 'yan_liste': ['f12', 'f05', 'f38'], 'sira': [], 'liste': []},
    'gazze': {'ad': 'Gazze', 'diger': 'Gazze’den diğer haberler', 'buyuk': ('f25', 'p25'),
              'yan': [('f50', 'p28')], 'yan_liste': ['f45', 'f31', 'f41', 'f15'], 'ozet': True, 'sira': [], 'liste': []},
}
ESIR = ('f10', 'p33')
ESIR_LISTE = ['f43', 'f38', 'f13']
ESIR_RAKAM = [('9.400', 'Filistinli İsrail hapishanelerinde', '14 Ekim'), ('3.101', 'idari tutuklu, yargılanmadan', '1 Ekim'),
              ('350', 'çocuk esir', '1 Ekim'), ('91', 'kadın esir', '1 Ekim')]
GALERI = ['p20', 'p32', 'p23', 'p17', 'p08', 'p02', 'p06']
RAKAM = [('9.400', 'Filistinli İsrail hapishanelerinde', 'Filistinli Esirler Kulübü, 14 Ekim', 'f13'),
         ('74.392', 'kişi Gazze’de 7 Ekim 2023’ten bu yana hayatını kaybetti', 'Gazze sağlık kaynakları, 14 Ekim', 'f15'),
         ('219', 'saldırı 1–12 Ekim arasında; 136’sı zeytin hasadıyla bağlantılı', 'Duvar ve Yerleşim Karşıtı Komisyon', 'f46'),
         ('917', 'askeri kontrol noktası ve kapı Batı Şeria’da', 'Duvar ve Yerleşim Karşıtı Komisyon, Temmuz', 'f09')]
TOPICS = [('ZEYTİN HASADI', 'f46'), ('TEKUA', 'f07'), ('GAZZE', 'f15'), ('ESİRLER', 'f13'), ('KUDÜS', 'f12'), ('TAMMUN', 'f02'), ('MUHMAS', 'f24')]

# a photo id with a «b» suffix means «the same photo again»: allowed only where no other picture of the place exists
def photo_id(pid):
    return pid[:-1] if pid and pid.endswith('b') else pid

# ---------- text helpers ----------
def e(s):
    return html.escape(str(s), quote=True)

def tr_text(s):
    s = re.sub(r"(?<=\w)'(?=\w)", '’', s)
    s = re.sub(r'"([^"]+)"', r'“\1”', s)
    return re.sub(r"'([^']+)'", r'‘\1’', s)

def T(s):
    return e(tr_text(s))

def date_tr(d, weekday=False, year=True):
    y, m, dd = map(int, d.split('-'))
    out = f'{dd} {AY[m - 1]}' + (f' {y}' if year else '')
    return out + (f' {GUN[datetime.date(y, m, dd).weekday()]}' if weekday else '')

def saat(t):
    return t.replace(':', '.') if t else ''

def zaman(it):
    if it['date'] == TODAY:
        return saat(it['time']) or date_tr(it['date'], year=False)
    return f'{date_tr(it["date"], year=False)}{", " + saat(it["time"]) if it["time"] else ""}'

def first(text):
    return re.split(r'(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ“"‘])', text.strip(), maxsplit=1)[0]

def etiket(it):
    """The red tag under a headline: the place, Hürriyet-style, as a hashtag."""
    p = it.get('place_tr') or it.get('governorate_tr') or {'gazze': 'Gazze', 'kudüs': 'Kudüs', 'esirler': 'Esirler'}.get(it['region'], 'Filistin')
    p = re.sub(r'\s*\(.*?\)', '', p)
    return '#' + p.upper().replace('İ', 'İ')

def link(it, inner, cls=''):
    return f'<a class="{cls}" href="{e(it["source_url"])}" target="_blank" rel="noopener">{inner}</a>'

def img(pid, sizes, cls='', eager=False, alt=None):
    pid = photo_id(pid)
    if not pid or pid not in LOCAL:
        return ''
    loc, p = LOCAL[pid], PHOTO[pid]
    a = alt if alt is not None else tr_text(p.get('caption_tr', ''))
    load = 'eager" fetchpriority="high' if eager else 'lazy'
    return (f'<img class="{cls}" src="{loc["src"]}" srcset="{loc["srcset"]}" sizes="{sizes}" width="{loc["w"]}" height="{loc["h"]}" '
            f'alt="{e(a)}" loading="{load}" decoding="async">')

def kredi(pid):
    p = PHOTO[photo_id(pid)]
    return f'Arşiv · {e(p.get("author", ""))} · {e(p.get("license", ""))}'

# ---------- components ----------
def kart(iid, pid, size='orta', ozet=False):
    """A card: archive photo on top, headline, red place tag. Without a photo it becomes a text card."""
    it = BY_ID[iid]
    sizes = {'buyuk': '(min-width: 1000px) 640px, 100vw', 'orta': '(min-width: 1000px) 300px, (min-width: 640px) 45vw, 100vw', 'kucuk': '(min-width: 1000px) 200px, 40vw'}[size]
    pic = img(pid, sizes) if pid else ''
    media = f'<span class="kart__foto">{pic}<span class="arsiv" title="{kredi(pid)}">Arşiv</span></span>' if pic else ''
    oz = f'<p class="kart__ozet">{T(first(it["summary_tr"]))}</p>' if ozet else ''
    cls = f'kart kart--{size}' + ('' if pic else ' kart--metin')
    return (f'<article class="{cls}">{link(it, media + f"<h3 class='kart__baslik'>{T(it['headline_tr'])}</h3>", "kart__bag")}'
            f'{oz}<p class="kart__alt"><span class="etiket">{e(etiket(it))}</span><span class="zaman">{zaman(it)}</span></p></article>')

def satir(iid):
    it = BY_ID[iid]
    return (f'<li class="satir"><span class="zaman">{zaman(it)}</span>'
            f'<div>{link(it, T(it["headline_tr"]), "satir__baslik")}<span class="etiket">{e(etiket(it))}</span></div></li>')

def bolum_basi(sid, ad, more=True):
    m = f'<a class="bolum__tum" href="#{sid}">Tümü<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></a>' if more else ''
    return f'<div class="bolum__bas"><h2 id="{sid}-b">{e(ad)}</h2><span class="bolum__cizgi" aria-hidden="true"></span>{m}</div>'

_uid = [0]
def u(svg):
    """Each inline copy of a lockup gets its own pattern/clip ids, so repeated logos stay valid HTML."""
    _uid[0] += 1
    n = _uid[0]
    return re.sub(r'url\(#(\w+)\)', lambda m: f'url(#{m.group(1)}-{n})', re.sub(r'id="(\w+)"', lambda m: f'id="{m.group(1)}-{n}"', svg))

def logo_w(svg, h):
    vb = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', svg)
    return round(float(vb.group(3)) / float(vb.group(4)) * h)

def logo_ust():
    """All four white lockups ride in the header; the chosen one shows (default 1, ?logo=N to preview)."""
    return ''.join(f'<img class="logo__s" data-secenek="{k}" src="assets/brand/secenek-{k}-beyaz.svg?v={V}" alt="Filistin Ajansı" width="{logo_w(v["beyaz"], 32)}" height="32">' for k, v in LOGOS.items())

def logo_alt():
    return ''.join(f'<img class="logo__s" data-secenek="{k}" src="assets/brand/secenek-{k}.svg?v={V}" alt="Filistin Ajansı" width="{logo_w(v["renk"], 40)}" height="40">' for k, v in LOGOS.items())

ICON = {
    'menu': '<path d="M4 7h16M4 12h16M4 17h16"/>',
    'ara': '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    'kapat': '<path d="M6 6l12 12M18 6L6 18"/>',
    'sol': '<path d="M15 6l-6 6 6 6"/>', 'sag': '<path d="M9 6l6 6-6 6"/>',
    'yukari': '<path d="M6 15l6-6 6 6"/>', 'asagi': '<path d="M6 9l6 6 6-6"/>',
    'dur': '<path d="M9 6v12M15 6v12"/>', 'oynat': '<path d="M8 5.5v13l11-6.5z" class="dolu"/>',
    'x': '<path d="M5 4h4l10 16h-4zM19 4l-6.5 7.5M5 20l6.5-7.5"/>', 'ig': '<rect x="4" y="4" width="16" height="16" rx="4.5"/><circle cx="12" cy="12" r="3.6"/><circle cx="16.8" cy="7.2" r=".9" class="dolu"/>',
    'tg': '<path d="M20.5 4.5L3.5 11l6 2 2 6 3.5-4.5 4.5 3.5z"/>', 'yt': '<rect x="3" y="6" width="18" height="12" rx="3.5"/><path d="M10.5 9.5v5l4.5-2.5z" class="dolu"/>',
}
def ic(n, cls='ikon'):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICON[n]}</svg>'

MENU = [('#manset', 'Gündem'), ('#bati-seria', 'Batı Şeria'), ('#kudus', 'Kudüs'), ('#gazze', 'Gazze'), ('#esirler', 'Esirler'),
        ('#rakamlar', 'Rakamlar'), ('#galeri', 'Foto Galeri'), ('#son-dakika', 'Son Dakika')]

def ust():
    nav = ''.join(f'<a href="{h}">{e(t)}</a>' for h, t in MENU)
    return f'''<header class="ust">
  <div class="ust__ic">
    <button class="ust__dugme" type="button" data-menu aria-label="Menüyü aç" aria-expanded="false" aria-controls="cekmece">{ic("menu")}</button>
    <a class="logo" href="home.html" aria-label="Filistin Ajansı ana sayfa">{logo_ust()}</a>
    <nav class="ust__menu" aria-label="Bölümler">{nav}</nav>
    <a class="ust__dugme ust__ara" href="#ara" aria-label="Haberlerde ara">{ic("ara")}</a>
    <a class="ust__bulten" href="#bulten">Bülten</a>
  </div>
</header>'''

def cekmece():
    nav = ''.join(f'<a href="{h}" data-kapat>{e(t)}</a>' for h, t in MENU)
    return f'''<div class="cekmece" id="cekmece" role="dialog" aria-modal="true" aria-label="Menü" hidden>
  <div class="cekmece__ust"><span class="logo">{logo_ust()}</span><button class="ust__dugme" type="button" data-kapat aria-label="Menüyü kapat">{ic("kapat")}</button></div>
  <nav aria-label="Bölümler">{nav}</nav>
  <p class="cekmece__tarih">{date_tr(TODAY, weekday=True)} · {EDITION_TIME}</p>
</div>'''

def gundem():
    """«Bugün neler oldu?»: a crawl that loops, pauses under the pointer or focus, and stands still for reduced motion."""
    items = ''.join(f'<li><a href="{e(BY_ID[i]["source_url"])}" target="_blank" rel="noopener"><b>#{e(t)}</b> {T(BY_ID[i]["headline_tr"])}</a></li>' for t, i in TOPICS)
    copy = items.replace('<a ', '<a tabindex="-1" ')
    return f'''<div class="gundem" role="region" aria-label="Bugün neler oldu?">
  <div class="kap gundem__ic"><p class="gundem__ad">Bugün neler oldu?</p>
  <div class="gundem__pencere"><div class="gundem__serit" data-serit><ul class="gundem__liste">{items}</ul><ul class="gundem__liste" aria-hidden="true">{copy}</ul></div></div>
  <button class="gundem__ok" type="button" data-serit-dur aria-label="Kayan başlıkları durdur">{ic("dur", "ikon ikon--dur")}{ic("oynat", "ikon ikon--oynat")}</button></div>
</div>'''

def sicak():
    cards = ''
    for t, iid, pid in SICAK:
        it = BY_ID[iid]
        cards += (f'<article class="sicak__kart">{link(it, f"<span class=sicak__foto>{img(pid, '(min-width: 1000px) 300px, 80vw')}</span><span class=sicak__ust>{e(t)}</span><h3>{T(it['headline_tr'])}</h3>", "sicak__bag")}'
                  f'<span class="arsiv" title="{kredi(pid)}">Arşiv</span></article>')
    return f'<section class="sicak" aria-labelledby="sicak-b"><h2 class="sicak__ad" id="sicak-b">Sıcak Gündem</h2><div class="sicak__liste">{cards}</div></section>'

def manset():
    slides, dots = '', ''
    n = len(SLIDER)
    for k, (iid, pid) in enumerate(SLIDER):
        it = BY_ID[iid]
        on = ' is-aktif' if k == 0 else ''
        hidden = '' if k == 0 else ' aria-hidden="true"'
        slides += (f'<li class="manset__slayt{on}" id="slayt-{k + 1}" role="group" aria-roledescription="slayt" aria-label="{k + 1} / {n}"{hidden}>'
                   f'{link(it, img(pid, "(min-width: 1000px) 820px, 100vw", "manset__foto", eager=(k == 0), alt="") + f"<span class=manset__metin><span class=etiket>{e(etiket(it))}</span><span class=manset__baslik>{T(it['headline_tr'])}</span><span class=manset__zaman>{zaman(it)}</span></span>", "manset__bag")}'
                   f'<span class="arsiv arsiv--ust" title="{kredi(pid)}">Arşiv · {e(PHOTO[photo_id(pid)].get("place_tr", ""))}</span></li>')
        dots += f'<li><button type="button" data-slayt="{k}" aria-label="{k + 1}. haber" aria-controls="slayt-{k + 1}"{" aria-current=true" if k == 0 else ""}><span>{k + 1}</span></button></li>'
    today = sorted([x for x in ITEMS if x['date'] == TODAY], key=lambda x: x['time'] or '', reverse=True)
    son = ''.join(f'<li><span class="zaman">{saat(i["time"])}</span>{link(i, T(i["headline_tr"]))}</li>' for i in today[:15])
    return f'''<section class="manset-alan" id="manset" aria-label="Manşet">
  <div class="manset" role="region" aria-roledescription="karusel" aria-label="Günün öne çıkan haberleri" data-karusel>
    <div class="manset__sahne">
      <ul class="manset__slaytlar" aria-live="off">{slides}</ul>
      <button type="button" class="manset__yan manset__yan--sol" data-onceki aria-label="Önceki haber">{ic("sol")}</button>
      <button type="button" class="manset__yan manset__yan--sag" data-sonraki aria-label="Sonraki haber">{ic("sag")}</button>
      <span class="manset__ilerleme" aria-hidden="true"><i></i></span>
    </div>
    <div class="manset__kontrol">
      <ol class="manset__noktalar">{dots}</ol>
      <button type="button" class="manset__dur" data-dur aria-label="Otomatik geçişi durdur">{ic("dur", "ikon ikon--dur")}{ic("oynat", "ikon ikon--oynat")}</button>
    </div>
  </div>
  <aside class="son" id="son-dakika" aria-labelledby="son-b" data-son>
    <div class="son__bas"><h2 class="son__ad" id="son-b"><span class="son__nokta" aria-hidden="true"></span>Son Dakika</h2>
      <div class="son__kontrol"><span class="son__sayfa" aria-live="polite">1 / 1</span>
      <button type="button" data-son-geri aria-label="Önceki son dakika haberleri">{ic("yukari")}</button>
      <button type="button" data-son-ileri aria-label="Sonraki son dakika haberleri">{ic("asagi")}</button></div></div>
    <div class="son__pencere"><ol class="son__liste">{son}</ol></div>
    <a class="son__tum" href="#bati-seria">Tüm haberler{ic("sag")}</a>
  </aside>
</section>'''

def alt_sira():
    return f'<section class="sira4" aria-label="Öne çıkanlar">{"".join(kart(i, p) for i, p in ALT_SIRA)}</section>'

def yan_liste(ids, ad='Son haberler', ozet=False):
    """Side list; with ozet each row carries two lines of the story, for columns that would otherwise stand half empty."""
    def row(it):
        oz = f'<p class="yan-liste__ozet">{T(first(it["summary_tr"]))}</p>' if ozet else ''
        return f'<li><span class="zaman">{zaman(it)}</span><div>{link(it, T(it["headline_tr"]))}{oz}</div></li>'
    rows = ''.join(row(BY_ID[i]) for i in ids)
    return f'<div class="yan-liste"><h3>{e(ad)}</h3><ol>{rows}</ol></div>'

def bolum(sid):
    b = BOLUM[sid]
    big = kart(*b['buyuk'], size='buyuk', ozet=True)
    yan = ''.join(kart(i, p, 'kucuk') for i, p in b['yan']) + (yan_liste(b['yan_liste'], ozet=b.get('ozet', False)) if b['yan_liste'] else '')
    liste = f'<div class="bolum__liste"><h3 class="bolum__liste-ad">{e(b["diger"])}</h3><ol>{"".join(satir(i) for i in b["liste"])}</ol></div>' if b['liste'] else ''
    return f'''<section class="bolum" id="{sid}" aria-labelledby="{sid}-b">
  {bolum_basi(sid, b["ad"])}
  <div class="bolum__ust"><div class="bolum__buyuk">{big}</div><div class="bolum__yan">{yan}</div></div>
  {liste}
</section>'''

def esirler():
    f13 = BY_ID['f13']
    nums = ''.join(f'<li><b>{v}</b><span>{t}</span><small>{d}</small></li>' for v, t, d in ESIR_RAKAM)
    return f'''<section class="bolum" id="esirler" aria-labelledby="esirler-b">
  {bolum_basi("esirler", "Esirler")}
  <div class="esir">
    {kart(*ESIR, size='orta', ozet=True)}
    <div class="esir__rakam"><h3>Hapishanelerde bugün</h3><ul>{nums}</ul>
      <a class="esir__kaynak" href="{e(f13["source_url"])}" target="_blank" rel="noopener">Kaynak: Esir İşleri Kurumu, Esirler Kulübü, Addameer</a></div>
    {yan_liste(ESIR_LISTE, 'Esirlerden haberler', ozet=True)}
  </div>
</section>'''

def rakamlar():
    lis = ''.join(f'<li><b>{v}</b><span>{t}</span><a class="rakam__kaynak" href="{e(BY_ID[i]["source_url"])}" target="_blank" rel="noopener">Kaynak: {e(s)}</a></li>' for v, t, s, i in RAKAM)
    return f'''<section class="rakam" id="rakamlar" aria-labelledby="rakamlar-b">
  <div class="kap">{bolum_basi("rakamlar", "Rakamlarla Filistin", more=False)}<ul class="rakam__liste">{lis}</ul></div>
</section>'''

def galeri():
    """A photo carousel: equal 3:2 frames, native scroll-snap, arrows and a counter."""
    figs = ''
    n = len(GALERI)
    for k, pid in enumerate(GALERI):
        p = PHOTO[pid]
        figs += (f'<li class="galeri__oge" role="group" aria-roledescription="fotoğraf" aria-label="{k + 1} / {n}"><figure>{img(pid, "(min-width: 1000px) 400px, 80vw")}'
                 f'<figcaption><b>{e(p.get("place_tr", ""))}</b><span class="galeri__metin">{T(p.get("caption_tr", ""))}</span><span class="galeri__kredi">{kredi(pid)}</span></figcaption></figure></li>')
    return f'''<section class="galeri" id="galeri" aria-labelledby="galeri-b" data-galeri>
  <div class="kap">
    <div class="bolum__bas"><h2 id="galeri-b">Foto Galeri</h2><span class="bolum__cizgi" aria-hidden="true"></span>
      <div class="galeri__kontrol"><span class="galeri__sayac" aria-live="polite">1 / {n}</span>
      <button type="button" data-galeri-geri aria-label="Önceki fotoğraf">{ic("sol")}</button><button type="button" data-galeri-ileri aria-label="Sonraki fotoğraf">{ic("sag")}</button></div></div>
    <p class="galeri__not">Arşiv kareleri: olay anında çekilmedi. Her karede çeken ve lisans yazılı.</p>
  </div>
  <ul class="galeri__serit" tabindex="0" aria-label="Fotoğraflar, yatay kaydırılır">{figs}</ul>
</section>'''

def bulten():
    return '''<section class="bulten" id="bulten" aria-labelledby="bulten-b">
  <div class="bulten__metin"><h2 id="bulten-b">Haber Bülteni</h2><p>Filistin’den günün öne çıkan haberleri her akşam e-postanızda.</p></div>
  <form class="bulten__form" action="#" novalidate>
    <label class="sr" for="bulten-eposta">E-posta adresi</label>
    <input id="bulten-eposta" type="email" autocomplete="email" placeholder="E-posta adresiniz" required>
    <button type="submit">Abone ol</button>
    <p class="bulten__durum" role="status" aria-live="polite"></p>
  </form>
</section>'''

def alt():
    sections = ''.join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in MENU)
    latest = sorted([x for x in ITEMS if x['date'] == TODAY], key=lambda x: x['time'] or '', reverse=True)[:4]
    son = ''.join(f'<li><span class="zaman">{saat(i["time"])}</span>{link(i, T(i["headline_tr"]))}</li>' for i in latest)
    soc = ''.join(f'<li><a href="#" aria-label="{t} — hesap yakında">{ic(n)}<span>{t}</span></a></li>' for n, t in [('x', 'X'), ('ig', 'Instagram'), ('tg', 'Telegram'), ('yt', 'YouTube')])
    kurum = ''.join(f'<li><a href="#">{e(x)}</a></li>' for x in ['Hakkımızda', 'Künye', 'İletişim', 'Reklam', 'Haber ihbarı'])
    yasal = ' '.join(f'<a href="#">{e(x)}</a>' for x in ['Gizlilik', 'Çerezler', 'Kullanım koşulları'])
    return f'''<footer class="alt">
  <div class="kap alt__ust">
    <div class="alt__marka">
      <a class="logo logo--alt" href="home.html" aria-label="Filistin Ajansı ana sayfa">{logo_ust()}</a>
      <p>Filistin’in, Batı Şeria’nın, Kudüs’ün ve Gazze’nin haberleri, Türkçe. Her haber yeri, saati ve kaynağıyla.</p>
      <ul class="alt__sosyal">{soc}</ul>
    </div>
    <nav class="alt__sutun" aria-label="Alt menü">
      <div><h3>Bölümler</h3><ul>{sections}</ul></div>
      <div><h3>Kurumsal</h3><ul>{kurum}</ul></div>
      <div class="alt__son"><h3>Son dakika</h3><ol>{son}</ol></div>
    </nav>
  </div>
  <div class="alt__alt"><div class="kap">
    <p>© 2026 Filistin Ajansı. Bu prototipteki haberler {date_tr(TODAY)} tarihli kamuya açık kaynaklardan derlendi; fotoğraflar Wikimedia Commons arşivindendir. Sosyal medya hesapları ve künye yakında.</p>
    <p class="alt__yasal">{yasal}</p>
    <a class="alt__yukari" href="#">Yukarı{ic("yukari")}</a>
  </div></div>
</footer>'''

def secici():
    """Shown only when the page is opened from the logo options page (?logo=N)."""
    b = ''.join(f'<button type="button" data-logo-sec="{k}">{k} · {e(v["name"])}</button>' for k, v in LOGOS.items())
    return f'<div class="secici" hidden><span>Logo seçeneği</span>{b}<a href="index.html">Tüm seçenekler</a></div>'

def build_home():
    tpl = open(P('tools', 'tpl', 'home.html'), encoding='utf-8').read()
    rep = {'V': V, 'UST': ust(), 'GUNDEM': gundem(), 'SICAK': sicak(), 'MANSET': manset(), 'ALTSIRA': alt_sira(),
           'BATI': bolum('bati-seria'), 'KUDUS': bolum('kudus'), 'GAZZE': bolum('gazze'), 'ESIRLER': esirler(),
           'RAKAMLAR': rakamlar(), 'GALERI': galeri(), 'BULTEN': bulten(), 'ALT': alt(), 'CEKMECE': cekmece(), 'SECICI': secici(),
           'TARIH': f'{date_tr(TODAY, weekday=True)}'}
    out = re.sub(r'\{\{(\w+)\}\}', lambda m: rep[m.group(1)], tpl)
    out = out.replace('<!doctype html>', '<!doctype html>\n<!-- generated by tools/build.py from tools/tpl/home.html — do not edit by hand -->', 1)
    open(P('home.html'), 'w', encoding='utf-8').write(out)
    return len(out)

# ---------- the Arabic logo options page ----------
SECENEK_AR = {
    '1': ('الوكالة', 'مربّع أحمر يحمل الحرفين FA بجانب الاسم، على طريقة وكالات الأنباء المعروفة في تركيا. شعار واضح وسريع القراءة، يعمل بالقوة نفسها في رأس الموقع وصورة الحساب وأيقونة المتصفح.'),
    '2': ('الزيتون', 'الاسم بأحرف صغيرة، والنقاط فوق حروف <span class="ltr">i</span> في كلمة <span class="ltr">filistin</span> صارت ثلاث ورقات زيتون كغصن صغير. الزيتون رمز الأرض الفلسطينية، وأخضره يرافق الأحمر في الهوية.'),
    '3': ('القبة', 'شارة على هيئة قبة الصخرة: القاعدة المثمّنة العريضة ثم الرقبة ثم القبة، والحرفان FA داخل القاعدة. القدس في قلب الشعار، قريبة من وجدان الجمهور التركي.'),
    '4': ('الكوفية', 'شارة سوداء بنقشة شبكة الكوفية والشريطين الأحمرين في أسفلها، عليها الحرفان FA، والاسم بأحرف كبيرة متباعدة. رمز فلسطيني يُعرف من النظرة الأولى.'),
}

def build_index():
    blocks = ''
    for k, v in LOGOS.items():
        ad, metin = SECENEK_AR[k]
        blocks += f'''<section class="secenek" id="secenek-{k}" aria-labelledby="secenek-{k}-b">
  <div class="secenek__bas"><span class="secenek__no">{k}</span><h2 id="secenek-{k}-b">{ad} <span class="ltr secenek__lat">{e(v["name"])}</span></h2></div>
  <p class="secenek__metin">{metin}</p>
  <div class="secenek__orn">
    <figure class="orn orn--beyaz"><div class="orn__alan"><img src="assets/brand/secenek-{k}.svg?v={V}" alt="الخيار {k} على خلفية بيضاء" width="{logo_w(v['renk'], 120)}" height="120"></div><figcaption>على خلفية بيضاء</figcaption></figure>
    <figure class="orn orn--ust"><div class="orn__ust"><img class="orn__foto" src="{LOCAL['p03']['src'].replace('1280', '640')}" alt="" loading="lazy"><span class="orn__baslik ltr" aria-hidden="true">Yerleşimciler Turmus Ayya’da zeytin toplayan Filistinlilere saldırdı</span><span class="orn__menu" aria-hidden="true"></span><span class="orn__logo"><img src="assets/brand/secenek-{k}-beyaz.svg?v={V}" alt="الخيار {k} في رأس الموقع" width="{logo_w(v['beyaz'], 26)}" height="26"></span><span class="orn__nav ltr" aria-hidden="true">BATI ŞERİA&nbsp;&nbsp;KUDÜS&nbsp;&nbsp;GAZZE</span></div><figcaption>في رأس الموقع</figcaption></figure>
    <figure class="orn orn--avatar"><div class="orn__ikili"><span class="orn__daire"><img src="assets/brand/secenek-{k}-avatar.svg?v={V}" alt="صورة الحساب للخيار {k}" width="120" height="120"></span><span class="orn__favicon"><img src="assets/brand/secenek-{k}-avatar.svg?v={V}" alt="" width="32" height="32"></span></div><figcaption>صورة الحساب وأيقونة المتصفح</figcaption></figure>
  </div>
  <div class="secenek__eylem"><a class="dugme" href="home.html?logo={k}">شاهده في الصفحة الرئيسية</a><a class="dugme dugme--cizgi" href="assets/brand/secenek-{k}.svg" download>تحميل الشعار <span class="ltr">SVG</span></a></div>
</section>'''
    tpl = open(P('tools', 'tpl', 'index.html'), encoding='utf-8').read()
    out = re.sub(r'\{\{(\w+)\}\}', lambda m: {'V': V, 'BLOKLAR': blocks}[m.group(1)], tpl)
    out = out.replace('<!doctype html>', '<!doctype html>\n<!-- generated by tools/build.py from tools/tpl/index.html — do not edit by hand -->', 1)
    open(P('index.html'), 'w', encoding='utf-8').write(out)
    return len(out)

if __name__ == '__main__':
    print('home.html', build_home(), 'bytes')
    print('index.html', build_index(), 'bytes')
