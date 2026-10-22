/* Filistin Ajansı — site behaviour. Homepage: menu sheet, the «Bugün neler oldu?» crawl, the manşet carousel,
   the paged Son Dakika list, the photo carousel. Inner pages: forms, story reading progress, text size and
   sharing, the Son Dakika region filter, the photo viewer and search. Plus the logo preview switcher.
   Every page reads without JavaScript except search; motion stops for reduced-motion users. */
(function () {
  'use strict';
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function $(s, c) { return (c || document).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); }

  /* ---------- menu sheet ---------- */
  var sheet = document.getElementById('cekmece');
  var opener = $('[data-menu]');
  function closeSheet() {
    if (!sheet || sheet.hidden) return;
    sheet.hidden = true;
    document.body.style.overflow = '';
    if (opener) { opener.setAttribute('aria-expanded', 'false'); opener.focus(); }
  }
  if (sheet && opener) {
    opener.addEventListener('click', function () {
      sheet.hidden = false;
      document.body.style.overflow = 'hidden';
      opener.setAttribute('aria-expanded', 'true');
      var a = $('nav a', sheet); if (a) a.focus();
    });
    sheet.addEventListener('click', function (ev) { if (ev.target.closest('[data-kapat]')) closeSheet(); });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') closeSheet(); });
  }

  /* ---------- «Bugün neler oldu?» crawl: pause control ---------- */
  var gundem = $('.gundem'), serBtn = $('[data-serit-dur]');
  if (gundem && serBtn) {
    if (reduce) serBtn.hidden = true;
    serBtn.addEventListener('click', function () {
      var off = gundem.hasAttribute('data-durdu');
      if (off) gundem.removeAttribute('data-durdu'); else gundem.setAttribute('data-durdu', '');
      serBtn.setAttribute('aria-label', off ? 'Kayan başlıkları durdur' : 'Kayan başlıkları başlat');
    });
  }

  /* ---------- manşet carousel ----------
     The red progress bar is the clock: when its animation ends, the next slide comes in.
     Hover or focus freezes the bar (and the slow zoom); the pause button stops it for good. */
  var car = $('[data-karusel]');
  if (car) {
    var slides = $$('.manset__slayt', car);
    var dots = $$('[data-slayt]', car);
    var bar = $('.manset__ilerleme i', car);
    var stage = $('.manset__sahne', car);
    var pauseBtn = $('[data-dur]', car);
    var cur = 0, paused = reduce;
    function restartBar() {
      car.classList.remove('is-oynuyor');
      void bar.offsetWidth;                          // restart the CSS animation
      if (!paused) car.classList.add('is-oynuyor');
    }
    function show(i, focus) {
      cur = (i + slides.length) % slides.length;
      slides.forEach(function (s, k) {
        var on = k === cur;
        s.classList.toggle('is-aktif', on);
        if (on) s.removeAttribute('aria-hidden'); else s.setAttribute('aria-hidden', 'true');
        $$('a', s).forEach(function (a) { a.tabIndex = on ? 0 : -1; });
      });
      dots.forEach(function (d, k) { if (k === cur) d.setAttribute('aria-current', 'true'); else d.removeAttribute('aria-current'); });
      if (focus) { var a = $('a', slides[cur]); if (a) a.focus({ preventScroll: true }); }
      restartBar();
    }
    bar.addEventListener('animationend', function () { if (!paused) show(cur + 1); });
    function setPaused(p) {
      paused = p;
      if (p) { car.setAttribute('data-durdu', ''); car.classList.remove('is-oynuyor'); }
      else { car.removeAttribute('data-durdu'); restartBar(); }
      pauseBtn.setAttribute('aria-label', p ? 'Otomatik geçişi başlat' : 'Otomatik geçişi durdur');
    }
    dots.forEach(function (d, k) { d.addEventListener('click', function () { show(k); }); });
    $('[data-onceki]', car).addEventListener('click', function () { show(cur - 1); });
    $('[data-sonraki]', car).addEventListener('click', function () { show(cur + 1); });
    pauseBtn.addEventListener('click', function () { setPaused(!paused); });
    car.addEventListener('pointerenter', function () { car.classList.add('is-bekle'); });
    car.addEventListener('pointerleave', function () { car.classList.remove('is-bekle'); });
    car.addEventListener('focusin', function () { car.classList.add('is-bekle'); });
    car.addEventListener('focusout', function (ev) { if (!car.contains(ev.relatedTarget)) car.classList.remove('is-bekle'); });
    car.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight') { show(cur + 1, true); ev.preventDefault(); }
      if (ev.key === 'ArrowLeft') { show(cur - 1, true); ev.preventDefault(); }
    });
    // drag or swipe the stage (mouse and touch); a real drag never opens the story link
    var x0 = null, moved = false;
    stage.addEventListener('pointerdown', function (ev) { if (ev.button !== 0) return; x0 = ev.clientX; moved = false; });
    stage.addEventListener('pointermove', function (ev) { if (x0 !== null && Math.abs(ev.clientX - x0) > 8) moved = true; });
    stage.addEventListener('pointerup', function (ev) {
      if (x0 === null) return;
      var dx = ev.clientX - x0; x0 = null;
      if (Math.abs(dx) > 50) show(cur + (dx < 0 ? 1 : -1));
    });
    stage.addEventListener('click', function (ev) { if (moved) { ev.preventDefault(); moved = false; } }, true);
    stage.addEventListener('dragstart', function (ev) { ev.preventDefault(); });
    document.addEventListener('visibilitychange', function () { car.classList.toggle('is-bekle', document.hidden); });
    if (reduce) setPaused(true);
    show(0);
  }

  /* ---------- Son Dakika: rows sized to the space, paged with a slide ---------- */
  var son = $('[data-son]');
  if (son) {
    var win = $('.son__pencere', son), list = $('.son__liste', son), rows = $$('li', list);
    var label = $('.son__sayfa', son), up = $('[data-son-geri]', son), down = $('[data-son-ileri]', son);
    var per = 5, page = 0, pages = 1, timer = null, hold = false;
    function layout() {
      win.style.removeProperty('--satir');
      var h = win.clientHeight;
      per = Math.max(3, Math.floor(h / 76));
      win.style.setProperty('--satir', (h / per) + 'px');
      pages = Math.ceil(rows.length / per);
      go(Math.min(page, pages - 1));
    }
    function go(p) {
      page = (p + pages) % pages;
      var rowH = parseFloat(getComputedStyle(win).getPropertyValue('--satir')) || 76;
      list.style.transform = 'translateY(' + (-page * per * rowH) + 'px)';
      rows.forEach(function (r, k) { var vis = k >= page * per && k < (page + 1) * per; $$('a', r).forEach(function (a) { a.tabIndex = vis ? 0 : -1; }); r.setAttribute('aria-hidden', String(!vis)); });
      label.textContent = (page + 1) + ' / ' + pages;
    }
    function tick() { clearInterval(timer); if (!reduce) timer = setInterval(function () { if (!hold) go(page + 1); }, 8000); }
    up.addEventListener('click', function () { go(page - 1); tick(); });
    down.addEventListener('click', function () { go(page + 1); tick(); });
    son.addEventListener('pointerenter', function () { hold = true; });
    son.addEventListener('pointerleave', function () { hold = false; });
    son.addEventListener('focusin', function () { hold = true; });
    son.addEventListener('focusout', function (ev) { if (!son.contains(ev.relatedTarget)) hold = false; });
    var rz; window.addEventListener('resize', function () { clearTimeout(rz); rz = setTimeout(layout, 120); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(layout);
    layout(); tick();
  }

  /* ---------- photo carousel ---------- */
  var gal = $('[data-galeri]');
  if (gal) {
    var track = $('.galeri__serit', gal), items = $$('.galeri__oge', track);
    var back = $('[data-galeri-geri]', gal), fwd = $('[data-galeri-ileri]', gal), count = $('.galeri__sayac', gal);
    function step() { return items.length > 1 ? items[1].offsetLeft - items[0].offsetLeft : track.clientWidth; }
    function update() {
      var i = Math.round(track.scrollLeft / step());
      count.textContent = Math.min(i + 1, items.length) + ' / ' + items.length;
      back.disabled = track.scrollLeft <= 2;
      fwd.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
    }
    back.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: reduce ? 'auto' : 'smooth' }); });
    fwd.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: reduce ? 'auto' : 'smooth' }); });
    track.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  /* ---------- newsletter and contact forms: the prototype sends nothing, and says so ---------- */
  $$('.bulten__form').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var input = $('input', form), out = $('.bulten__durum', form);
      if (!input.checkValidity() || !input.value) { out.textContent = 'Geçerli bir e-posta adresi yazın: ad@ornek.com gibi.'; input.focus(); return; }
      out.textContent = 'Teşekkürler. Bu prototip e-posta göndermez; bülten canlı sitede açılacak.';
    });
  });
  $$('form[data-prototip]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var out = $('.form__durum', form), bad = null;
      $$('[required]', form).forEach(function (el) {
        var ok = el.type === 'checkbox' ? el.checked : el.checkValidity() && el.value.trim() !== '';
        el.setAttribute('aria-invalid', String(!ok));
        if (!ok && !bad) bad = el;
      });
      if (bad) { out.textContent = 'Lütfen işaretli alanları doldurun.'; bad.focus(); return; }
      out.textContent = 'Teşekkürler. Bu prototip mesaj göndermez; form canlı sitede çalışacak.';
    });
  });

  /* ---------- story page: reading progress, text size, share ---------- */
  var article = $('[data-haber]'), okuma = $('.okuma');
  if (article && okuma) {
    var queued = false;
    function readProgress() {
      queued = false;
      var r = article.getBoundingClientRect();
      var span = Math.max(r.height - window.innerHeight * 0.6, 1);
      okuma.style.setProperty('--okuma', Math.min(1, Math.max(0, -r.top / span)).toFixed(4));
    }
    window.addEventListener('scroll', function () { if (!queued) { queued = true; requestAnimationFrame(readProgress); } }, { passive: true });
    window.addEventListener('resize', readProgress);
    readProgress();
  }
  var metin = $('.haber__metin'), sizeBtns = $$('[data-yazi]');
  if (metin && sizeBtns.length) {
    var steps = [1, 1.125, 1.25, 1.375], step = 1;
    function applySize(set) {
      if (set) metin.style.setProperty('--yazi', steps[step] + 'rem');
      sizeBtns.forEach(function (btn) { var d = +btn.dataset.yazi; btn.disabled = (d < 0 && step === 0) || (d > 0 && step === steps.length - 1); });
    }
    try { var saved = parseInt(localStorage.getItem('fa-yazi'), 10); if (saved >= 0 && saved < steps.length) { step = saved; applySize(true); } } catch (e) {}
    sizeBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        step = Math.min(steps.length - 1, Math.max(0, step + (+btn.dataset.yazi)));
        try { localStorage.setItem('fa-yazi', String(step)); } catch (e) {}
        applySize(true);
      });
    });
    applySize(false);
  }
  var copyBtn = $('[data-kopyala]'), shareBtn = $('[data-paylas]'), shareOut = $('.paylas__durum');
  function shareSay(msg) {
    if (!shareOut) return;
    shareOut.textContent = msg; shareOut.classList.add('is-gorunur');
    clearTimeout(shareSay.t);
    shareSay.t = setTimeout(function () { shareOut.classList.remove('is-gorunur'); }, 2200);
  }
  if (copyBtn) copyBtn.addEventListener('click', function () {
    var url = location.href.split('#')[0];
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(function () { shareSay('Bağlantı kopyalandı'); }, function () { shareSay('Kopyalanamadı'); });
    else shareSay('Kopyalanamadı');
  });
  if (shareBtn && navigator.share) {
    shareBtn.hidden = false;
    shareBtn.addEventListener('click', function () { navigator.share({ title: document.title, url: location.href.split('#')[0] }).catch(function () {}); });
  }

  /* ---------- Son Dakika: filter by region (kept in the address as ?bolge=) ---------- */
  var suz = $('[data-suz]');
  if (suz) {
    var suzAlan = $('[data-suz-alan]'), suzDurum = $('.suz__durum'), suzChips = $$('[data-bolge]', suz);
    function suzGoster(bolge, write) {
      suzChips.forEach(function (c) { c.setAttribute('aria-pressed', String(c.dataset.bolge === bolge)); });
      var n = 0;
      $$('.gun', suzAlan).forEach(function (g) {
        var any = false;
        $$('.akis__oge', g).forEach(function (li) { var on = !bolge || li.dataset.bolge === bolge; li.hidden = !on; if (on) { any = true; n++; } });
        g.hidden = !any;
      });
      if (suzDurum) suzDurum.textContent = n + ' haber gösteriliyor';
      if (write) {
        var u = new URL(location.href);
        if (bolge) u.searchParams.set('bolge', bolge); else u.searchParams.delete('bolge');
        history.replaceState(null, '', u);
      }
    }
    suzChips.forEach(function (c) { c.addEventListener('click', function () { suzGoster(c.dataset.bolge, true); }); });
    var b0 = new URLSearchParams(location.search).get('bolge');
    if (b0 && suzChips.some(function (c) { return c.dataset.bolge === b0; })) suzGoster(b0, false);
  }

  /* ---------- photo viewer (galeri.html) ---------- */
  var isik = $('[data-isik-kutu]');
  if (isik && typeof isik.showModal === 'function') {
    var openers = $$('[data-isik]'), ix = 0, lastOpener = null;
    var isikImg = $('.isik__resim', isik), isikAlt = $('.isik__alt', isik), isikSay = $('.isik__sayac', isik);
    function isikGoster(i) {
      ix = (i + openers.length) % openers.length;
      var btn = openers[ix];
      isikImg.src = btn.dataset.buyuk;
      isikImg.alt = $('img', btn).alt;
      isikAlt.innerHTML = btn.closest('figure').querySelector('figcaption').innerHTML;   // the page's own caption markup
      isikSay.textContent = (ix + 1) + ' / ' + openers.length;
    }
    openers.forEach(function (btn, i) { btn.addEventListener('click', function () { lastOpener = btn; isikGoster(i); isik.showModal(); }); });
    $('[data-isik-kapat]', isik).addEventListener('click', function () { isik.close(); });
    $('[data-isik-geri]', isik).addEventListener('click', function () { isikGoster(ix - 1); });
    $('[data-isik-ileri]', isik).addEventListener('click', function () { isikGoster(ix + 1); });
    isik.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight') { isikGoster(ix + 1); ev.preventDefault(); }
      if (ev.key === 'ArrowLeft') { isikGoster(ix - 1); ev.preventDefault(); }
    });
    isik.addEventListener('click', function (ev) { if (ev.target === isik || ev.target.classList.contains('isik__sahne')) isik.close(); });
    var sx = null;
    isik.addEventListener('pointerdown', function (ev) { sx = ev.clientX; });
    isik.addEventListener('pointerup', function (ev) { if (sx === null) return; var dx = ev.clientX - sx; sx = null; if (Math.abs(dx) > 60) isikGoster(ix + (dx < 0 ? 1 : -1)); });
    isik.addEventListener('close', function () { isikImg.removeAttribute('src'); if (lastOpener) lastOpener.focus(); });
  }

  /* ---------- search (arama.html): words, region and topic, all in the address ---------- */
  var araForm = $('[data-ara]');
  if (araForm) {
    var araInput = $('input', araForm), araSonuc = $('[data-ara-sonuc]'), araDurum = $('[data-ara-durum]'), araOneri = $('[data-ara-oneri]');
    var araChips = $$('[data-ara-bolge] [data-bolge]'), araFiltre = $('[data-ara-filtre]');
    var qs = new URLSearchParams(location.search);
    var st = { q: qs.get('q') || '', bolge: qs.get('bolge') || '', konu: qs.get('konu') || '' };
    var veri = null, KONU = {};
    var TRS = 'çğıöşüâîû', ASC = 'cgiosuaiu';
    function norm(s) {
      return String(s || '').toLocaleLowerCase('tr').replace(/[çğıöşüâîû]/g, function (c) { return ASC[TRS.indexOf(c)]; })
        .replace(/['’‘]/g, '').normalize('NFD').replace(/[̀-ͯ]/g, '');
    }
    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
    var VAR = { i: '[iİıI]', c: '[cçCÇ]', g: '[gğGĞ]', o: '[oöOÖ]', s: '[sşSŞ]', u: '[uüUÜ]', a: '[aâAÂ]' };
    function isaretle(html, toks) {
      toks.forEach(function (t) {
        if (t.length < 2) return;
        var re = new RegExp('(' + t.split('').map(function (ch) { return VAR[ch] || ch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }).join('') + ')', 'gi');
        html = html.replace(/(<[^>]*>)|([^<]+)/g, function (m, tag, text) { return tag || text.replace(re, '<mark>$1</mark>'); });
      });
      return html;
    }
    function satir(h, toks) {
      var foto = h.f ? '<span class="akis__foto"><img src="' + esc(h.f) + '" alt="" loading="lazy" decoding="async"></span>' : '';
      return '<li class="akis__oge' + (h.f ? '' : ' akis__oge--metin') + '"><time class="akis__saat" datetime="' + esc(h.d) + '">' + esc(h.z) + '</time>' +
        '<a class="akis__bag" href="' + esc(h.u) + '">' + foto + '<span class="akis__metin"><span class="etiket">' + esc(h.y) + '</span>' +
        '<span class="akis__baslik">' + isaretle(esc(h.b), toks) + '</span><span class="akis__ozet">' + isaretle(esc(h.o), toks) + '</span></span></a></li>';
    }
    function yaz() {
      var u = new URL(location.href);
      ['q', 'bolge', 'konu'].forEach(function (k) { if (st[k]) u.searchParams.set(k, st[k]); else u.searchParams.delete(k); });
      history.replaceState(null, '', u);
    }
    function ara(write) {
      var toks = norm(st.q).split(/[^a-z0-9.]+/).filter(Boolean);
      var list = veri.filter(function (h) {
        if (st.bolge && h.r !== st.bolge) return false;
        if (st.konu && h.k !== st.konu) return false;
        if (!toks.length) return true;
        var hay = h._n || (h._n = norm([h.b, h.m, h.p, h.il, h.ka, h.y].join(' ')));
        return toks.every(function (t) { return hay.indexOf(t) !== -1; });
      });
      araSonuc.innerHTML = list.map(function (h) { return satir(h, toks); }).join('');
      var bos = !toks.length && !st.bolge && !st.konu;
      araOneri.hidden = !bos && list.length > 0;
      araDurum.textContent = !list.length ? 'Sonuç bulunamadı. Başka bir kelime deneyin ya da süzgeci kaldırın.'
        : bos ? 'Bütün haberler (' + list.length + '), en yeniden eskiye' : list.length + ' haber bulundu';
      araChips.forEach(function (c) { c.setAttribute('aria-pressed', String(c.dataset.bolge === st.bolge)); });
      araFiltre.hidden = !st.konu;
      araFiltre.innerHTML = st.konu ? '<button type="button" data-konu-kaldir aria-label="Konu süzgecini kaldır: ' + esc(KONU[st.konu] || st.konu) + '">Konu: ' +
        esc(KONU[st.konu] || st.konu) + ' <svg class="ikon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button>' : '';
      if (write) yaz();
    }
    araInput.value = st.q;
    var debounce;
    araForm.addEventListener('submit', function (ev) { ev.preventDefault(); st.q = araInput.value.trim(); if (veri) ara(true); });
    araInput.addEventListener('input', function () { clearTimeout(debounce); debounce = setTimeout(function () { st.q = araInput.value.trim(); if (veri) ara(true); }, 220); });
    araChips.forEach(function (c) { c.addEventListener('click', function () { st.bolge = c.dataset.bolge; if (veri) ara(true); }); });
    araFiltre.addEventListener('click', function (ev) { if (ev.target.closest('[data-konu-kaldir]')) { st.konu = ''; ara(true); araInput.focus(); } });
    fetch('assets/data/haberler.json').then(function (r) { return r.json(); }).then(function (rows) {
      veri = rows;
      rows.forEach(function (h) { KONU[h.k] = h.ka; });
      ara(false);
    }).catch(function () { araDurum.textContent = 'Haberler yüklenemedi. Sayfayı yenileyin ya da Son Dakika sayfasına geçin.'; });
  }

  /* ---------- logo preview switcher ---------- */
  var sw = $('.secici');
  var fav = $('[data-favicon]');
  function setLogo(k, keep) {
    root.dataset.logo = k;
    if (keep) try { sessionStorage.setItem('fa-logo', k); } catch (e) {}
    if (fav) fav.href = fav.href.replace(/secenek-\d/, 'secenek-' + k);
    if (sw) $$('[data-logo-sec]', sw).forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.logoSec === k)); });
  }
  if (sw) sw.addEventListener('click', function (ev) { var b = ev.target.closest('[data-logo-sec]'); if (b) setLogo(b.dataset.logoSec, true); });
  setLogo(root.dataset.logo || '1');
})();
