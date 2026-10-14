/* Filistin Ajansı — homepage behaviour.
   1. Overprint: today's symbols are printed onto the sheet in the order they came in (once per session).
   2. Leader lines: a report in the feed points to its place on the sheet, and back.
   3. Legend as filter: the legend narrows the sheet and the feed to one kind of report.
   4. Latitude ruler: walking the West Bank north to south moves the marker down the ruler. */
(function () {
  'use strict';
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ilk = document.querySelector('.ilk');
  var pafta = document.getElementById('pafta');
  if (!ilk || !pafta) return;
  var noktalar = Array.prototype.slice.call(pafta.querySelectorAll('.nokta'));
  var byId = {};
  noktalar.forEach(function (n) { byId[n.dataset.id] = n; });

  /* ---------- 1. overprint ---------- */
  function overprint() {
    root.classList.remove('baski-bekle');
    var seen = false;
    try { seen = sessionStorage.getItem('fa-baski') === '1'; sessionStorage.setItem('fa-baski', '1'); } catch (e) {}
    if (reduce || seen) return;
    var today = noktalar.filter(function (n) { return n.classList.contains('bugun'); });
    // the feed order is newest first; print oldest first
    today.reverse().forEach(function (n, i) {
      n.style.animationDelay = (i * 55) + 'ms';
      n.classList.add('is-baski');
      n.addEventListener('animationend', function () { n.classList.remove('is-baski'); n.style.animationDelay = ''; }, { once: true });
    });
  }
  (window.FA_whenReady || function (f) { f(); })(overprint);

  /* ---------- 2. leader lines ---------- */
  var lider = ilk.querySelector('.lider');
  var lpath = lider && lider.querySelector('path');
  var ldot = lider && lider.querySelector('circle');
  var wide = window.matchMedia('(min-width: 761px)');
  var activeKayit = null, activeNokta = null;

  function rel(r) {
    var b = ilk.getBoundingClientRect();
    return { x: r.left - b.left, y: r.top - b.top, w: r.width, h: r.height };
  }
  function drawLeader(fromEl, toEl) {
    if (!lider || !wide.matches) return;
    var a = rel(fromEl.getBoundingClientRect());
    var b = rel(toEl.getBoundingClientRect());
    var sx = a.x + a.w + 6, sy = a.y + a.h / 2;
    var ex = b.x + b.w / 2, ey = b.y + b.h / 2;
    var shoulder = Math.min(sx + 22, ex);
    var d = 'M' + sx + ' ' + sy + 'H' + shoulder + 'L' + ex + ' ' + ey;
    lpath.setAttribute('d', d);
    ldot.setAttribute('cx', ex); ldot.setAttribute('cy', ey);
    var len = lpath.getTotalLength();
    lpath.style.transition = 'none';
    lpath.style.strokeDasharray = len; lpath.style.strokeDashoffset = reduce ? 0 : len;
    lider.classList.add('is-acik');
    lpath.getBoundingClientRect();
    lpath.style.transition = 'stroke-dashoffset .32s cubic-bezier(.16,1,.3,1)';
    lpath.style.strokeDashoffset = 0;
  }
  function clearLeader() {
    if (lider) lider.classList.remove('is-acik');
    if (activeKayit) activeKayit.classList.remove('is-aktif');
    if (activeNokta) activeNokta.classList.remove('is-aktif');
    activeKayit = activeNokta = null;
  }
  function link(kayit, nokta, fromMap) {
    clearLeader();
    if (!kayit || !nokta || nokta.classList.contains('is-gizli')) return;
    activeKayit = kayit; activeNokta = nokta;
    kayit.classList.add('is-aktif'); nokta.classList.add('is-aktif');
    var icon = kayit.querySelector(':scope > .isr');
    var mark = nokta.querySelector('.nokta__isr');
    if (icon && mark && !kayit.closest('details:not([open])')) drawLeader(icon, mark);
  }
  var akis = ilk.querySelector('.akis');
  if (akis) {
    akis.addEventListener('pointerover', function (ev) {
      var k = ev.target.closest('.kayit');
      if (k && k !== activeKayit) link(k, byId[k.dataset.id]);
    });
    akis.addEventListener('pointerleave', clearLeader);
    akis.addEventListener('focusin', function (ev) {
      var k = ev.target.closest('.kayit');
      if (k) link(k, byId[k.dataset.id]);
    });
    akis.addEventListener('focusout', function (ev) { if (!akis.contains(ev.relatedTarget)) clearLeader(); });
  }
  noktalar.forEach(function (n) {
    var k = document.getElementById('k-' + n.dataset.id);
    function on() { if (k) link(k, n, true); else { clearLeader(); n.classList.add('is-aktif'); activeNokta = n; } }
    n.addEventListener('pointerenter', on);
    n.addEventListener('focus', on);
    n.addEventListener('pointerleave', clearLeader);
    n.addEventListener('blur', clearLeader);
    if (k) n.addEventListener('click', function (ev) {
      ev.preventDefault();
      var det = k.closest('details');
      if (det) det.open = true;
      k.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
      var a = k.querySelector('a'); if (a) a.focus({ preventScroll: true });
    });
  });
  window.addEventListener('resize', clearLeader);
  window.addEventListener('scroll', function () { if (activeKayit && activeNokta) link(activeKayit, activeNokta); }, { passive: true });

  /* ---------- 3. legend as filter ---------- */
  var lejant = ilk.querySelector('.lejant');
  var kayitlar = Array.prototype.slice.call(akis ? akis.querySelectorAll('.kayit') : []);
  var bos = akis && akis.querySelector('.akis__bos');
  var details = akis && akis.querySelector('.akis__devam');
  function filter(cat) {
    clearLeader();
    lejant.querySelectorAll('[data-filtre]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.filtre === cat)); });
    if (cat) lejant.setAttribute('data-aktif', cat); else lejant.removeAttribute('data-aktif');
    noktalar.forEach(function (n) { n.classList.toggle('is-gizli', !!cat && n.dataset.cat !== cat); });
    var shown = 0, inRest = 0;
    kayitlar.forEach(function (k) {
      var hide = !!cat && k.dataset.cat !== cat;
      k.hidden = hide;
      if (!hide) { shown++; if (k.closest('details')) inRest++; }
    });
    if (details) { details.hidden = !!cat && inRest === 0; if (cat && inRest) details.open = true; }
    if (bos) bos.hidden = shown > 0;
  }
  if (lejant) {
    lejant.addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-filtre]');
      if (!b) return;
      filter(b.getAttribute('aria-pressed') === 'true' ? null : b.dataset.filtre);
    });
  }
  if (bos) bos.addEventListener('click', function (ev) { if (ev.target.closest('[data-filtre-sifirla]')) filter(null); });
  // links further down the page («today's olive-harvest records») jump back to the sheet, filtered
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest('[data-filtre-git]');
    if (!a || !lejant) return;
    ev.preventDefault();
    filter(a.dataset.filtreGit);
    lejant.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    var b = lejant.querySelector('[aria-pressed="true"]'); if (b) b.focus({ preventScroll: true });
  });

  /* ---------- 4. latitude ruler ---------- */
  var imlec = document.querySelector('.enlem__imlec');
  var rows = Array.prototype.slice.call(document.querySelectorAll('.il[data-lat]'));
  if (imlec && rows.length && 'IntersectionObserver' in window) {
    var TOP = 32.55, SPAN = 1.2;
    function dms(lat) { var d = Math.floor(lat), m = Math.round((lat - d) * 60); if (m === 60) { d++; m = 0; } return d + '°' + (m < 10 ? '0' : '') + m + '′ K'; }
    function set(row) {
      rows.forEach(function (r) { r.classList.toggle('is-burada', r === row); });
      var lat = parseFloat(row.dataset.lat);
      var pct = Math.max(0, Math.min(100, (TOP - lat) / SPAN * 100));
      imlec.style.top = pct + '%';
      imlec.querySelector('b').textContent = dms(lat);
      imlec.querySelector('i').textContent = row.querySelector('.il__ad').textContent;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) set(en.target); });
    }, { rootMargin: '-35% 0px -60% 0px' });
    rows.forEach(function (r) { io.observe(r); });
    set(rows[0]);
  }
})();
