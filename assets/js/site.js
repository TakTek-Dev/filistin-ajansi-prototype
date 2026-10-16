/* Filistin Ajansı — homepage behaviour: menu sheet, the «Bugün neler oldu?» crawl, the manşet
   carousel, the paged Son Dakika list, the photo carousel, the newsletter note and the logo switcher.
   Everything reads without JavaScript; motion stops for reduced-motion users. */
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

  /* ---------- newsletter: the prototype sends nothing, and says so ---------- */
  var form = $('.bulten__form');
  if (form) form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var input = $('input', form), out = $('.bulten__durum', form);
    if (!input.checkValidity() || !input.value) { out.textContent = 'Geçerli bir e-posta adresi yazın: ad@ornek.com gibi.'; input.focus(); return; }
    out.textContent = 'Teşekkürler. Bu prototip e-posta göndermez; bülten canlı sitede açılacak.';
  });

  /* ---------- logo preview switcher ---------- */
  var sw = $('.secici');
  var fav = $('[data-favicon]');
  function setLogo(k) {
    root.dataset.logo = k;
    try { localStorage.setItem('fa-logo', k); } catch (e) {}
    if (fav) fav.href = 'assets/brand/secenek-' + k + '-avatar.svg';
    if (sw) $$('[data-logo-sec]', sw).forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.logoSec === k)); });
  }
  if (sw) sw.addEventListener('click', function (ev) { var b = ev.target.closest('[data-logo-sec]'); if (b) setLogo(b.dataset.logoSec); });
  setLogo(root.dataset.logo || '1');
})();
