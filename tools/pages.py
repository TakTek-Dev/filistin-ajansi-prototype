"""Builds the whole Filistin Ajansı site: the homepage and logo options page (build.py) and every inner page.

python -I tools/pages.py   (from the project root; run tools/logos.py and tools/photos.py first)

haber/<slug>.html    a page for every story in research/news.json
bati-seria.html, kudus.html, gazze.html, esirler.html   section pages
son-dakika.html      every story, newest first, with a region filter
rakamlar.html        the dated numbers and their sources
galeri.html          every archive photo, with a viewer
arama.html           search over assets/data/haberler.json (written here)
bulten.html, hakkimizda.html, kunye.html, iletisim.html, gizlilik.html, 404.html
Never hand-edit the generated pages: edit this file, build.py, the templates or the data, then rebuild.
"""
import json, os, re, sys
from urllib.parse import quote, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as b
from build import e, T, tr_text, ic, date_tr, saat, zaman, first, etiket, BY_ID, ITEMS, PHOTO, LOCAL, TODAY

P = b.P
SITE_PATH = urlsplit(b.BASE_URL).path          # '/filistin-ajansi-prototype/' — 404.html needs absolute paths

b.ICON.update({
    'fb': '<path class="dolu" d="M13.5 21v-7.2h2.4l.4-2.9h-2.8V9.1c0-.8.2-1.4 1.4-1.4h1.5V5.1c-.3 0-1.1-.1-2.2-.1-2.2 0-3.6 1.3-3.6 3.8v2.1H8.2v2.9h2.4V21z"/>',
    'wa': '<path d="M4.5 19.5l1.2-3.6A7.8 7.8 0 1 1 8.6 18.6z"/><path class="dolu" d="M9.2 8.4c.2-.4.5-.4.8-.4h.5c.2 0 .4 0 .5.4l.7 1.6c.1.2 0 .4-.1.6l-.5.6c-.1.1-.2.3 0 .5.6 1.1 1.5 1.9 2.6 2.4.2.1.4.1.5-.1l.7-.8c.2-.2.3-.2.6-.1l1.6.8c.2.1.4.2.4.4 0 .5-.2 1.3-.9 1.7-.6.4-1.5.6-3.2-.1-2-.8-3.5-2.6-4-3.5-.5-.9-.6-2.4.4-3.9z"/>',
    'baglanti': '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    'paylas': '<circle cx="17" cy="5.5" r="2.5"/><circle cx="6.5" cy="12" r="2.5"/><circle cx="17" cy="18.5" r="2.5"/><path d="M8.7 10.8l6.1-3.9M8.7 13.2l6.1 3.9"/>',
    'dis': '<path d="M14 5h5v5M19 5l-8 8M17 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h4"/>',
})

# ---------- which photo each story carries ----------
# The homepage plan first (its photos were matched by hand), then photos found for the story itself, then an archive
# photo of the same place, governorate or region-wide area. A photo of a different named place is never borrowed.
PLAN = {}
for _i, _p in b.SLIDER + b.ALT_SIRA + [(x[1], x[2]) for x in b.SICAK] + [b.ESIR]:
    PLAN[_i] = b.photo_id(_p)
for _s in b.BOLUM.values():
    PLAN[_s['buyuk'][0]] = b.photo_id(_s['buyuk'][1])
    for _i, _p in _s['yan']:
        PLAN[_i] = b.photo_id(_p)
GENIS = {'Batı Şeria': 'batı-şeria', 'Kudüs': 'kudüs', 'Gazze Şeridi': 'gazze'}   # region-wide places and their region

def _foto_bul(it):
    iid = it['id']
    if iid in PLAN:
        return PLAN[iid]
    adaylar = [p for p in b.PH if iid in p.get('fits_items', []) and p['id'] in LOCAL]
    adaylar.sort(key=lambda p: -int(p['id'][1:]))                 # photos searched for this story come first
    yer, il = it.get('place_tr') or '', it.get('governorate_tr') or ''
    genis_haber = not yer or yer in GENIS
    for p in adaylar:
        py = p.get('place_tr', '')
        if int(p['id'][1:]) > 34 or py in (yer, il, il + ' ili') or genis_haber or GENIS.get(py) == it['region']:
            return p['id']
    return None

FOTO = {it['id']: _foto_bul(it) for it in ITEMS}

def foto_bir(iid, used):
    """On a listing page a photo shows once; a later story with the same photo is listed without it."""
    p = FOTO.get(iid)
    if p and p not in used:
        used.add(p)
        return p
    return None

def sirali(items):
    return sorted(items, key=lambda x: (x['date'], x['time'] or '00:00'), reverse=True)

TUMU = sirali(ITEMS)
def bolge_slug(it):
    return b.BOLGE[it['region']][0]
def bolge_ad(it):
    return b.BOLGE[it['region']][1]
def konu_slug(it):
    return b.ascii_tr(it['category'])

def abs_url(path):
    return b.BASE_URL + path

def iso(it):
    return f'{it["date"]}T{it["time"]}:00+03:00' if it['time'] else it['date']

def tam_zaman(it):
    return f'{date_tr(it["date"], weekday=True)}{", " + saat(it["time"]) if it["time"] else ""}'

def sentences(text):
    return [s for s in re.split(r'(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ“"‘])', text.strip()) if s]

# ---------- shared page parts ----------
def yaz(path, html_):
    full = P(*path.split('/'))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(html_)
    return len(html_)

TPL = open(P('tools', 'tpl', 'sayfa.html'), encoding='utf-8').read()

def sayfa(path, baslik, aciklama, icerik, aktif=None, govde='', og_img=None, jsonld='', ogtur='website', tam_baslik=None):
    og = f'<meta property="og:image" content="{e(abs_url(LOCAL[og_img]["src"]))}">\n' if og_img and og_img in LOCAL else ''
    rep = {'BASLIK': e(tam_baslik or f'{baslik} — Filistin Ajansı'), 'ACIKLAMA': e(aciklama), 'KANONIK': e(abs_url(path)),
           'OGTUR': ogtur, 'OGBASLIK': e(baslik), 'OGIMG': og, 'R': b.R, 'V': b.V, 'LOGOJS': b.LOGOJS, 'JSONLD': jsonld,
           'GOVDE': govde, 'TARIH': date_tr(TODAY, weekday=True), 'UST': b.ust(aktif), 'ICERIK': icerik, 'ALT': b.alt(),
           'CEKMECE': b.cekmece(aktif), 'SECICI': b.secici()}
    out = re.sub(r'\{\{(\w+)\}\}', lambda m: rep[m.group(1)], TPL)
    out = out.replace('<!doctype html>', '<!doctype html>\n<!-- generated by tools/pages.py — do not edit by hand -->', 1)
    return yaz(path, out)

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>\n'

