(function () {
  'use strict';

  // Per-lawyer settings. Everything else on the page is plain HTML.
  var CONFIG = {
    whatsapp: '201140118038', // international format, no "+"
    defaultMessage: 'السلام عليكم، أرغب في الاستفسار عن خدمات المكتب.',
    timezone: 'Africa/Cairo'
  };

  function waUrl(text) {
    return 'https://wa.me/' + CONFIG.whatsapp + '?text=' + encodeURIComponent(text);
  }

  document.querySelectorAll('[data-wa]').forEach(function (el) {
    el.setAttribute('href', waUrl(el.getAttribute('data-msg') || CONFIG.defaultMessage));
    el.setAttribute('target', '_blank');
    el.setAttribute('rel', 'noopener');
  });

  // WhatsApp-only contact form.
  var form = document.getElementById('waForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = form.elements.name;
      if (!name.value.trim()) {
        name.classList.add('invalid');
        name.focus();
        return;
      }
      var text = 'السلام عليكم،\nالاسم: ' + name.value.trim() + '\nنوع القضية: ' + form.elements.type.value;
      var msg = form.elements.msg.value.trim();
      if (msg) text += '\nالتفاصيل: ' + msg;
      window.open(waUrl(text), '_blank', 'noopener');
    });
    form.elements.name.addEventListener('input', function () { this.classList.remove('invalid'); });
  }

  // Mobile menu.
  var toggle = document.getElementById('menuToggle');
  var nav = document.getElementById('nav');
  if (toggle && nav) {
    var setOpen = function (open) {
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
    };
    toggle.addEventListener('click', function () { setOpen(!nav.classList.contains('open')); });
    nav.addEventListener('click', function (e) { if (e.target.tagName === 'A') setOpen(false); });
  }

  // Hero portrait: show it only when the file exists, so the page works before the photo is added.
  var photo = document.getElementById('heroPhoto');
  var hero = document.getElementById('hero');
  if (photo && hero) {
    var show = function () { photo.hidden = false; hero.classList.add('has-photo'); };
    if (photo.complete && photo.naturalWidth) show();
    else photo.addEventListener('load', show);
  }

  // Services carousel arrows (the page is RTL, so "next" scrolls toward negative X).
  var track = document.getElementById('svcTrack');
  var next = document.getElementById('svcNext');
  var prev = document.getElementById('svcPrev');
  if (track && next && prev) {
    var step = function () { var c = track.querySelector('.svc-card'); return c ? c.getBoundingClientRect().width + 18 : 300; };
    next.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: 'smooth' }); });
    prev.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: 'smooth' }); });
  }

  // Opening hours: highlight today's row (Cairo time). The office is closed on Friday only.
  function cairoDay() {
    try {
      var w = new Intl.DateTimeFormat('en-US', { timeZone: CONFIG.timezone, weekday: 'short' }).format(new Date());
      return { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }[w];
    } catch (err) {
      return new Date().getDay();
    }
  }
  var today = document.querySelector('#hoursList [data-day="' + cairoDay() + '"]');
  if (today) {
    today.classList.add('today');
    var s = today.querySelector('.s');
    if (s && !today.classList.contains('off')) s.textContent = 'اليوم';
  }

  var year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();
})();
