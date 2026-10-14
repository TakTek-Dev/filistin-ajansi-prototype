/* Filistin Ajansı — shared behaviour: theme, menu, newsletter note, and the loader.
   The loader runs once per session (or with ?loader): the three İ dots of FİLİSTİN are the
   known points; sight lines from them fix the fourth point, the nirengi; then the name
   settles into the header. Everything is visible without JavaScript. */
(function () {
  'use strict';
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- theme ---------- */
  var temaBtn = document.querySelector('[data-tema]');
  function currentTheme() {
    if (root.dataset.theme) return root.dataset.theme;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function labelTheme() {
    if (!temaBtn) return;
    var dark = currentTheme() === 'dark';
    root.classList.toggle('is-gece', dark);
    temaBtn.setAttribute('aria-label', dark ? 'Gündüz paftasına geç' : 'Gece paftasına geç');
  }
  if (temaBtn) {
    temaBtn.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      root.dataset.theme = next;
      try { localStorage.setItem('fa-tema', next); } catch (e) {}
      labelTheme();
    });
    labelTheme();
  }

  /* ---------- menu sheet ---------- */
  var cek = document.getElementById('cekmece');
  var acBtn = document.querySelector('[data-menu]');
  function closeMenu() {
    if (!cek || cek.hidden) return;
    cek.hidden = true; cek.removeAttribute('data-open');
    document.body.style.overflow = '';
    if (acBtn) { acBtn.setAttribute('aria-expanded', 'false'); acBtn.focus(); }
  }
  if (cek && acBtn) {
    acBtn.addEventListener('click', function () {
      cek.hidden = false; cek.setAttribute('data-open', '');
      document.body.style.overflow = 'hidden';
      acBtn.setAttribute('aria-expanded', 'true');
      var first = cek.querySelector('nav a');
      if (first) first.focus();
    });
    cek.addEventListener('click', function (ev) {
      if (ev.target.closest('[data-kapat]')) closeMenu();
    });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') closeMenu(); });
  }

  /* ---------- newsletter: the prototype sends nothing, and says so ---------- */
  document.querySelectorAll('.bulten').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var input = f.querySelector('input[type="email"]');
      var out = f.querySelector('.bulten__durum');
      if (!input.checkValidity()) {
        out.textContent = 'Geçerli bir e-posta adresi yazın: ad@ornek.com gibi.';
        input.focus();
        return;
      }
      out.textContent = 'Kaydınız alındı. Bu prototip e-posta göndermez; bülten canlı sitede açılacak.';
    });
  });

  /* ---------- ready signal ---------- */
  function ready() {
    root.classList.remove('yuk');
    window.FA_HAZIR = true;
    document.dispatchEvent(new CustomEvent('fa:hazir'));
  }
  window.FA_whenReady = function (fn) {
    if (window.FA_HAZIR) fn(); else document.addEventListener('fa:hazir', fn, { once: true });
  };

  /* ---------- the nirengi sequence: the loader and the guide's cover share it ---------- */
  window.FA_nirengi = function (sahne) {
  var svg = sahne.querySelector('.yukleyici__logo');
  var isin = sahne.querySelector('.yukleyici__isinlar');
  var dots = Array.prototype.slice.call(svg.querySelectorAll('.l-dot:not(.l-nokta)'));
  var nokta = svg.querySelector('.l-nokta');
  var tri = svg.querySelector('polygon');
  var rect = svg.querySelector('rect');
  var letters = svg.querySelector('g');
  var ease = 'cubic-bezier(.16,1,.3,1)';
  var anims = [];
  function A(el, kf, opt) { var a = el.animate(kf, Object.assign({ fill: 'both', easing: ease }, opt)); anims.push(a); return a; }
  isin.innerHTML = '';

  var sr = sahne.getBoundingClientRect();
  function center(el) { var r = el.getBoundingClientRect(); return [r.left + r.width / 2 - sr.left, r.top + r.height / 2 - sr.top]; }
  var target = center(nokta);
  isin.setAttribute('viewBox', '0 0 ' + sr.width + ' ' + sr.height);

  // 1. the three known points
  dots.forEach(function (d, i) {
    d.style.transformBox = 'fill-box'; d.style.transformOrigin = 'center';
    A(d, [{ transform: 'scale(0)' }, { transform: 'scale(1.35)', offset: .7 }, { transform: 'scale(1)' }], { duration: 380, delay: 80 + i * 90 });
  });
  // 2. sight lines from each known point to the unknown one
  dots.forEach(function (d, i) {
    var c = center(d);
    var l = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    l.setAttribute('x1', c[0]); l.setAttribute('y1', c[1]); l.setAttribute('x2', target[0]); l.setAttribute('y2', target[1]);
    var len = Math.hypot(target[0] - c[0], target[1] - c[1]);
    l.style.strokeDasharray = len; l.style.strokeDashoffset = len;
    isin.appendChild(l);
    A(l, [{ strokeDashoffset: len, opacity: 1 }, { strokeDashoffset: 0, opacity: 1, offset: .62 }, { strokeDashoffset: 0, opacity: 0 }], { duration: 900, delay: 420 + i * 70, easing: 'cubic-bezier(.55,0,.25,1)' });
  });
  // 3. the point is fixed
  nokta.style.transformBox = 'fill-box'; nokta.style.transformOrigin = 'center';
  A(nokta, [{ transform: 'scale(0)' }, { transform: 'scale(1.8)', offset: .55 }, { transform: 'scale(1)' }], { duration: 460, delay: 930 });
  // 4. the triangle and the key box are drawn around it
  var tl = tri.getTotalLength ? tri.getTotalLength() : 4000;
  tri.style.strokeDasharray = tl;
  A(tri, [{ strokeDashoffset: tl }, { strokeDashoffset: 0 }], { duration: 520, delay: 1080 });
  A(rect, [{ opacity: 0, transform: 'scale(.92)' }, { opacity: 1, transform: 'scale(1)' }], { duration: 420, delay: 1240 });
  rect.style.transformBox = 'fill-box'; rect.style.transformOrigin = 'center';
  // 5. the name is lettered in, left to right, like a label set on a sheet
  A(letters, [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }], { duration: 640, delay: 1200, easing: 'cubic-bezier(.65,0,.35,1)' });
  return { anims: anims, add: A };
  };

  /* ---------- loader ---------- */
  var box = document.querySelector('.yukleyici');
  if (!box || !root.classList.contains('yuk') || reduce.matches || !Element.prototype.animate) {
    if (box) box.remove();
    ready();
    return;
  }
  try { sessionStorage.setItem('fa-yuk', '1'); } catch (e) {}
  box.hidden = false;
  var sahne = box.querySelector('.yukleyici__sahne');
  var seq = window.FA_nirengi(sahne);
  var anims = seq.anims, A = seq.add;

  // 6. the lockup flies into the header logo, the paper lifts
  var headerLogo = document.querySelector('.ust .logo svg');
  var flyDelay = 2000, flyDur = 620;
  var fly = function () {
    if (headerLogo) {
      var a = sahne.getBoundingClientRect(), b = headerLogo.getBoundingClientRect();
      var s = b.width / a.width;
      var dx = b.left - a.left, dy = b.top - a.top;
      sahne.style.transformOrigin = '0 0';
      A(sahne, [{ transform: 'none' }, { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(' + s + ')' }], { duration: flyDur, easing: 'cubic-bezier(.7,0,.2,1)' });
    }
    A(box, [{ backgroundColor: getComputedStyle(box).backgroundColor }, { backgroundColor: 'transparent' }], { duration: 380, delay: flyDur * 0.45 });
    if (headerLogo) A(headerLogo, [{ opacity: 0 }, { opacity: 0, offset: .99 }, { opacity: 1 }], { duration: flyDur });
  };
  var t1 = setTimeout(fly, flyDelay);
  var t2 = setTimeout(finish, flyDelay + flyDur + 40);
  var done = false;
  function finish() {
    if (done) return; done = true;
    clearTimeout(t1); clearTimeout(t2);
    anims.forEach(function (a) { try { a.cancel(); } catch (e) {} });
    box.remove();
    ready();
  }
  // any key or click skips
  ['keydown', 'pointerdown'].forEach(function (t) { window.addEventListener(t, finish, { once: true, capture: true }); });
})();