def iz(parcalar):
    """Breadcrumb: (label, href) pairs, the last one is the current page."""
    lis = ''.join(f'<li><a href="{b.yol(h)}">{e(t)}</a></li>' if h else f'<li><span aria-current="page">{e(t)}</span></li>' for t, h in parcalar)
    return f'<nav class="iz" aria-label="Sayfa yolu"><ol>{lis}</ol></nav>'

def iz_ld(parcalar, path):
    return ld({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': k + 1, 'name': t, 'item': abs_url(h or path)} for k, (t, h) in enumerate(parcalar)]})

def sayfa_basi(ad, not_=None, hid='sayfa-b'):
    n = f'<p class="sayfa-bas__not">{not_}</p>' if not_ else ''
    return f'<header class="sayfa-bas"><div class="sayfa-bas__satir"><h1 id="{hid}">{e(ad)}</h1><span class="bolum__cizgi" aria-hidden="true"></span></div>{n}</header>'

def ara_baslik(ad, hid, sag=''):
    return f'<div class="bolum__bas"><h2 id="{hid}">{e(ad)}</h2><span class="bolum__cizgi" aria-hidden="true"></span>{sag}</div>'

def son_kutu(n=8, haric=None):
    rows = [x for x in TUMU if x['id'] != haric][:n]
    lis = ''.join(f'<li><span class="zaman">{zaman(i)}</span>{b.link(i, T(i["headline_tr"]))}</li>' for i in rows)
    return (f'<section class="kutu" aria-labelledby="kutu-son"><h2 class="kutu__ad" id="kutu-son"><span class="son__nokta" aria-hidden="true"></span>Son Dakika</h2>'
            f'<ol class="kutu__liste">{lis}</ol><a class="kutu__tum" href="{b.yol("son-dakika.html")}">Tüm haberler{ic("sag")}</a></section>')

def bulten_kutu():
    return (f'<section class="kutu kutu--bulten" aria-labelledby="kutu-bulten"><h2 class="kutu__ad" id="kutu-bulten">Haber Bülteni</h2>'
            f'<p>Filistin’den günün öne çıkan haberleri her akşam e-postanızda.</p><a class="dugme" href="{b.yol("bulten.html")}">Abone ol</a></section>')

def akis_satir(it, used, saat_only=False):
    """One row of a news stream (Son Dakika, search): time, thumbnail when the story has its own photo, tag, headline, first sentence."""
    pid = foto_bir(it['id'], used)
    thumb = f'<span class="akis__foto">{b.img(pid, "(min-width: 760px) 176px, 112px")}</span>' if pid else ''
    t = saat(it['time']) if saat_only else zaman(it)
    return (f'<li class="akis__oge{"" if pid else " akis__oge--metin"}" data-bolge="{bolge_slug(it)}">'
            f'<time class="akis__saat" datetime="{iso(it)}">{t or "—"}</time>'
            f'<a class="akis__bag" href="{b.yol(b.haber_url(it["id"]))}">{thumb}<span class="akis__metin">'
            f'<span class="etiket">{e(etiket(it))}</span><span class="akis__baslik">{T(it["headline_tr"])}</span>'
            f'<span class="akis__ozet">{T(first(it["summary_tr"]))}</span></span></a></li>')

def rakam_li(n, link_item=True):
    src = n.get('source_url')
    kaynak = (f'<a href="{e(src)}" target="_blank" rel="noopener">{e(n["source_name"])}</a>' if src else e(n['source_name']))
    haber = (f'<a class="sayi__haber" href="{b.yol(b.haber_url(n["item_id"]))}">Haberi oku{ic("sag")}</a>' if link_item and n.get('item_id') else '')
    return (f'<li class="sayi"><b class="sayi__deger">{e(n["value"])}</b><span class="sayi__birim">{e(n["unit_tr"])}</span>'
            f'<span class="sayi__ne">{T(n["label_tr"])}</span><small class="sayi__kaynak">{date_tr(n["as_of"])} · Kaynak: {kaynak}</small>{haber}</li>')

# ---------- story pages ----------
def paylas(it):
    url = quote(abs_url(b.haber_url(it['id'])), safe='')
    txt = quote(tr_text(it['headline_tr']), safe='')
    links = [('x', 'X’te paylaş', f'https://x.com/intent/post?text={txt}&url={url}'),
             ('fb', 'Facebook’ta paylaş', f'https://www.facebook.com/sharer/sharer.php?u={url}'),
             ('wa', 'WhatsApp’ta paylaş', f'https://wa.me/?text={txt}%20{url}'),
             ('tg', 'Telegram’da paylaş', f'https://t.me/share/url?url={url}&text={txt}')]
    a = ''.join(f'<a class="paylas__dugme paylas__dugme--{k}" href="{h}" target="_blank" rel="noopener" aria-label="{t}">{ic(k)}</a>' for k, t, h in links)
    return (f'<div class="paylas" role="group" aria-label="Paylaş">{a}'
            f'<button class="paylas__dugme" type="button" data-kopyala aria-label="Bağlantıyı kopyala">{ic("baglanti")}</button>'
            f'<button class="paylas__dugme" type="button" data-paylas hidden aria-label="Paylaş">{ic("paylas")}</button>'
            f'<span class="paylas__durum" role="status" aria-live="polite"></span></div>')

def haber_sayfasi(it, onceki, sonraki):
    iid = it['id']
    sec, sec_ad = bolge_slug(it), bolge_ad(it)
    sec_href = 'son-dakika.html' if sec == 'dunya' else f'{sec}.html'
    yer = it.get('place_tr') or sec_ad
    parcalar = [('Ana Sayfa', 'home.html'), (sec_ad if sec != 'dunya' else 'Son Dakika', sec_href), (tr_text(it['headline_tr']), None)]
    s = sentences(it['summary_tr'])
    spot, govde = s[0], s[1:]
    pid = FOTO[iid]
    if pid:
        ph = PHOTO[pid]
        medya = (f'<figure class="haber__foto"><div class="haber__resim">{b.img(pid, "(min-width: 1000px) 820px, 100vw", eager=True)}'
                 f'<span class="arsiv">Arşiv</span></div><figcaption>{T(ph.get("caption_tr", ""))} <span class="haber__kredi">'
                 f'Fotoğraf: <a href="{e(ph["commons_page"])}" target="_blank" rel="noopener">{e(ph.get("author", ""))}</a> · {e(ph.get("license", ""))} · Wikimedia Commons</span></figcaption></figure>')
    else:
        medya = (f'<div class="haber__levha" aria-hidden="true"><span class="etiket">{e(etiket(it))}</span>'
                 f'<b>{e(re.sub(r"\s*\(.*?\)", "", yer))}</b><span>{e(it.get("governorate_tr") or sec_ad)} · {date_tr(it["date"])}</span></div>')
    metin = ''.join(f'<p>{T(x)}</p>' for x in govde)
    rakam = ''
    if it['numbers']:
        rakam = f'<aside class="haber__rakam" aria-labelledby="rakam-{iid}"><h2 id="rakam-{iid}">Rakamlarla</h2><ul>{"".join(rakam_li(n, False) for n in it["numbers"])}</ul></aside>'
    ek = ''
    if it.get('related_urls'):
        ek = '<p class="haber__ek">Ek kaynaklar: ' + ', '.join(
            f'<a href="{e(u)}" target="_blank" rel="noopener">{e(urlsplit(u).netloc.replace("www.", ""))} ({k + 1})</a>' for k, u in enumerate(it['related_urls'])) + '</p>'
    kaynak = (f'<div class="haber__kaynak"><h2>Kaynak</h2><p>Bu haber, {e(it["source_name"])} tarafından {date_tr(it["date"])} tarihinde yayımlanan bilgilere dayanır.</p>'
              f'<a class="haber__kaynak-bag" href="{e(it["source_url"])}" target="_blank" rel="noopener">Haberin kaynağına git{ic("dis")}</a>{ek}</div>')
    yer_q = re.sub(r'\s*\(.*?\)', '', yer)
    etiketler = [(f'#{yer_q}', f'arama.html?q={quote(yer_q)}')]
    if it.get('governorate_tr') and it['governorate_tr'] != yer_q:
        etiketler.append((it['governorate_tr'], f'arama.html?q={quote(it["governorate_tr"])}'))
    etiketler.append((b.KONU[it['category']], f'arama.html?konu={konu_slug(it)}'))
    if sec != 'dunya' and sec_ad != yer_q:
        etiketler.append((sec_ad, sec_href))
    tags = ''.join(f'<li><a href="{b.yol(h)}">{e(t)}</a></li>' for t, h in etiketler)
    gecis = ''
    for cls, lab, x in (('onceki', 'Önceki haber', onceki), ('sonraki', 'Sonraki haber', sonraki)):
        if x:
            gecis += f'<a class="gecis__bag gecis__bag--{cls}" href="{b.yol(b.haber_url(x["id"]))}"><span>{lab}</span><b>{T(x["headline_tr"])}</b></a>'
    # related: same region first, nearest in time; then the latest elsewhere
    ayni = [x for x in TUMU if x['region'] == it['region'] and x['id'] != iid]
    ayni.sort(key=lambda x: abs(TUMU.index(x) - TUMU.index(it)))
    diger = [x for x in TUMU if x['region'] != it['region']]
    used = {pid} if pid else set()
    ilgili_ids = []
    for x in ayni + diger:
        if len(ilgili_ids) == 4:
            break
        if FOTO[x['id']] and FOTO[x['id']] not in used:
            used.add(FOTO[x['id']])
            ilgili_ids.append(x['id'])
    ilgili = ''.join(b.kart(x, FOTO[x]) for x in ilgili_ids)
    yazi = ('<div class="yazi" role="group" aria-label="Yazı boyutu"><button type="button" data-yazi="-1" aria-label="Yazıyı küçült">A−</button>'
            '<button type="button" data-yazi="1" aria-label="Yazıyı büyüt">A+</button></div>')
    icerik = f'''<div class="okuma" aria-hidden="true"><i></i></div>
<main id="icerik" class="kap sayfa">
  {iz(parcalar)}
  <div class="haber-izgara">
    <article class="haber" data-haber>
      <header class="haber__bas">
        <a class="haber__konu" href="{b.yol(f"arama.html?konu={konu_slug(it)}")}">{e(b.KONU[it["category"]])}</a>
        <h1>{T(it["headline_tr"])}</h1>
        <p class="haber__spot">{T(spot)}</p>
        <div class="haber__kunye">
          <p class="haber__meta"><span class="etiket">{e(etiket(it))}</span><span>Filistin Ajansı</span><time datetime="{iso(it)}">{tam_zaman(it)}</time></p>
          <div class="haber__arac">{yazi}{paylas(it)}</div>
        </div>
      </header>
      {medya}
      <div class="haber__metin">{metin}</div>
      {rakam}
      {kaynak}
      <ul class="haber__etiketler" aria-label="Etiketler">{tags}</ul>
      <nav class="gecis" aria-label="Diğer haberler">{gecis}</nav>
    </article>
    <aside class="haber-yan">{son_kutu(8, iid)}{bulten_kutu()}</aside>
  </div>
  <section class="bolum ilgili" aria-labelledby="ilgili-b">{ara_baslik("İlgili haberler", "ilgili-b")}<div class="sira4">{ilgili}</div></section>
</main>'''
    path = b.haber_url(iid)
    art = {'@context': 'https://schema.org', '@type': 'NewsArticle', 'headline': tr_text(it['headline_tr']), 'description': tr_text(spot),
           'datePublished': iso(it), 'dateModified': iso(it), 'inLanguage': 'tr', 'articleSection': sec_ad,
           'mainEntityOfPage': abs_url(path), 'isBasedOn': it['source_url'],
           'author': {'@type': 'Organization', 'name': 'Filistin Ajansı', 'url': abs_url('hakkimizda.html')},
           'publisher': {'@type': 'Organization', 'name': 'Filistin Ajansı', 'logo': {'@type': 'ImageObject', 'url': abs_url('assets/brand/secenek-1.svg')}}}
    if pid:
        art['image'] = [abs_url(LOCAL[pid]['src'])]
    if it.get('lat') and it.get('place_tr'):
        art['contentLocation'] = {'@type': 'Place', 'name': yer_q, 'geo': {'@type': 'GeoCoordinates', 'latitude': it['lat'], 'longitude': it['lon']}}
    return sayfa(path, tr_text(it['headline_tr']), tr_text(spot), icerik, aktif=sec_href if sec != 'dunya' else 'son-dakika.html',
                 govde='g-haber', og_img=pid, jsonld=ld(art) + iz_ld(parcalar, path), ogtur='article')

# ---------- section pages ----------
BOLUM_SAYFA = {
    'bati-seria': ('batı-şeria', 'Batı Şeria’dan son dakika haberleri: yerleşimci saldırıları, baskınlar, gözaltılar, kapılar ve zeytin hasadı.'),
    'kudus': ('kudüs', 'Kudüs’ten haberler: Mescid-i Aksa, yıkımlar ve Doğu Kudüs mahalleleri.'),
    'gazze': ('gazze', 'Gazze’den haberler: ateşkes, saldırılar ve insani durum.'),
    'esirler': ('esirler', 'İsrail hapishanelerindeki Filistinli esirlerle ilgili haberler ve güncel rakamlar.'),
}
LEAD = {'bati-seria': b.BOLUM['bati-seria']['buyuk'][0], 'kudus': b.BOLUM['kudus']['buyuk'][0], 'gazze': b.BOLUM['gazze']['buyuk'][0], 'esirler': b.ESIR[0]}

def bolum_rakam(bolge):
    """The section's dated numbers: the edition's headline numbers first, then numbers from the section's own stories."""
    out, seen = [], set()
    for n in b.NEWS['headline_numbers']:
        if BY_ID[n['item_id']]['region'] == bolge and n['value'] not in seen:
            out.append(n); seen.add(n['value'])
    for it in sirali([x for x in ITEMS if x['region'] == bolge]):
        for n in it['numbers']:
            if len(out) >= 4:
                break
            if n['value'] not in seen and len(n['value']) > 1 and n['unit_tr'] not in SAYI_DEGIL:
                out.append(dict(n, source_url=it['source_url'], item_id=it['id'])); seen.add(n['value'])
    return out[:4]
SAYI_DEGIL = {'karar no.', 'yıl', 'yaş'}      # identifiers and ages are facts in a story, not section statistics

def bolum_sayfasi(sid):
    """Lead story beside three photo cards and a headline list; the rest in rows of four.
    The side list takes as many stories as it needs so the grid below always ends on a full row."""
    bolge, aciklama = BOLUM_SAYFA[sid]
    ad = b.BOLGE[bolge][1]
    items = sirali([x for x in ITEMS if x['region'] == bolge])
    lead = BY_ID[LEAD[sid]]
    rest = [x for x in items if x['id'] != lead['id']]
    used = set()
    lead_p = foto_bir(lead['id'], used)
    side = []
    for x in rest:
        if len(side) == 3:
            break
        if FOTO[x['id']] and FOTO[x['id']] not in used:
            used.add(FOTO[x['id']]); side.append((x['id'], FOTO[x['id']]))
    rest = [x for x in rest if x['id'] not in {i for i, _ in side}]
    n_liste = len(rest) if len(rest) < 7 else 3 + (len(rest) - 3) % 4
    liste, rest = rest[:n_liste], rest[n_liste:]
    yan = ''.join(b.kart(i, p, 'kucuk') for i, p in side)
    if liste:
        yl = b.yan_liste([x['id'] for x in liste], f'{ad}’dan diğer başlıklar' if sid == 'bati-seria' else 'Diğer başlıklar', ozet=len(liste) <= 4)
        # one or two headlines would float in a stretched box: keep them at their height and let Son Dakika fill the column
        yan += yl.replace('class="yan-liste"', 'class="yan-liste yan-liste--kisa"', 1) + son_kutu(4) if len(liste) <= 2 else yl
    else:
        yan += son_kutu(4)
    ust = (f'<div class="bolum__ust"><div class="bolum__buyuk">{b.kart(lead["id"], lead_p, "buyuk", ozet=True)}</div>'
           f'<div class="bolum__yan">{yan}</div></div>')
    kartlar = ''
    for x in rest:
        p = foto_bir(x['id'], used)
        kartlar += b.kart(x['id'], p, ozet=not p)
    grid = (f'<section class="bolum" aria-labelledby="{sid}-tum">{ara_baslik(f"{ad} haberleri", f"{sid}-tum")}<div class="izgara">{kartlar}</div></section>'
            if kartlar else '')
    sayilar = bolum_rakam(bolge)
    rakam = (f'<section class="bolum-rakam" aria-labelledby="{sid}-rakam"><h2 id="{sid}-rakam">{e(ad)} rakamlarla</h2>'
             f'<ul>{"".join(rakam_li(n) for n in sayilar)}</ul><a class="bolum-rakam__tum" href="{b.yol("rakamlar.html")}">Tüm rakamlar{ic("sag")}</a></section>') if sayilar else ''
    il_seridi = ''
    if sid == 'bati-seria':
        iller = {}
        for x in items:
            if x.get('governorate_tr'):
                iller[x['governorate_tr']] = iller.get(x['governorate_tr'], 0) + 1
        il_seridi = ('<nav class="cipler" aria-label="İllere göre"><span class="cipler__ad">İller</span>' +
                     ''.join(f'<a class="cip" href="{b.yol(f"arama.html?bolge=bati-seria&q={quote(k)}")}">{e(k)} <span>{v}</span></a>'
                             for k, v in sorted(iller.items(), key=lambda kv: (-kv[1], kv[0]))) + '</nav>')
    diger = [x for x in TUMU if x['region'] != bolge and FOTO[x['id']] and FOTO[x['id']] not in used][:4]
    diger_html = ''.join(b.kart(x['id'], FOTO[x['id']]) for x in diger)
    gunler = sorted({x['date'] for x in items})
    not_ = f'{len(items)} haber · {date_tr(gunler[0], year=False)}–{date_tr(gunler[-1])}' if len(gunler) > 1 else f'{len(items)} haber · {date_tr(gunler[0])}'
    parcalar = [('Ana Sayfa', 'home.html'), (ad, None)]
    icerik = f'''<main id="icerik" class="kap sayfa">
  {iz(parcalar)}
  {sayfa_basi(ad, not_)}
  {il_seridi}
  {ust}
  {rakam}
  {grid}
  <section class="bolum" aria-labelledby="{sid}-diger">{ara_baslik("Diğer bölümlerden", f"{sid}-diger")}<div class="sira4">{diger_html}</div></section>
</main>'''
    return sayfa(f'{sid}.html', f'{ad} Haberleri', aciklama, icerik, aktif=f'{sid}.html', govde='g-bolum', og_img=lead_p,
                 jsonld=iz_ld(parcalar, f'{sid}.html'))

# ---------- Son Dakika: every story ----------
def son_dakika():
    used = set()
    gunler = sorted({x['date'] for x in TUMU}, reverse=True)
    gruplar = ''
    for d in gunler:
        rows = ''.join(akis_satir(x, used, saat_only=True) for x in TUMU if x['date'] == d)
        gruplar += f'<section class="gun" aria-labelledby="gun-{d}"><h2 class="gun__ad" id="gun-{d}">{date_tr(d, weekday=True)}</h2><ol class="akis">{rows}</ol></section>'
    sayim = {}
    for x in TUMU:
        sayim[bolge_slug(x)] = sayim.get(bolge_slug(x), 0) + 1
    cips = f'<button class="cip" type="button" data-bolge="" aria-pressed="true">Tümü <span>{len(TUMU)}</span></button>' + ''.join(
        f'<button class="cip" type="button" data-bolge="{s}" aria-pressed="false">{e(a)} <span>{sayim.get(s, 0)}</span></button>'
        for k, (s, a) in b.BOLGE.items() if sayim.get(s))
    parcalar = [('Ana Sayfa', 'home.html'), ('Son Dakika', None)]
    icerik = f'''<main id="icerik" class="kap sayfa sayfa--dar">
  {iz(parcalar)}
  {sayfa_basi("Son Dakika", f"Filistin’den bütün haberler, en yeniden eskiye · {len(TUMU)} haber · Son güncelleme {date_tr(TODAY)}, {b.EDITION_TIME}")}
  <div class="cipler" role="group" aria-label="Bölgeye göre süz" data-suz>{cips}</div>
  <p class="suz__durum sr" role="status" aria-live="polite"></p>
  <div data-suz-alan>{gruplar}</div>
</main>'''
    return sayfa('son-dakika.html', 'Son Dakika Haberleri', 'Filistin’den son dakika haberleri: Batı Şeria, Kudüs, Gazze ve esirler, en yeniden eskiye.',
                 icerik, aktif='son-dakika.html', govde='g-akis', jsonld=iz_ld(parcalar, 'son-dakika.html'))

# ---------- Rakamlar ----------
def rakamlar():
    bas = ''.join(rakam_li(n) for n in b.NEWS['headline_numbers'])
    bloklar = ''
    for it in [x for x in TUMU if x['kind'] == 'rakam']:
        lis = ''.join(rakam_li(n, False) for n in it['numbers'])
        bloklar += (f'<article class="rakam-haber"><h3>{b.link(it, T(it["headline_tr"]))}</h3><p class="rakam-haber__alt"><span class="etiket">{e(etiket(it))}</span>'
                    f'<span class="zaman">{zaman(it)}</span></p><ul>{lis}</ul></article>')
    parcalar = [('Ana Sayfa', 'home.html'), ('Rakamlar', None)]
    icerik = f'''<main id="icerik" class="kap sayfa">
  {iz(parcalar)}
  {sayfa_basi("Rakamlarla Filistin", "Her rakam, geçerli olduğu tarih ve kaynağıyla. Kaynak adına tıklayınca rakamın yayımlandığı sayfa açılır.")}
  <ul class="sayilar">{bas}</ul>
  <section class="bolum" aria-labelledby="rakam-haberler">{ara_baslik("Haberlerdeki rakamlar", "rakam-haberler")}<div class="rakam-haberler">{bloklar}</div></section>
</main>'''
    return sayfa('rakamlar.html', 'Rakamlarla Filistin', 'Filistin’den güncel rakamlar: esirler, Gazze’deki can kaybı, Batı Şeria’daki kontrol noktaları ve yerleşimci saldırıları, kaynaklarıyla.',
                 icerik, aktif='rakamlar.html', govde='g-rakam', jsonld=iz_ld(parcalar, 'rakamlar.html'))

# ---------- Foto Galeri ----------
def galeri():
    hikaye = {}
    for iid, pid in FOTO.items():
        if pid and pid not in hikaye:
            hikaye[pid] = iid
    figs = ''
    ids = [p['id'] for p in b.PH if p['id'] in LOCAL]
    for k, pid in enumerate(ids):
        p = PHOTO[pid]
        big = LOCAL[pid]['src']
        oku = f'<a class="foto__haber" href="{b.yol(b.haber_url(hikaye[pid]))}">Fotoğrafın kullanıldığı haber{ic("sag")}</a>' if pid in hikaye else ''
        figs += (f'<li class="foto"><figure><button class="foto__ac" type="button" data-isik="{k}" data-buyuk="{b.yol(big)}" aria-label="Büyüt: {e(p.get("place_tr", ""))}">'
                 f'{b.img(pid, "(min-width: 1000px) 400px, (min-width: 640px) 45vw, 100vw")}</button>'
                 f'<figcaption><b>{e(p.get("place_tr", ""))}</b><span class="foto__metin">{T(p.get("caption_tr", ""))}</span>'
                 f'<span class="foto__kredi"><a href="{e(p["commons_page"])}" target="_blank" rel="noopener">{e(p.get("author", ""))}</a> · {e(p.get("license", ""))}</span>{oku}</figcaption></figure></li>')
    isik = f'''<dialog class="isik" aria-label="Fotoğraf görüntüleyici" data-isik-kutu>
  <div class="isik__ust"><span class="isik__sayac" aria-live="polite"></span><button type="button" class="isik__dugme" data-isik-kapat aria-label="Kapat">{ic("kapat")}</button></div>
  <div class="isik__sahne"><button type="button" class="isik__dugme isik__ok isik__ok--sol" data-isik-geri aria-label="Önceki fotoğraf">{ic("sol")}</button>
    <img class="isik__resim" alt=""><button type="button" class="isik__dugme isik__ok isik__ok--sag" data-isik-ileri aria-label="Sonraki fotoğraf">{ic("sag")}</button></div>
  <div class="isik__alt"></div>
</dialog>'''
    parcalar = [('Ana Sayfa', 'home.html'), ('Foto Galeri', None)]
    icerik = f'''<main id="icerik" class="kap sayfa">
  {iz(parcalar)}
  {sayfa_basi("Foto Galeri", f"{len(ids)} arşiv karesi. Olay anında çekilmediler; her karede çeken kişi, yıl ve lisans yazılı. Büyütmek için fotoğrafa tıklayın.")}
  <ul class="fotolar" data-galeri-izgara>{figs}</ul>
  {isik}
</main>'''
    return sayfa('galeri.html', 'Foto Galeri', 'Filistin’den arşiv fotoğrafları: Kudüs, Batı Şeria ve Gazze, çekenin adı ve lisansıyla.',
                 icerik, aktif='galeri.html', govde='g-galeri', og_img='p20', jsonld=iz_ld(parcalar, 'galeri.html'))

# ---------- search ----------
def arama_verisi():
    rows = []
    for it in TUMU:
        pid = FOTO[it['id']]
        rows.append({'u': b.haber_url(it['id']), 'b': tr_text(it['headline_tr']), 'o': tr_text(first(it['summary_tr'])),
                     'm': tr_text(it['summary_tr']), 'y': etiket(it), 'p': it.get('place_tr') or '', 'il': it.get('governorate_tr') or '',
                     'r': bolge_slug(it), 'k': konu_slug(it), 'ka': b.KONU[it['category']], 'z': zaman(it), 'd': it['date'], 's': it['time'] or '',
                     'f': LOCAL[pid]['srcset'].split(',')[-1].strip().split(' ')[0] if pid else None})
    os.makedirs(P('assets', 'data'), exist_ok=True)
    json.dump(rows, open(P('assets', 'data', 'haberler.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return len(rows)

def arama():
    cips = f'<button class="cip" type="button" data-bolge="" aria-pressed="true">Tümü</button>' + ''.join(
        f'<button class="cip" type="button" data-bolge="{s}" aria-pressed="false">{e(a)}</button>' for k, (s, a) in b.BOLGE.items())
    oneri = ''.join(f'<a class="cip" href="arama.html?q={quote(q)}">{e(q)}</a>' for q in ['Zeytin', 'Mescid-i Aksa', 'Nablus', 'Cenin', 'El Halil', 'Gazze', 'Esirler', 'Yıkım'])
    konular = ''.join(f'<a class="cip" href="arama.html?konu={b.ascii_tr(k)}">{e(v)}</a>' for k, v in b.KONU.items())
    parcalar = [('Ana Sayfa', 'home.html'), ('Arama', None)]
    icerik = f'''<main id="icerik" class="kap sayfa sayfa--dar">
  {iz(parcalar)}
  {sayfa_basi("Haberlerde ara")}
  <form class="ara" action="arama.html" method="get" role="search" data-ara>
    <label class="sr" for="ara-q">Aranacak kelime</label>
    <input id="ara-q" name="q" type="search" placeholder="Yer, kişi ya da konu: Tekua, zeytin, Mescid-i Aksa…" autocomplete="off" enterkeyhint="search">
    <button type="submit">{ic("ara")}<span>Ara</span></button>
  </form>
  <div class="cipler" role="group" aria-label="Bölgeye göre süz" data-ara-bolge>{cips}</div>
  <div class="ara__filtre" data-ara-filtre hidden></div>
  <p class="ara__durum" role="status" aria-live="polite" data-ara-durum>Haberler yükleniyor…</p>
  <ol class="akis" data-ara-sonuc></ol>
  <noscript><p class="ara__durum">Arama için JavaScript gerekir. Bütün haberler <a href="son-dakika.html">Son Dakika</a> sayfasında.</p></noscript>
  <section class="ara__oneri" aria-labelledby="oneri-b" data-ara-oneri>
    <h2 id="oneri-b">Sık arananlar</h2><div class="cipler">{oneri}</div>
    <h2>Konular</h2><div class="cipler">{konular}</div>
  </section>
</main>'''
    return sayfa('arama.html', 'Arama', 'Filistin Ajansı haberlerinde arayın: yer, kişi ya da konu.', icerik, aktif='arama.html', govde='g-ara',
                 jsonld=iz_ld(parcalar, 'arama.html'))

# ---------- newsletter, corporate and legal pages ----------
def form_bulten(fid):
    return f'''<form class="bulten__form" action="#" novalidate>
    <label class="sr" for="{fid}">E-posta adresi</label>
    <input id="{fid}" type="email" autocomplete="email" placeholder="E-posta adresiniz" required>
    <button type="submit">Abone ol</button>
    <p class="bulten__durum" role="status" aria-live="polite"></p>
  </form>'''

def bulten():
    bes = [BY_ID[i] for i, _ in b.SLIDER[:5]]
    ornek = ''.join(f'<li><span class="etiket">{e(etiket(x))}</span>{b.link(x, T(x["headline_tr"]))}</li>' for x in bes)
    parcalar = [('Ana Sayfa', 'home.html'), ('Haber Bülteni', None)]
    icerik = f'''<main id="icerik" class="kap sayfa sayfa--dar">
  {iz(parcalar)}
  {sayfa_basi("Haber Bülteni", "Filistin’den günün öne çıkan haberleri her akşam e-postanızda.")}
  <section class="bulten bulten--sayfa" aria-label="Abonelik">
    <div class="bulten__metin"><h2>Ücretsiz abone olun</h2><p>E-posta adresinizi yazın; ilk bülten aynı akşam gelir.</p></div>
    {form_bulten("bulten-sayfa-eposta")}
  </section>
  <section class="metin" aria-labelledby="neler-b">
    <h2 id="neler-b">Bültende neler var?</h2>
    <ul class="madde">
      <li><b>Günün beş haberi.</b> Batı Şeria, Kudüs ve Gazze’den en önemli gelişmeler, birer cümlelik özetle.</li>
      <li><b>Günün rakamı.</b> Tarihi ve kaynağıyla tek bir rakam.</li>
      <li><b>Haftanın özeti.</b> Cumartesi akşamları, haftanın öne çıkan haberleri bir arada.</li>
    </ul>
  </section>
  <section class="ornek" aria-labelledby="ornek-b">
    <p class="ornek__ust">Örnek bülten · {date_tr(TODAY, weekday=True)}</p>
    <h2 id="ornek-b">Günün beş haberi</h2>
    <ol>{ornek}</ol>
    <p class="ornek__rakam"><b>9.400</b> Filistinli İsrail hapishanelerinde. <small>14 Ekim, Filistinli Esirler Kulübü</small></p>
  </section>
  <p class="not">İstediğiniz zaman bültenin altındaki bağlantıyla abonelikten çıkabilirsiniz. Bu prototip e-posta göndermez; bülten canlı sitede açılacak.</p>
</main>'''
    return sayfa('bulten.html', 'Haber Bülteni', 'Filistin’den günün öne çıkan haberleri her akşam e-postanızda. Ücretsiz abone olun.',
                 icerik, aktif='bulten.html', govde='g-metin', jsonld=iz_ld(parcalar, 'bulten.html'))

def metin_sayfa(path, baslik, aciklama, govde, giris=None):
    nav = ''.join(f'<li><a href="{b.yol(h)}"{" aria-current=page" if h == path else ""}>{e(t)}</a></li>'
                  for h, t in [('hakkimizda.html', 'Hakkımızda'), ('kunye.html', 'Künye'), ('iletisim.html', 'İletişim'), ('gizlilik.html', 'Gizlilik ve kullanım'), ('bulten.html', 'Haber Bülteni')])
    parcalar = [('Ana Sayfa', 'home.html'), (baslik, None)]
    icerik = f'''<main id="icerik" class="kap sayfa">
  {iz(parcalar)}
  <div class="metin-izgara">
    <div class="metin">{sayfa_basi(baslik, giris)}{govde}</div>
    <nav class="metin-nav" aria-label="Kurumsal"><h2>Kurumsal</h2><ul>{nav}</ul></nav>
  </div>
</main>'''
    return sayfa(path, baslik, aciklama, icerik, govde='g-metin', jsonld=iz_ld(parcalar, path))

def hakkimizda():
    bolumler = ''.join(f'<li><a href="{b.yol(h)}"><b>{e(t)}</b></a> {d}</li>' for h, t, d in [
        ('bati-seria.html', 'Batı Şeria', 'Yerleşimci saldırıları, baskınlar, gözaltılar, kapılar ve zeytin hasadı.'),
        ('kudus.html', 'Kudüs', 'Mescid-i Aksa, yıkımlar ve Doğu Kudüs mahalleleri.'),
        ('gazze.html', 'Gazze', 'Ateşkes, saldırılar ve insani durum.'),
        ('esirler.html', 'Esirler', 'İsrail hapishanelerindeki Filistinliler ve güncel rakamlar.'),
        ('rakamlar.html', 'Rakamlar', 'Tarihi ve kaynağıyla bütün rakamlar.'),
        ('son-dakika.html', 'Son Dakika', 'Bütün haberler, en yeniden eskiye.')])
    govde = f'''<p class="metin__giris">Filistin Ajansı, Filistin’den, Batı Şeria’dan, Kudüs’ten ve Gazze’den haberleri Türkçe okuyucuya ulaştıran bir haber sitesidir.</p>
<p>Bölgedeki yerel kaynakları, resmî kurumların açıklamalarını ve uluslararası kuruluşların raporlarını her gün izliyor; doğruladığımız haberleri sade bir Türkçeyle yayımlıyoruz.</p>
<h2>İlkelerimiz</h2>
<ul class="madde">
  <li><b>Yer, tarih ve saat.</b> Olayın nerede ve ne zaman yaşandığı her haberin başında yazar.</li>
  <li><b>Kaynak.</b> Bilginin kimden geldiğini haberin sonunda belirtir, kaynağın bağlantısını veririz.</li>
  <li><b>Arşiv fotoğrafı etiketlidir.</b> Olay anında çekilmemiş her fotoğrafın üzerinde «Arşiv» yazar; çeken kişi ve lisans fotoğrafın altındadır. Haberin yerine ait bir fotoğraf yoksa başka bir yerin fotoğrafını kullanmayız.</li>
  <li><b>Rakamlar tarihlidir.</b> Her rakamın hangi tarihe kadar geçerli olduğunu ve kaynağını yazarız.</li>
  <li><b>Hata yaparsak düzeltiriz.</b> Düzeltme taleplerinizi <a href="{b.yol("iletisim.html#duzeltme")}">İletişim</a> sayfasından iletebilirsiniz.</li>
</ul>
<h2>Bölümlerimiz</h2>
<ul class="madde madde--bolum">{bolumler}</ul>
<p class="not">Bu site bir prototiptir. Haberler {date_tr(TODAY)} tarihli kamuya açık kaynaklardan derlendi; fotoğraflar Wikimedia Commons arşivindendir.</p>'''
    return metin_sayfa('hakkimizda.html', 'Hakkımızda', 'Filistin Ajansı: Filistin’den, Batı Şeria’dan, Kudüs’ten ve Gazze’den haberler, Türkçe. Yayın ilkelerimiz.', govde)

def kunye():
    roller = ['Genel Yayın Yönetmeni', 'Sorumlu Yazı İşleri Müdürü', 'Haber Müdürü', 'Kudüs Muhabiri', 'Batı Şeria Muhabiri',
              'Gazze Muhabiri', 'Çeviri ve Editörlük', 'Fotoğraf Editörü', 'Teknik Sorumlu']
    satirlar = ''.join(f'<tr><th scope="row">{e(r)}</th><td>Yayın öncesi eklenecek</td></tr>' for r in roller)
    govde = f'''<table class="kunye"><caption class="sr">Yayın kadrosu</caption><tbody><tr><th scope="row">Yayıncı</th><td>Filistin Ajansı</td></tr>{satirlar}</tbody></table>
<h2>Yayın merkezi</h2>
<p>Adres, telefon ve e-posta bilgileri yayın öncesi bu sayfaya eklenecek. Şimdilik bize <a href="{b.yol("iletisim.html")}">İletişim</a> sayfasındaki formdan ulaşabilirsiniz.</p>'''
    return metin_sayfa('kunye.html', 'Künye', 'Filistin Ajansı künyesi: yayıncı ve yayın kadrosu.', govde)

def iletisim():
    govde = f'''<form class="form" action="#" novalidate data-prototip>
  <div class="form__ikili">
    <p class="alan"><label for="if-ad">Ad soyad</label><input id="if-ad" name="ad" type="text" autocomplete="name" required></p>
    <p class="alan"><label for="if-eposta">E-posta</label><input id="if-eposta" name="eposta" type="email" autocomplete="email" required></p>
  </div>
  <p class="alan"><label for="if-konu">Konu</label><select id="if-konu" name="konu"><option>Genel</option><option>Haber ihbarı</option><option>Düzeltme talebi</option><option>Reklam ve iş birliği</option></select></p>
  <p class="alan"><label for="if-mesaj">Mesajınız</label><textarea id="if-mesaj" name="mesaj" rows="6" required></textarea></p>
  <p class="alan alan--onay"><input id="if-onay" name="onay" type="checkbox" required><label for="if-onay">Kişisel verilerimin bu mesajı yanıtlamak için işlenmesini kabul ediyorum (<a href="{b.yol("gizlilik.html")}">Gizlilik</a>).</label></p>
  <button class="dugme" type="submit">Gönder</button>
  <p class="form__durum" role="status" aria-live="polite"></p>
</form>
<h2 id="ihbar">Haber ihbarı</h2>
<p>Bölgeden bir gelişmeyi bize iletmek için konu olarak «Haber ihbarı»nı seçin. Olayın yerini, zamanını ve ne olduğunu kısaca yazın; varsa fotoğrafı yanıt e-postamıza ekleyebilirsiniz. Her ihbarı yayımlamadan önce doğrularız.</p>
<h2 id="duzeltme">Düzeltme talebi</h2>
<p>Bir haberde hata gördüyseniz konu olarak «Düzeltme talebi»ni seçin ve haberin başlığını yazın. Düzeltme haberin sonunda tarihiyle belirtilir.</p>
<h2 id="reklam">Reklam ve iş birliği</h2>
<p>Reklam ve iş birliği talepleriniz için konu olarak «Reklam ve iş birliği»ni seçin; size en kısa sürede dönüş yapılır.</p>
<h2 id="sosyal">Sosyal medya</h2>
<p>X, Instagram, Telegram ve YouTube hesaplarımız yakında açılacak; açıldıklarında bağlantıları sitenin altında yer alacak.</p>'''
    return metin_sayfa('iletisim.html', 'İletişim', 'Filistin Ajansı ile iletişim: haber ihbarı, düzeltme talebi, reklam ve iş birliği.', govde,
                       'Haber ihbarı, düzeltme talebi, reklam ve diğer konular için formu kullanın.')

def gizlilik():
    govde = f'''<h2 id="gizlilik">Gizlilik politikası</h2>
<p>Bu prototip kişisel veri toplamaz. Bülten ve iletişim formları hiçbir yere veri göndermez.</p>
<p>Canlı sitede bu bölüm, 6698 sayılı Kişisel Verilerin Korunması Kanunu’na (KVKK) uygun aydınlatma metniyle güncellenecek: hangi verinin hangi amaçla işlendiği, ne kadar saklandığı ve haklarınızı nasıl kullanacağınız burada yazacak.</p>
<h2 id="cerezler">Çerezler</h2>
<p>Bu prototip çerez kullanmaz. Haber sayfalarında seçtiğiniz yazı boyutu yalnızca kendi tarayıcınızda saklanır. Logo seçeneklerinden birini önizlerken seçiminiz tarayıcının oturum belleğinde tutulur ve tarayıcı kapanınca silinir.</p>
<h2 id="kosullar">Kullanım koşulları</h2>
<p>Sitedeki haber metinleri Filistin Ajansı’na aittir; kaynak göstererek ve bağlantı vererek alıntı yapabilirsiniz.</p>
<p>Fotoğraflar Wikimedia Commons arşivinden, her birinin altında yazan lisansla kullanılmıştır. Yeniden kullanırken aynı lisansa uyun ve çekenin adını yazın.</p>
<p>Haberlerin dayandığı kaynakların bağlantıları her haberin sonunda yer alır; o sayfaların içeriğinden kaynakları sorumludur.</p>'''
    return metin_sayfa('gizlilik.html', 'Gizlilik ve kullanım', 'Filistin Ajansı gizlilik politikası, çerezler ve kullanım koşulları.', govde)

def bulunamadi():
    son = ''.join(b.kart(x['id'], FOTO[x['id']]) for x in [x for x in TUMU if FOTO[x['id']]][:4])
    bolumler = ''.join(f'<a class="cip" href="{b.yol(h)}">{e(t)}</a>' for h, t in b.MENU)
    icerik = f'''<main id="icerik" class="kap sayfa">
  <section class="yok">
    <p class="yok__kod">404</p>
    <h1>Sayfa bulunamadı</h1>
    <p>Aradığınız sayfa taşınmış ya da hiç var olmamış olabilir. Haberlerde arayabilir ya da bir bölüme gidebilirsiniz.</p>
    <form class="ara" action="{b.yol("arama.html")}" method="get" role="search">
      <label class="sr" for="yok-q">Aranacak kelime</label>
      <input id="yok-q" name="q" type="search" placeholder="Haberlerde ara" enterkeyhint="search">
      <button type="submit">{ic("ara")}<span>Ara</span></button>
    </form>
    <nav class="cipler" aria-label="Bölümler"><a class="cip" href="{b.yol("home.html")}">Ana Sayfa</a>{bolumler}</nav>
  </section>
  <section class="bolum" aria-labelledby="yok-son">{ara_baslik("Son haberler", "yok-son")}<div class="sira4">{son}</div></section>
</main>'''
    return sayfa('404.html', 'Sayfa bulunamadı', 'Aradığınız sayfa bulunamadı.', icerik, govde='g-yok', tam_baslik='Sayfa bulunamadı — Filistin Ajansı')

def kaynaklar():
    """assets/img/arsiv/KAYNAKLAR.md: author, licence, year and Commons page of every archive photo, shipped with the site."""
    rows = [f'| {p["id"]}-*.webp | {p.get("place_tr", "")} | {p.get("author", "")} | {p.get("license", "")} | {p.get("year", "")} | {p["commons_page"]} |'
            for p in b.PH if p['id'] in LOCAL]
    md = '\n'.join(['# Arşiv fotoğrafları — kaynaklar ve lisanslar', '',
                    'Bu klasördeki fotoğraflar Wikimedia Commons arşivindendir; haberlerin anına ait değildir.',
                    'Her dosya özgün lisansıyla yeniden boyutlandırılıp WebP biçimine çevrilmiştir.', '',
                    '| Dosya | Yer | Çeken | Lisans | Yıl | Kaynak |', '|---|---|---|---|---|---|'] + rows) + '\n'
    open(P('assets', 'img', 'arsiv', 'KAYNAKLAR.md'), 'w', encoding='utf-8').write(md)
    return len(rows)

# ---------- run ----------
if __name__ == '__main__':
    out = {}
    b.R = ''
    out['home.html'] = b.build_home()
    out['index.html'] = b.build_index()
    b.R = '../'
    for k, it in enumerate(TUMU):
        haber_sayfasi(it, TUMU[k + 1] if k + 1 < len(TUMU) else None, TUMU[k - 1] if k else None)
    out['haber/*'] = len(TUMU)
    b.R = ''
    for sid in BOLUM_SAYFA:
        out[f'{sid}.html'] = bolum_sayfasi(sid)
    out['son-dakika.html'] = son_dakika()
    out['rakamlar.html'] = rakamlar()
    out['galeri.html'] = galeri()
    out['haberler.json'] = arama_verisi()
    out['arama.html'] = arama()
    out['bulten.html'] = bulten()
    out['hakkimizda.html'] = hakkimizda()
    out['kunye.html'] = kunye()
    out['iletisim.html'] = iletisim()
    out['gizlilik.html'] = gizlilik()
    b.R = SITE_PATH
    out['404.html'] = bulunamadi()
    b.R = ''
    out['KAYNAKLAR.md'] = kaynaklar()
    b.R = ''
    missing = [i for i, p in FOTO.items() if not p]
    for k, v in out.items():
        print(k, v)
    print('stories without a photo of their place:', len(missing), ' '.join(missing))
