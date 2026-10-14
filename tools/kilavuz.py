"""Builds index.html, the identity guide («Kimlik kılavuzu»). Called from tools/build.py,
which passes its globals (logo, symbols, pafta, edition data)."""
import os, re, math


def build(G):
    e, T, isr, ui = G['e'], G['T'], G['isr'], G['ui']
    BY_ID, ITEMS, TODAY_ITEMS = G['BY_ID'], G['ITEMS'], G['TODAY_ITEMS']
    logo_svg, pafta, geo, logo = G['logo_svg'], G['pafta'], G['geo'], G['logo']
    saat, date_tr, place_label, sym_of, first, kayit = G['saat'], G['date_tr'], G['place_label'], G['sym_of'], G['first'], G['kayit']
    LOCAL, PHOTOS, W, H = G['LOCAL'], G['PHOTOS'], G['W'], G['H']
    wb_xy = G['wb_xy']
    P = G['P']
    pid = {p['id']: p for p in PHOTOS}

    # ---------- small builders ----------
    def mark_svg(cls='', size_box=True, ink='currentColor'):
        m = logo['mark']; bx, by, bs = m['box']
        tri = ' '.join(f'{x:.1f},{y:.1f}' for x, y in m['tri'])
        boxr = f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bs:.1f}" height="{bs:.1f}" fill="none" stroke="{ink}" stroke-width="{m["boxStroke"]}"/>' if size_box else ''
        return (f'<svg class="{cls}" viewBox="0 0 {logo["box"]} {logo["box"]}" aria-hidden="true" focusable="false">{boxr}'
                f'<polygon points="{tri}" fill="none" stroke="{ink}" stroke-width="{m["tw"]:.1f}"/>'
                f'<circle class="l-dot" cx="{m["centroid"][0]:.1f}" cy="{m["centroid"][1]:.1f}" r="{m["dot"]:.1f}"/></svg>')

    def locator(lat, lon, cls='konumcu'):
        x, y = wb_xy(lon, lat)
        return (f'<svg class="{cls}" viewBox="380 0 700 1371" aria-hidden="true" focusable="false">'
                f'<path class="konumcu__zemin" d="{geo["wbLo"]}"/><circle class="konumcu__halka" cx="{x:.0f}" cy="{y:.0f}" r="70"/><circle class="konumcu__nokta" cx="{x:.0f}" cy="{y:.0f}" r="26"/></svg>')

    def img(pid_, cls='', sizes='50vw'):
        if pid_ not in LOCAL:
            return ''
        loc = LOCAL[pid_]
        return f'<img class="{cls}" src="{loc["src"]}" srcset="{loc["srcset"]}" sizes="{sizes}" width="{loc["w"]}" height="{loc["h"]}" alt="{e(G["tr_text"](pid[pid_].get("caption_tr", "")))}" decoding="async">'

    def credit(pid_):
        p = pid[pid_]
        return f'Arşiv · {e(p.get("author", ""))} · {e(p.get("license", ""))} · Wikimedia Commons'

    def section(sid, title, intro, body, cls=''):
        return (f'<section class="bolum ic bant {cls}" id="{sid}" aria-labelledby="{sid}-b">'
                f'<div class="baslik"><h2 id="{sid}-b">{title}</h2>{f"<p>{intro}</p>" if intro else ""}</div>{body}</section>\n<hr class="kat">\n')

    TOC = [('fikir', 'Fikir'), ('isaret', 'İşaret'), ('logo', 'Logo'), ('murekkep', 'Mürekkepler'), ('harf', 'Harf'),
           ('lejant', 'Lejant'), ('pafta', 'Pafta'), ('hareket', 'Hareket'), ('sosyal', 'Sosyal medya'), ('uygulama', 'Uygulamalar'), ('indir', 'İndir')]
    tocnav = ''.join(f'<a href="#{i}">{t}</a>' for i, t in TOC if i in ('fikir', 'isaret', 'logo', 'murekkep', 'harf', 'lejant', 'sosyal', 'indir'))

    out = []

    # ---------- cover ----------
    legend6 = [('baskin', 'Baskın'), ('kapi', 'Kapalı kapı'), ('zeytin', 'Zeytin hasadı'), ('yikim', 'Yıkım'), ('esir', 'Esir'), ('nirengi', 'Filistin Ajansı')]
    out.append(f'''<section class="kapak ic" aria-labelledby="kapak-b">
  <div class="kapak__sahne">
    <div class="kapak__logo-kutu">{logo_svg('kapak__logo yukleyici__logo')}<svg class="kapak__isin yukleyici__isinlar" aria-hidden="true"></svg></div>
  </div>
  <div class="kapak__metin">
    <h1 id="kapak-b">Her haber bir yer,<br>her yer bir işaret.</h1>
    <p class="kapak__giris">Filistin Ajansı, Filistin’in ve Batı Şeria’nın haberlerini Türkçe okura taşır. Kimliğin dili, Batı Şeria’yı anlatan haritaların dilidir: kontrol noktaları, kapılar, toprak setler, duvar. Bu dilde her olay bir işarettir ve her işaretin bir yeri vardır.</p>
    <div class="kapak__eylem"><button class="dugme dugme--cizgi" type="button" data-oynat="kapak">Açılışı yeniden oynat</button><a class="dugme" href="home.html">Ana sayfayı aç</a></div>
  </div>
  <ul class="kapak__lejant" aria-label="Lejanttan örnekler">{''.join(f'<li>{isr(s, "bugun" if s != "nirengi" else "")}<span>{t}</span></li>' for s, t in legend6)}</ul>
</section>
<hr class="kat">
''')

    # ---------- idea ----------
    f17 = BY_ID['f17']
    crop_x, crop_y = wb_xy(35.286, 32.036)
    mini = pafta([f17], cls='mini-pafta', title_id='mini-pafta-b', gaza=False, size=56, interactive=False)
    vx, vy, vw, vh = crop_x - 240, crop_y - 190, 480, 380
    mini = mini.replace(f'viewBox="0 0 {W} {H}"', f'viewBox="{vx:.0f} {vy:.0f} {vw} {vh}"')
    def keep(mm):
        cxv, cyv = float(mm.group(1)), float(mm.group(2))
        return mm.group(0) if (vx + 30 < cxv < vx + vw - 120 and vy + 40 < cyv < vy + vh - 30) else ''
    mini = re.sub(r'<g class="yerlesim[^"]*"><circle cx="([\d.]+)" cy="([\d.]+)".*?</g>', keep, mini)
    out.append(section('fikir', 'Neden harita dili?', '', f'''
<div class="fikir">
  <div class="fikir__metin">
    <p class="buyuk-metin">Batı Şeria’nın gündelik haberleri toprağın haberleridir: bir köyün girişine kurulan demir kapı, sökülen zeytin ağaçları, yıkılan bir ev, gece baskın yapılan bir kamp. Bu olaylar en açık hâliyle haritada anlatılır.</p>
    <p>BM’nin Batı Şeria erişim haritaları yıllardır aynı işaretlerle çizilir: kontrol noktası, kapı, toprak set, duvar. Filistin Ajansı bu notasyonu kendi diline çevirir. Lejant hem menüdür hem de haberin durumudur. Okur sitede, sosyal medyada ya da bir video bandında aynı işareti görür ve ne olduğunu, nerede olduğunu bir bakışta anlar.</p>
    <dl class="ilkeler">
      <div><dt>{isr('nirengi')}Önce yer</dt><dd>Her haber bir yere bağlanır, yer adı Türkçe yazılışıyla verilir: Tulkerem, El Halil, Beytüllahim, Ürdün Vadisi.</dd></div>
      <div><dt><span class="ilke-bag" aria-hidden="true"></span>Her sayının kaynağı var</dt><dd>Kaynağı ve tarihi olmayan sayı yayımlanmaz. Sayı ile kaynağı arasında her zaman bir gösterge çizgisi vardır.</dd></div>
      <div><dt><span class="ilke-mor" aria-hidden="true"></span>Bugün mor basılır</dt><dd>Haritada yalnız bugünün kayıtları mor; önceki günler gri altlığa çekilir. Tazelik renkle değil baskıyla anlatılır.</dd></div>
    </dl>
  </div>
  <figure class="fikir__ornek">
    <figcaption class="yer yer--base">Bir haber, üç yerde</figcaption>
    <div class="fikir__ornek-harita">{mini}<span class="fikir__not">Haritada</span></div>
    <div class="fikir__ornek-akis"><ol>{kayit(f17)}</ol><span class="fikir__not">Akışta</span></div>
    <div class="fikir__ornek-lejant"><span class="lejant-satir">{isr('zeytin', 'bugun')}<span>Zeytin hasadı</span><b class="num">5</b></span><span class="fikir__not">Lejantta</span></div>
  </figure>
</div>'''))

    # ---------- mark ----------
    m = logo['mark']; bx, by, bs = m['box']
    (ax, ay), (bx2, by2), (cx, cy) = m['tri']
    cen = m['centroid']
    B = logo['box']
    dims = f'''<svg class="insa" viewBox="-520 -260 {B + 1180} {B + 620}" role="img" aria-labelledby="insa-b">
  <title id="insa-b">Nirengi işaretinin yapısı</title>
  <g class="insa__izgara">{''.join(f'<path d="M{k * B / 8:.0f} -120V{B + 120}"/><path d="M-120 {k * B / 8:.0f}H{B + 120}"/>' for k in range(9))}</g>
  <rect x="{bx:.1f}" y="{by:.1f}" width="{bs:.1f}" height="{bs:.1f}" class="insa__kutu" stroke-width="{m["boxStroke"]}"/>
  <polygon points="{' '.join(f'{x:.1f},{y:.1f}' for x, y in m['tri'])}" class="insa__ucgen" stroke-width="{m["tw"]:.1f}"/>
  <circle cx="{cen[0]:.1f}" cy="{cen[1]:.1f}" r="{m["dot"]:.1f}" class="insa__nokta"/>
  <g class="insa__olcu">
    <path d="M0 {B + 90}H{B}M0 {B + 60}V{B + 120}M{B} {B + 60}V{B + 120}"/><text x="{B / 2}" y="{B + 200}" text-anchor="middle">a</text>
    <path d="M{ax:.0f} {ay + 140:.0f}H{bx2:.0f}M{ax:.0f} {ay + 110:.0f}V{ay + 170:.0f}M{bx2:.0f} {ay + 110:.0f}V{ay + 170:.0f}"/><text x="{(ax + bx2) / 2:.0f}" y="{ay + 260:.0f}" text-anchor="middle">0,62 a</text>
    <path d="M{B + 90} 0V{ay:.0f}M{B + 60} {ay:.0f}H{B + 120}M{B + 60} 0H{B + 120}"/><text x="{B + 150}" y="{ay / 2:.0f}">0,785 a</text>
    <path d="M{cen[0] + m['dot'] + 20:.0f} {cen[1]:.0f}L{-300} {cen[1] - 380:.0f}H-480"/><text x="-480" y="{cen[1] - 420:.0f}">nokta ⌀ 0,092 a</text>
    <path d="M{(ax + cx) / 2:.0f} {(ay + cy) / 2:.0f}L-300 {cen[1] + 240:.0f}H-480"/><text x="-480" y="{cen[1] + 200:.0f}">çizgi 0,063 a</text>
  </g>
</svg>'''
    tri_line = f'''<div class="ucnokta">{logo_svg('ucnokta__logo')}<svg class="ucnokta__isin" aria-hidden="true"></svg></div>'''
    out.append(section('isaret', 'İşaret: nirengi noktası', '', f'''
<div class="isaret">
  <div class="isaret__metin">
    <p class="buyuk-metin">Haritacılıkta nirengi noktası, konumu ölçülerek kesinleştirilmiş noktadır. Paftalarda içinde nokta olan bir üçgenle gösterilir.</p>
    <p>Filistin Ajansı’nın işareti bu semboldür: doğrulanmış bir yer. Üçgen bir lejant kutusunun içinde durur, çünkü logonun kendisi bir lejant satırıdır: solda işaret, sağda adı. Ad, haritada bölge adları nasıl yazılıyorsa öyle dizilir: aralıklı büyük harflerle, iki satırda.</p>
    <h3>Üç bilinen nokta</h3>
    <p>FİLİSTİN kelimesindeki üç İ’nin noktası mor basılır. Nirengide yeni bir noktanın yeri, bilinen üç noktadan bakılarak bulunur; ajansın noktası da bu üç noktadan bulunur. Açılış animasyonu tam olarak bunu gösterir.</p>
    {tri_line}
  </div>
  <figure class="isaret__insa">{dims}<figcaption>Kutu yüksekliği (a) iki satırlık adın yüksekliğine eşittir. Nokta küçük kalır: üçgen içinde büyüyen bir nokta göz gibi okunur.</figcaption></figure>
</div>
<div class="bosluk">
  <figure class="bosluk__ornek"><div class="bosluk__alan">{logo_svg('bosluk__logo')}</div><figcaption><b>Boşluk.</b> Logonun çevresinde en az kutunun yarısı kadar (0,5 a) boş alan bırakılır.</figcaption></figure>
  <figure class="bosluk__ornek"><div class="bosluk__boy"><span>{logo_svg('boy-120')}<i class="num">120 px</i></span><span>{logo_svg('boy-90')}<i class="num">90 px · en küçük</i></span><span>{mark_svg('boy-16')}<i class="num">16 px</i></span></div><figcaption><b>En küçük boy.</b> İki satırlık logo 90 piksel (ekran) ya da 24 mm (baskı) altına inmez; daha küçük yerlerde yalnız işaret kullanılır.</figcaption></figure>
</div>'''))

    # ---------- logo versions + misuse ----------
    files = [('logo.svg', 'Ana logo', 'kagit'), ('logo-gece.svg', 'Gece', 'gece'), ('logo-mono-siyah.svg', 'Tek renk, siyah', 'kagit'),
             ('logo-mono-beyaz.svg', 'Tek renk, beyaz', 'mor'), ('logo-tek-satir.svg', 'Tek satır', 'kagit'), ('isaret.svg', 'İşaret', 'kagit'),
             ('isaret-avatar.svg', 'Profil fotoğrafı', 'yok'), ('isaret-avatar-gece.svg', 'Profil fotoğrafı, gece', 'yok')]
    tiles = ''.join(f'<figure class="karo karo--{bg}"><div class="karo__alan"><img src="assets/brand/{f}?v={G["V"]}" alt="{e(t)}"></div><figcaption><span>{e(t)}</span><a href="assets/brand/{f}" download>{f}</a></figcaption></figure>' for f, t, bg in files)
    wrong = [
        ('ters', 'Üçgeni ters çevirmeyin. Ters üçgen başka bir sembolle karışır; işaretin tepesi her zaman yukarıdadır.'),
        ('kirmizi', 'Üçgeni doldurmayın, kırmızıya boyamayın. İşaret bir çizgi sembolüdür.'),
        ('goz', 'Noktayı büyütmeyin. Üçgen içinde büyük nokta göz gibi okunur.'),
        ('esnek', 'Esnetmeyin, eğmeyin, gölge vermeyin.'),
        ('aralik', 'Adı yeniden dizmeyin, harf aralığını değiştirmeyin.'),
        ('foto', 'Kalabalık fotoğrafın üstüne zeminsiz koymayın; kâğıt zemin ya da mor plaka kullanın.'),
    ]
    wtiles = ''
    for k, t in wrong:
        if k == 'aralik':
            vis = '<span class="yanlis__yazi">Filistin Ajansı</span>'
        elif k == 'foto':
            vis = f'{img("p23", "yanlis__foto", "20vw")}<span class="yanlis__ust">{logo_svg("yanlis__logo")}</span>'
        else:
            vis = logo_svg(f'yanlis__logo yanlis--{k}')
        wtiles += f'<figure class="yanlis"><div class="yanlis__alan">{vis}<svg class="yanlis__cizik" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><path d="M2 98L98 2"/></svg></div><figcaption>{t}</figcaption></figure>'
    out.append(section('logo', 'Logo', 'Sekiz sürüm, her biri SVG olarak indirilebilir. Zemine göre seçilir: kâğıt, gece ya da mor.', f'''
<div class="karolar">{tiles}</div>
<h3 class="alt-baslik">Yapmayın</h3>
<div class="yanlislar">{wtiles}</div>'''))

    # ---------- inks ----------
    inks = [
        ('Çizim siyahı', '#121417', '18 · 13 · 0 · 91', '18, 20, 23', 'Metin, çizgi, sınır, çerçeve.', '17,9:1', '#E9EDEF', '16,0:1', 'ink'),
        ('Altlık grisi', '#5D666C', '14 · 6 · 0 · 58', '93, 102, 108', 'Altlık harita, ikincil metin, önceki günlerin işaretleri.', '5,7:1', '#98A2A8', '7,2:1', 'base'),
        ('Güncelleme moru', '#A3127F', '0 · 89 · 22 · 36', '163, 18, 127', 'Yalnız bugün: bugünün kayıtları, canlı yayın, yer etiketleri. ABD’nin topoğrafik paftalarında sahada henüz doğrulanmamış yeni bilgiler mor ek baskıyla işlenirdi; burada da mor, en yeni bilginin rengidir.', '6,9:1', '#EE63C8', '6,5:1', 'mag'),
        ('Su mavisi', '#2D5C9A', '71 · 40 · 0 · 40', '45, 92, 154', 'Ürdün Nehri, Ölü Deniz, Akdeniz ve doğal adlar.', '6,6:1', '#78A4E0', '7,3:1', 'blue'),
        ('Yeşil Hat', '#2E7A4D', '62 · 0 · 37 · 52', '46, 122, 77', '1949 ateşkes hattı ve zeytinlik işareti. Başka hiçbir yerde kullanılmaz.', '5,1:1', '#62BE87', '8,3:1', 'green'),
        ('Kâğıt', '#FBFCFC', '1 · 0 · 0 · 1', '251, 252, 252', 'Zemin. Krem ya da bej değil: soğuk, temiz harita kâğıdı.', '—', '#0F1214', '—', 'paper'),
    ]
    rows = ''.join(f'''<tr><td><span class="murekkep murekkep--{k}" style="--c:{hx};--cg:{nh}"><i></i><i></i></span></td><th scope="row">{n}</th><td>{r}</td>
      <td class="num">{hx}<br><span class="kaynak">RGB {rgb}</span><br><span class="kaynak">CMYK {cm}</span></td><td class="num">{c1}</td><td class="num">{nh}<br><span class="kaynak">{c2}</span></td></tr>''' for n, hx, cm, rgb, r, c1, nh, c2, k in inks)
    out.append(section('murekkep', 'Mürekkepler', 'Altı mürekkep, her birinin tek bir işi var. Ara tonlar şeffaflıkla değil, haritadaki gibi ekran ve taramayla elde edilir.', f'''
<div class="tablo-kap"><table class="murekkep-tablo"><caption class="sr">Mürekkepler, değerleri ve kâğıt üzerindeki kontrast</caption>
<thead><tr><th scope="col"><span class="sr">Örnek</span></th><th scope="col">Ad</th><th scope="col">Görev</th><th scope="col">Değer</th><th scope="col">Kontrast</th><th scope="col">Gece</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<div class="desenler">
  <figure><svg viewBox="0 0 200 120" aria-hidden="true"><defs><pattern id="d-ekran" width="11" height="11" patternUnits="userSpaceOnUse"><circle cx="5.5" cy="5.5" r="1.3" class="ekran"/></pattern></defs><rect width="200" height="120" fill="url(#d-ekran)"/></svg><figcaption><b>Nokta ekranı.</b> Haritanın dışında kalan kara.</figcaption></figure>
  <figure><svg viewBox="0 0 200 120" aria-hidden="true"><defs><pattern id="d-su" width="12" height="8" patternUnits="userSpaceOnUse"><path d="M0 4H12" class="su-cizgi"/></pattern></defs><rect width="200" height="120" fill="url(#d-su)"/></svg><figcaption><b>Su çizgileri.</b> Ölü Deniz ve Akdeniz.</figcaption></figure>
  <figure><svg viewBox="0 0 200 120" aria-hidden="true"><defs><pattern id="d-tar" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V12" class="d-tarama"/></pattern></defs><rect width="200" height="120" fill="url(#d-tar)"/></svg><figcaption><b>Mor tarama.</b> Seçili il, işaretli alan.</figcaption></figure>
  <figure><div class="zeytinlik__alan zeytinlik__alan--ornek" aria-hidden="true">{''.join('<i class="h"></i>' if k % 3 else '<i></i>' for k in range(40))}</div><figcaption><b>Zeytinlik.</b> Her işaret bir kayıt; mor olanlar hasatla bağlantılı.</figcaption></figure>
</div>'''))

    # ---------- type ----------
    finalists = [('Atkinson Hyperlegible Next', 'Çok okunaklı ama başlıkta geniş; dar sürümü yok.'), ('Mona Sans', 'Genişlik ekseni iyi; manşet dört satıra çıktı, karakteri GitHub’ı çağrıştırıyor.'),
                 ('Fira Sans', 'Gerçek italik ve dar sürüm; çok yaygın, kendine ait bir ses vermiyor.'), ('Alegreya Sans', 'Harita yazısına en yakın el: gerçek italik, eski üslup rakamlar, küçük harf büyükleri. Manşet üç satıra sığdı.')]
    scale = [('Manşet', '3,3 rem / 52 px', '800', '1,02', 'Yerleşimciler Turmus Ayya’da zeytin toplayan Filistinlilere saldırdı', 'o-manset'),
             ('Bölüm başlığı', '2,6 rem / 42 px', '800', '1,08', 'İl il Batı Şeria', 'o-bolum'),
             ('Haber başlığı', '1,375 rem / 22 px', '800', '1,15', 'İsrail, Tekua’nın yedi girişini ikinci gün de kapalı tuttu', 'o-haber'),
             ('Metin', '1,125 rem / 18 px', '400', '1,6', 'Tekua Belediye Başkanı’nın WAFA’ya verdiği bilgiye göre İsrail güçleri beldenin yedi girişini demir kapılarla kapattı.', 'o-metin'),
             ('Yer etiketi', '0,75 rem / 12 px · +0,16 em', '700', '1,25', 'Beytüllahim · Tekua · 13.09', 'o-yer'),
             ('Veri', '0,9375 rem / 15 px · tablo rakamı', '700', '1,3', '9.400 · 3.101 · 13.09', 'o-veri')]
    srows = ''.join(f'<tr><th scope="row">{n}<span class="kaynak">{s} · {w} · {lh}</span></th><td><span class="{c}">{t}</span></td></tr>' for n, s, w, lh, t, c in scale)
    out.append(section('harf', 'Harf: Alegreya Sans', '', f'''
<div class="harf">
  <div class="harf__ornek" aria-hidden="true">
    <p class="harf__dev">Aa Ğğ İı Şş</p>
    <p class="harf__agirlik"><span style="font-weight:400">Normal</span><span style="font-weight:400;font-style:italic">İtalik</span><span style="font-weight:500">Orta</span><span style="font-weight:700">Kalın</span><span style="font-weight:700;font-style:italic">Kalın italik</span><span style="font-weight:800">Ekstra kalın</span></p>
    <p class="harf__pangram">Pijamalı hasta yağız şoföre çabucak güvendi.</p>
    <p class="harf__rakam"><span><b class="o-eski">0123456789</b><i>Metinde eski üslup</i></span><span><b class="num">0123456789</b><i>Veride dik, eşit genişlik</i></span></p>
  </div>
  <div class="harf__metin">
    <p class="buyuk-metin">Harita yazısının kuralı eskidir: yerleşim adları dik, bölge adları aralıklı büyük harf, doğal adlar italik.</p>
    <p>Bunun için gerçek italiği olan, küçük boyda bile okunan, insan elinden çıkmış gibi duran bir sans gerekiyordu. On dört aday aynı Türkçe başlık, aynı özet ve aynı harita etiketleriyle karşılaştırıldı. Son dörde kalanlar:</p>
    <ul class="finalist">{''.join(f'<li><b>{n}</b><span>{t}</span></li>' for n, t in finalists)}</ul>
    <p class="kaynak">Alegreya Sans, Juan Pablo del Peral, Huerta Tipográfica. SIL Open Font License. Sitede kendi sunucumuzdan, Türkçe karakterleri ve bütün OpenType özellikleriyle yüklenir.</p>
  </div>
</div>
<figure class="karsilastirma"><img src="assets/img/harf-karsilastirma.webp?v={G["V"]}" width="1200" height="662" alt="Son dört aday aynı manşet ve aynı harita etiketleriyle: Atkinson Hyperlegible Next, Mona Sans, Fira Sans ve seçilen Alegreya Sans" decoding="async"><figcaption>Karşılaştırmadan bir kesit: aynı manşet, aynı genişlik, aynı etiketler.</figcaption></figure>
<div class="harita-yazisi">
  <figure><span class="hy-yerlesim">Nablus</span><figcaption>Yerleşim: dik, kalın</figcaption></figure>
  <figure><span class="yer yer--ink hy-bolge">Tubas · Cenin</span><figcaption>Bölge ve il: aralıklı büyük harf</figcaption></figure>
  <figure><span class="hy-doga">Ürdün Vadisi</span><figcaption>Doğal ad: italik, su mavisi</figcaption></figure>
  <figure><span class="hy-veri num">32°13′ K</span><figcaption>Ölçüm: tablo rakamı</figcaption></figure>
</div>
<div class="tablo-kap"><table class="olcek-tablo"><caption class="sr">Yazı ölçeği</caption><tbody>{srows}</tbody></table></div>'''))

    # ---------- legend set ----------
    sym = [('baskin', 'Baskın', 'Bir yere giriş: gece baskısı, kuşatma.'), ('gozalti', 'Gözaltı', 'Çerçeve içinde bir kişi.'), ('yerlesimci', 'Yerleşimci saldırısı', 'Olay patlaması.'),
           ('yikim', 'Yıkım', 'Üzeri çizili ev.'), ('kapi', 'Kapalı kapı', 'İki direk, kapalı kol.'), ('kapi-acik', 'Açık kapı', 'Kol kalkık.'),
           ('kontrol', 'Kontrol noktası', 'Halka ve kol.'), ('set', 'Toprak set', 'Yolda tümsek.'), ('zeytin', 'Zeytin hasadı', 'Topoğrafik haritanın zeytinlik işareti.'),
           ('kayip', 'Can kaybı', 'Dolu nokta.'), ('yarali', 'Yaralı', 'Halka ve artı.'), ('saldiri', 'Saldırı, ateşkes ihlali', 'Dolu yıldız.'),
           ('insani', 'İnsani durum', 'Yardım, geçiş, sağlık.'), ('aksa', 'Mescid-i Aksa', 'Kubbe ve alem.'), ('esir', 'Esir', 'Hücre penceresi.'),
           ('siyaset', 'Siyaset ve diplomasi', 'Flama.'), ('diger', 'Diğer', 'Boş baklava.'), ('nirengi', 'Filistin Ajansı', 'Doğrulanmış yer.')]
    grid = ''.join(f'<li><span class="isr-kutu">{isr(s)}</span><b>{t}</b><span>{d}</span></li>' for s, t, d in sym)
    states = [('bugun', 'Bugün', 'Mor ek baskı.'), ('dun', 'Önceki günler', 'Gri altlık.'), ('bugun gelisen', 'Gelişiyor', 'Kesik çizgi: harita dilinde “henüz tamamlanmadı”.'),
              ('bugun bitti-isr', 'Sona erdi', 'Üzeri çizili: kapı açıldı, baskın bitti.'), ('bugun canli', 'Canlı', 'Halka nabız gibi genişler.')]
    srow = ''
    for c, t, d in states:
        icon = isr('kapi', c.replace(' canli', '').replace(' bitti-isr', ''))
        if 'canli' in c:
            icon = f'<span class="canli-halka">{icon}</span>'
        if 'bitti' in c:
            icon = f'<span class="bitti-kutu">{icon}<svg class="bitti-cizik" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 21L21 3"/></svg></span>'
        srow += f'<li><span class="isr-kutu isr-kutu--buyuk">{icon}</span><b>{t}</b><span>{d}</span></li>'
    out.append(section('lejant', 'Lejant: işaretler', 'Her işaret 24 birimlik ızgarada, 1,7 piksel çizgiyle, kare uçlarla çizilir. Renk bağlamdan gelir: bugün mor, önceki günler gri. Durum renkle değil işaretin biçimiyle anlatılır.', f'''
<ul class="isaret-izgara">{grid}</ul>
<h3 class="alt-baslik">Durumlar</h3>
<ul class="isaret-izgara isaret-izgara--durum">{srow}</ul>
<h3 class="alt-baslik">Çizgiler</h3>
<ul class="cizgi-listesi">
  <li><i class="c-yesil"></i><b>Yeşil Hat</b><span>1949 ateşkes hattı. Yeşil, kesik.</span></li>
  <li><i class="c-duvar"></i><b>Ayırma duvarı</b><span>Çizgi ve diş. Kaynak: OpenStreetMap.</span></li>
  <li><i class="c-plan"></i><b>Planlanan duvar</b><span>Kesik çizgi.</span></li>
  <li><i class="c-nehir"></i><b>Nehir ve kıyı</b><span>Su mavisi.</span></li>
  <li><i class="c-il"></i><b>İl sınırı</b><span>Gri, ince, kesik.</span></li>
  <li><i class="c-kat"></i><b>Kıvrım</b><span>Sayfadaki bölümler arasında: kâğıt haritanın katlandığı yer.</span></li>
</ul>'''))

    # ---------- the pafta ----------
    big = pafta(ITEMS, cls='kilavuz-pafta', title_id='kilavuz-pafta-b', interactive=False)
    out.append(section('pafta', 'Pafta', 'Ana sayfanın kalbi: Batı Şeria’nın bugünkü paftası. Gazze Şeridi aynı ölçekte, yeri kaydırılmış bir ek paftada durur.', f'''
<div class="pafta-kural">
  <figure class="pafta-kural__harita"><h3 class="sr" id="kilavuz-pafta-b">Örnek pafta, 12–14 Ekim 2026</h3>{big}</figure>
  <ol class="kural-listesi">
    <li><b>Mor yalnız bugündür.</b> Önceki iki günün kayıtları gri kalır; gün döndüğünde mor baskı griye iner.</li>
    <li><b>İşaret haberdir, etiket yol verir.</b> Yer adları sekiz konumu dener ve haber işaretlerini en az örten konuma yerleşir.</li>
    <li><b>Üst üste binen haberler halkaya açılır.</b> Gerçek yerinde küçük bir nokta kalır, işaret bir gösterge çizgisiyle ona bağlanır.</li>
    <li><b>Gazze aynı ölçektedir.</b> Ek paftanın yeri kaydırılmıştır ve bu her zaman yazılır.</li>
    <li><b>İller kuzeyden güneye sıralanır.</b> Cenin’den El Halil’e; sayfada aşağı inmek haritada güneye inmektir.</li>
    <li><b>Kaynaklar açıktır.</b> Sınırlar geoBoundaries (CC BY 4.0), duvar OpenStreetMap (ODbL), su Natural Earth.</li>
  </ol>
</div>'''))

    # ---------- motion ----------
    demo = pafta(TODAY_ITEMS, cls='demo-pafta', title_id='demo-pafta-b', interactive=False, size=44)
    out.append(section('hareket', 'Hareket', 'Dört an, hepsi işaretin kendi davranışından. Azaltılmış hareket tercihinde hiçbiri oynamaz; içerik her zaman baştan görünür.', f'''
<div class="hareket">
  <div class="hareket__liste">
    <article><h3>Açılış: nirengi</h3><p>Üç İ noktası belirir, onlardan çıkan görüş çizgileri ajansın noktasını bulur, üçgen ve kutu çizilir, ad soldan sağa yazılır ve logo başlıktaki yerine uçar. Oturum başına bir kez, 2,6 saniye; tıklama ya da tuş geçer.</p><button class="dugme dugme--cizgi" type="button" data-oynat="kapak">Oynat</button></article>
    <article><h3>Mor baskı</h3><p>Sayfa açılınca bugünün işaretleri geliş sırasıyla basılır. Mor kalıp hafif kayık iner ve yerine oturur, tıpkı ek baskıda olduğu gibi. İşaret başına 55 ms aralık.</p><button class="dugme dugme--cizgi" type="button" data-oynat="baski">Oynat</button></article>
    <article><h3>Gösterge çizgisi</h3><p>Akıştaki bir haberin üstüne gelindiğinde, haber haritadaki yerine bir çizgiyle bağlanır. 320 ms, önce omuz, sonra yer.</p><a class="tum" href="home.html#pafta">Ana sayfada dene {ui('ok', 'isr')}</a></article>
    <article><h3>Enlem imleci</h3><p>İl il bölümünde okur aşağı indikçe imleç enlem cetvelinde güneye iner ve bulunduğu ilin enlemini yazar. 500 ms.</p><a class="tum" href="home.html#bati-seria">Ana sayfada dene {ui('ok', 'isr')}</a></article>
  </div>
  <figure class="hareket__demo"><h3 class="sr" id="demo-pafta-b">Mor baskı örneği</h3>{demo}<figcaption class="kaynak">Eğri: cubic-bezier(.16, 1, .3, 1), hızlı çıkış, yumuşak duruş.</figcaption></figure>
</div>'''))

    # ---------- social ----------
    f02, f07, f16 = BY_ID['f02'], BY_ID['f07'], BY_ID['f16']
    def post_ust(live=False):
        flag = '<span class="post__etiket"><span class="post__halka"></span>Son dakika</span>' if live else ''
        return f'<div class="post__ust"><span class="post__marka">{mark_svg("post__isaret")}<b>FİLİSTİN<br>AJANSI</b></span>{flag}</div>'
    p_sondakika = f'''<figure class="post-kap"><div class="post post--sondakika" style="aspect-ratio:4/5">
      {post_ust(True)}
      <div class="post__govde"><p class="post__baslik">{T(f02["headline_tr"])}</p>
      <p class="post__yer">{T(place_label(f02, True))} · {saat(f02["time"])}</p></div>
      <div class="post__alt">{locator(f02["lat"], f02["lon"], "post__konum")}<span>Kaynak: {e(f02["source_name"])}<br>{date_tr(f02["date"])}</span></div>
    </div><figcaption>Son dakika · 1080 × 1350</figcaption></figure>'''
    p_haber = f'''<figure class="post-kap"><div class="post post--haber" style="aspect-ratio:4/5">
      <div class="post__foto">{img("p03", "", "30vw")}<span class="post__arsiv">Arşiv</span></div>
      <div class="post__govde">{post_ust()}<p class="post__baslik">{T(f17["headline_tr"])}</p><p class="post__yer">{T(place_label(f17))}</p></div>
      <div class="post__alt">{locator(f17["lat"], f17["lon"], "post__konum")}<span>Kaynak: {e(f17["source_name"])} · {date_tr(f17["date"])}<br>{credit("p03")}</span></div>
    </div><figcaption>Haber · 1080 × 1350</figcaption></figure>'''
    cells = ''.join(f'<i class="{"h" if k < 136 else ""}"></i>' for k in range(219))
    p_rakam = f'''<figure class="post-kap"><div class="post post--rakam" style="aspect-ratio:4/5">
      {post_ust()}
      <div class="post__govde"><p class="post__dev num">219</p><p class="post__baslik">saldırı, 1–12 Ekim. Mor olan 136’sı zeytin hasadıyla bağlantılı.</p>
      <div class="post__alan">{cells}</div></div>
      <div class="post__alt post__alt--kaynak"><span class="post__bag"></span><span>Duvar ve Yerleşim Karşıtı Komisyon<br>ön sayım, 12 Ekim 2026</span></div>
    </div><figcaption>Rakam · 1080 × 1350</figcaption></figure>'''
    pp = pafta(TODAY_ITEMS, cls='post-pafta', title_id='post-pafta-b', interactive=False, size=50)
    p_harita = f'''<figure class="post-kap"><div class="post post--harita" style="aspect-ratio:4/5">
      {post_ust()}
      <div class="post__govde"><p class="post__baslik">Batı Şeria’da bugün {len([i for i in TODAY_ITEMS if i["region"] in ("batı-şeria", "kudüs")])} kayıt</p><p class="post__yer">Günün paftası · {date_tr(G["TODAY"])}</p></div>
      <div class="post__harita"><span class="sr" id="post-pafta-b">Günün paftası</span>{pp}</div>
    </div><figcaption>Günün paftası · 1080 × 1350</figcaption></figure>'''
    p_hikaye = f'''<figure class="post-kap post-kap--dar"><div class="post post--hikaye" style="aspect-ratio:9/16">
      {post_ust()}
      <div class="post__govde"><span class="post__dev-isaret">{isr("kapi")}</span><p class="post__baslik">{T(f07["headline_tr"])}</p><p class="post__yer">{T(place_label(f07))} · {saat(f07["time"])}</p>
      <p class="post__sayi"><b class="num">7</b> giriş demir kapıyla kapalı<br><b class="num">2</b>. gün</p></div>
      <div class="post__alt">{locator(f07["lat"], f07["lon"], "post__konum")}<span>Kaynak: WAFA · Tekua Belediyesi</span></div>
    </div><figcaption>Hikâye · 1080 × 1920</figcaption></figure>'''
    p_x = f'''<figure class="post-kap post-kap--genis"><div class="post post--yatay" style="aspect-ratio:16/9">
      <div class="post__foto">{img("p07", "", "40vw")}<span class="post__arsiv">Arşiv</span></div>
      <div class="post__govde">{post_ust()}<p class="post__baslik">{T(f16["headline_tr"])}</p><p class="post__yer">{T(place_label(f16))} · {saat(f16["time"])}</p><p class="post__kucuk">Kaynak: WAFA · {credit("p07")}</p></div>
    </div><figcaption>X ve Telegram kartı · 1600 × 900</figcaption></figure>'''
    cover_syms = [('baskin', 'Baskın'), ('gozalti', 'Gözaltı'), ('yerlesimci', 'Yerleşimci saldırısı'), ('zeytin', 'Zeytin hasadı'), ('yikim', 'Yıkım'), ('kapi', 'Kapalı kapı'), ('esir', 'Esir'), ('aksa', 'Mescid-i Aksa')]
    profil = f'''<figure class="profil"><div class="profil__kapak"><div class="kapak-bant">
        <div class="kapak-bant__cetvel" aria-hidden="true">{''.join(f'<i style="left:{k / 24 * 100:.2f}%"></i>' for k in range(25))}</div>
        <p class="kapak-bant__soz">Her haber bir yer,<br>her yer bir işaret.</p>
        <ul class="kapak-bant__lejant">{''.join(f'<li>{isr(s_, "bugun")}<span>{t_}</span></li>' for s_, t_ in cover_syms)}</ul>
      </div></div>
      <div class="profil__alt"><img class="profil__foto" src="assets/brand/isaret-avatar.svg?v={G["V"]}" alt="Profil fotoğrafı: mor zemin üzerinde beyaz nirengi işareti" width="96" height="96">
      <div><p class="profil__ad">Filistin Ajansı</p><p class="profil__kul">@hesap-adı</p><p class="profil__bio">Filistin’in ve Batı Şeria’nın haberleri, Türkçe. Her haber yeriyle, saatiyle ve kaynağıyla.</p></div></div>
      <figcaption>Profil fotoğrafı ve kapak · kapak 1500 × 500. Hesap adı henüz yok; yer tutucu.</figcaption></figure>'''
    out.append(section('sosyal', 'Sosyal medya', 'Her şablon aynı lejantı konuşur: işaret, yer, saat, kaynak. Örnekler 14 Ekim 2026’nın gerçek kayıtlarıyla dizildi.', f'''
{profil}
<div class="postlar">{p_sondakika}{p_haber}{p_rakam}{p_harita}</div>
<div class="postlar postlar--ikinci">{p_hikaye}{p_x}</div>'''))

    # ---------- applications ----------
    f_kal = 'p23'
    out.append(section('uygulama', 'Uygulamalar', 'Sahada ve ekranda: basın kartı, mikrofon küpü ve video alt bandı.', f'''
<div class="uygulamalar">
  <figure class="basin-kart-kap"><div class="basin-kart">
    <div class="basin-kart__ust">{logo_svg('basin-kart__logo')}<span class="yer yer--ink">Basın · Press</span></div>
    <div class="basin-kart__govde"><div class="basin-kart__foto" aria-hidden="true"><svg viewBox="0 0 60 72"><path d="M30 8V64M2 36H58"/><circle cx="30" cy="36" r="10"/></svg></div>
    <dl><div><dt>Ad Soyad</dt><dd>[Muhabir adı]</dd></div><div><dt>Görev</dt><dd>Muhabir · Batı Şeria masası</dd></div><div><dt>Kart no.</dt><dd class="num">FA-0000</dd></div></dl></div>
    <div class="basin-kart__alt"><span class="olcek__cubuk" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span></div>
  </div><figcaption>Basın kartı · 85,6 × 54 mm. Ad ve numara yer tutucudur.</figcaption></figure>
  <figure class="kup-kap"><div class="kup"><span class="kup__yuz kup__yuz--mor">{mark_svg('kup__isaret', size_box=False, ink='#fff')}</span><span class="kup__yuz">{logo_svg('kup__logo')}</span></div><figcaption>Mikrofon küpü · dört yüz, ikisi mor işaret, ikisi logo.</figcaption></figure>
  <figure class="altbant-kap"><div class="altbant" style="aspect-ratio:16/9">{img(f_kal, "altbant__foto", "50vw")}
    <div class="altbant__bant"><span class="altbant__isaret">{isr('kontrol', 'bugun')}</span><div><p class="yer">Kudüs–Ramallah · Kalandiya</p><p class="altbant__baslik">Kontrol noktasında sabah kuyruğu</p></div><span class="altbant__marka">{mark_svg('altbant__nirengi')}</span></div>
    <span class="altbant__arsiv">Arşiv · {e(pid[f_kal].get("author", ""))} · {e(pid[f_kal].get("license", ""))}</span>
  </div><figcaption>Video alt bandı · 1920 × 1080. Bant lejant satırıdır: işaret, yer, başlık. Örnek başlık arşiv karesini anlatır.</figcaption></figure>
</div>'''))

    # ---------- downloads ----------
    brand_dir = P('assets', 'brand')
    lst = sorted(f for f in os.listdir(brand_dir) if f.endswith(('.svg', '.png', '.zip')))
    links = ''.join(f'<li><a href="assets/brand/{f}" download>{f}</a><span class="kaynak num">{os.path.getsize(os.path.join(brand_dir, f)) / 1024:.1f} KB</span></li>' for f in lst)
    out.append(section('indir', 'İndir', 'Logolar SVG olarak, profil fotoğrafı PNG olarak. Bütün paket tek dosyada.', f'''
<ul class="indir-listesi">{links}</ul>'''))

    body = ''.join(out)
    body = body.rstrip().removesuffix('<hr class="kat">')
    tpl = open(P('tools', 'tpl', 'index.html'), encoding='utf-8').read()
    rep = {'V': G['V'], 'LEJANT': G['part']('lejant.html'), 'LOGO': logo_svg('logo-svg', 'Filistin Ajansı'), 'TOCNAV': tocnav,
           'TEMA': ui('gece', 'tema-gece') + ui('gunduz', 'tema-gunduz'), 'BODY': body, 'ALT': G['alt']()}
    html_out = re.sub(r'\{\{(\w+)\}\}', lambda mm: rep[mm.group(1)], tpl)
    html_out = html_out.replace('<!doctype html>', '<!doctype html>\n<!-- generated by tools/build.py (tools/kilavuz.py) from tools/tpl/index.html — do not edit by hand -->', 1)
    open(P('index.html'), 'w', encoding='utf-8').write(html_out)
    return len(html_out)
