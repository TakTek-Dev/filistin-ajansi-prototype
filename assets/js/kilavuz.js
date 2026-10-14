/* Filistin Ajansı — identity guide: replays the nirengi on the cover, draws the three sight
   lines of the static diagram, and replays the overprint on the demo sheet. */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var cover = document.querySelector('.kapak__logo-kutu');
  var running = null;

  function playCover() {
    if (!cover || !window.FA_nirengi || !Element.prototype.animate || reduce) return;
    if (running) running.anims.forEach(function (a) { try { a.cancel(); } catch (e) {} });
    running = window.FA_nirengi(cover);
  }

  // the static «three known points» diagram: dashed sight lines from the İ dots to the nirengi
  function sightLines() {
    document.querySelectorAll('.ucnokta').forEach(function (box) {
      var svg = box.querySelector('.ucnokta__isin');
      var logo = box.querySelector('.ucnokta__logo');
      var r0 = svg.getBoundingClientRect();
      svg.setAttribute('viewBox', '0 0 ' + r0.width + ' ' + r0.height);
      function c(el) { var r = el.getBoundingClientRect(); return [r.left + r.width / 2 - r0.left, r.top + r.height / 2 - r0.top]; }
      var t = c(logo.querySelector('.l-nokta'));
      svg.innerHTML = '';
      logo.querySelectorAll('.l-dot:not(.l-nokta)').forEach(function (d) {
        var p = c(d);
        var l = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        l.setAttribute('x1', p[0]); l.setAttribute('y1', p[1]); l.setAttribute('x2', t[0]); l.setAttribute('y2', t[1]);
        svg.appendChild(l);
      });
    });
  }

  function overprint() {
    if (reduce) return;
    var marks = Array.prototype.slice.call(document.querySelectorAll('.demo-pafta__svg .nokta.bugun')).reverse();
    marks.forEach(function (n, i) {
      n.classList.remove('is-baski');
      void n.getBoundingClientRect();
      n.style.animationDelay = (i * 55) + 'ms';
      n.classList.add('is-baski');
    });
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-oynat]');
    if (!b) return;
    if (b.dataset.oynat === 'kapak') {
      if (cover) cover.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
      setTimeout(playCover, reduce ? 0 : 380);
    } else if (b.dataset.oynat === 'baski') {
      overprint();
    }
  });

  function start() { sightLines(); playCover(); }
  if (document.readyState === 'complete') start(); else window.addEventListener('load', start);
  var rt;
  window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(sightLines, 120); });
})();
