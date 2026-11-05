/* kattapack – Seitenlogik: Menü, Paket, Einblenden, Links, Abschnittsleiste, Strichcodes, Kopieren, Stellplatz-Rechner, Anfrageformular */
(function(){
  'use strict';

  var EMAIL = 'info@kattapack.de';
  var root = document.documentElement;
  var header = document.querySelector('.site-header');
  var mqReduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  var mqFine = window.matchMedia ? window.matchMedia('(hover: hover) and (pointer: fine)') : null;
  var reduced = function(){ return !!(mqReduce && mqReduce.matches); };
  var finePointer = function(){ return !!(mqFine && mqFine.matches); };
  var hasIO = 'IntersectionObserver' in window;

  /* ---------- Menü mit Unterpunkten ---------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  var items = nav ? Array.prototype.slice.call(nav.querySelectorAll('.nav-item')) : [];
  var mobileNav = function(){ return !!toggle && window.getComputedStyle(toggle).display !== 'none'; };
  var setItem = function(item, open){
    item.classList.toggle('open', open);
    var b = item.querySelector('.nav-more');
    if (b) b.setAttribute('aria-expanded', open ? 'true' : 'false');
  };
  var closeAll = function(except){ items.forEach(function(it){ if (it !== except) setItem(it, false); }); };
  items.forEach(function(item){
    var b = item.querySelector('.nav-more');
    if (!b) return;
    b.addEventListener('click', function(e){
      e.preventDefault();
      e.stopPropagation();
      var open = !item.classList.contains('open');
      if (!mobileNav()) closeAll(item);
      setItem(item, open);
    });
    item.addEventListener('mouseleave', function(){ if (!mobileNav()) setItem(item, false); });
  });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeAll(); });
  document.addEventListener('click', function(e){ if (nav && !mobileNav() && !nav.contains(e.target)) closeAll(); });
  if (toggle && nav){
    var label = toggle.querySelector('.label');
    var setNav = function(open){
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (label) label.textContent = open ? 'Schließen' : 'Menü';
      if (open) items.forEach(function(it){ setItem(it, !!it.querySelector('.nav-link[aria-current="page"]')); });
    };
    toggle.addEventListener('click', function(){ setNav(!nav.classList.contains('open')); });
    nav.addEventListener('click', function(e){ if (e.target.closest('a') && nav.classList.contains('open')) setNav(false); });
  }

  /* ---------- Kopfzeile: leichter Schatten beim Scrollen ---------- */
  var scrolled = null;
  var onScrollHead = function(){
    var s = (window.scrollY || 0) > 4;
    if (s !== scrolled){ scrolled = s; root.classList.toggle('is-scrolled', s); }
  };
  window.addEventListener('scroll', onScrollHead, {passive: true});
  onScrollHead();

  /* ---------- Startseite: Paket ----------
     Das Paket öffnet sich passend zum Scrollen, am Computer und am Handy.
     Moderne Browser berechnen die Bewegung selbst aus der Scrollposition (CSS, Klasse "sda").
     Das läuft unabhängig vom Skript und bleibt auch am Handy flüssig.
     Ältere Browser bekommen dieselbe Bewegung per Skript (Klasse "pin"). */
  (function(){
    var intro = document.getElementById('intro');
    if (!intro || !window.requestAnimationFrame) return;
    var q = function(s){ return intro.querySelector(s); };
    var stage = q('.intro-stage'), grid = q('.intro-grid'), wrap = q('.box-wrap'), box = q('.box'), copy = q('.intro-copy'),
        flL = q('.flap-l'), flR = q('.flap-r'), ifT = q('.iflap-t'), ifB = q('.iflap-b'),
        blade = q('.blade'), bLine = q('.blade-line'), bTip = q('.blade-tip'),
        hint = q('.scroll-hint'), next = document.getElementById('so-gehts');
    if (!stage || !wrap || !box || !copy || !flL || !flR) return;
    var cssScroll = !!(window.CSS && CSS.supports && CSS.supports('animation-timeline', 'scroll()') &&
                       CSS.supports('animation-range', '10px 20px'));
    var mqStack = window.matchMedia ? window.matchMedia('(max-width: 820px)') : null;
    var mode = '', stack = false, p0 = 0, open = 1, stageH = 1, dx = 0, dy = 0, s0 = 1, zoom = 1.2, bh = 0, shade = true, ticking = false, auto = null;
    var vars = {};
    var clamp = function(v){ return v < 0 ? 0 : (v > 1 ? 1 : v); };
    var seg = function(p, a, b){ return clamp((p - a) / (b - a)); };
    var ease = function(x){ return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
    var easeOut = function(x){ return 1 - Math.pow(1 - x, 3); };
    var all = [copy, box, flL, flR, ifT, ifB, blade, bLine, bTip, hint];

    var pick = function(){
      if (reduced() || window.innerHeight < 480) return 'static';
      return cssScroll ? 'sda' : 'pin';
    };
    var setVar = function(name, value){
      if (vars[name] === value) return;
      vars[name] = value;
      intro.style.setProperty(name, value);
    };
    var reset = function(){
      all.forEach(function(el){ if (el){ el.style.transform = ''; el.style.opacity = ''; el.style.visibility = ''; el.style.removeProperty('--sh'); } });
      box.style.perspective = '';
      Object.keys(vars).forEach(function(n){ intro.style.removeProperty(n); });
      vars = {};
      intro.classList.remove('anim', 'pin', 'sda');
    };

    // Maße einmal bestimmen (nicht bei jedem Scrollen): Ab wann steht das Paket, wohin wandert es, wie groß wird es?
    // Öffnen dauert --open (72 % der Bühnenhöhe), danach schiebt sich der nächste Abschnitt darüber.
    var measure = function(){
      var bw = box.offsetWidth, sw, sh;
      bh = box.offsetHeight;
      stack = !!(mqStack && mqStack.matches);
      if (stack){
        // Handy: Der Text scrollt weg, das Paket bleibt in der Mitte des Bildschirms stehen
        sw = wrap.clientWidth; sh = wrap.clientHeight;
        var gap = parseFloat(window.getComputedStyle(grid).rowGap) || 0;
        var ws = window.getComputedStyle(wrap);
        var top = parseFloat(ws.top) || (header ? header.offsetHeight : 0);
        var mt = parseFloat(ws.marginTop) || 0;
        p0 = Math.max(0, Math.round(intro.getBoundingClientRect().top + window.scrollY + copy.offsetTop + copy.offsetHeight + gap + mt - top));
        dx = 0; dy = 0; s0 = 1;
      } else {
        // Computer: Die ganze Bühne bleibt stehen, das Paket wandert in die Mitte
        sw = stage.clientWidth; sh = stage.clientHeight;
        p0 = 0;
        dx = sw / 2 - (wrap.offsetLeft + wrap.offsetWidth / 2);
        dy = sh / 2 - (wrap.offsetTop + wrap.offsetHeight / 2);
        s0 = Math.max(1, Math.min((sw - 32) / bw, sh * .6 / bh));
      }
      stageH = Math.max(1, sh);
      open = Math.max(1, Math.round(sh * .72));
      zoom = s0 * 1.2;
      box.style.perspective = Math.round(bw * 2.3) + 'px';
      if (mode === 'sda'){
        setVar('--p0', p0 + 'px');
        setVar('--dx', dx.toFixed(1) + 'px');
        setVar('--dy', dy.toFixed(1) + 'px');
        setVar('--s0', s0.toFixed(3));
        setVar('--zoom', zoom.toFixed(3));
        setVar('--bh', bh + 'px');
      } else if (mode === 'pin'){
        render();
      }
    };

    var render = function(){
      ticking = false;
      if (mode !== 'pin') return;
      var y = window.scrollY - p0;
      var p = clamp(y / open), cur = clamp((y - open) / stageH);

      if (!stack){
        var c = easeOut(seg(p, 0, .22));
        copy.style.opacity = (1 - c).toFixed(3);
        copy.style.transform = c ? 'translate3d(0,' + (-28 * c).toFixed(1) + 'px,0)' : '';
        copy.style.visibility = c >= 1 ? 'hidden' : '';
      }
      if (hint && !stack){
        var hv = seg(p, 0, .06);
        hint.style.opacity = (1 - hv).toFixed(3);
        hint.style.visibility = hv >= 1 ? 'hidden' : '';
      }

      var cut = ease(seg(p, .12, .45));
      if (blade) blade.style.opacity = cut > 0 ? (1 - seg(p, .45, .52)).toFixed(3) : '0';
      if (bLine) bLine.style.transform = 'scaleY(' + cut.toFixed(4) + ')';
      if (bTip) bTip.style.transform = 'translate3d(0,' + (cut * bh).toFixed(1) + 'px,0)';

      var a = 172 * ease(seg(p, .42, .78));
      flL.style.transform = 'rotateY(' + (-a).toFixed(2) + 'deg)';
      flR.style.transform = 'rotateY(' + a.toFixed(2) + 'deg)';
      var ai = 168 * ease(seg(p, .66, 1));
      if (ifT) ifT.style.transform = 'rotateX(' + ai.toFixed(2) + 'deg)';
      if (ifB) ifB.style.transform = 'rotateX(' + (-ai).toFixed(2) + 'deg)';
      if (shade){
        var sh1 = (.24 * Math.sin(a * Math.PI / 180)).toFixed(3), sh2 = (.2 * Math.sin(ai * Math.PI / 180)).toFixed(3);
        flL.style.setProperty('--sh', sh1);
        flR.style.setProperty('--sh', sh1);
        if (ifT) ifT.style.setProperty('--sh', sh2);
        if (ifB) ifB.style.setProperty('--sh', sh2);
      }

      // Paket wandert in die Mitte, danach wird es etwas größer, während der nächste Abschnitt darüber gleitet
      var mv = ease(seg(p, .05, .45));
      var s = 1 + (s0 - 1) * mv + (zoom - s0) * ease(cur);
      box.style.transform = 'translate3d(' + (dx * mv).toFixed(1) + 'px,' + (dy * mv).toFixed(1) + 'px,0) scale(' + s.toFixed(3) + ')';
    };

    var apply = function(){
      var m = pick();
      if (m !== mode){
        reset();
        mode = m;
        // Schattierung per Skript nur am Computer, am Handy wäre sie zu aufwendig
        shade = finePointer();
        if (m !== 'static') intro.classList.add('anim', m);
      }
      if (mode !== 'static') measure();
    };

    window.addEventListener('scroll', function(){
      if (mode === 'pin' && !ticking){ ticking = true; requestAnimationFrame(render); }
    }, {passive: true});

    // "Paket öffnen": langsam durch die Animation scrollen
    var stop = function(){
      if (auto){ cancelAnimationFrame(auto); auto = null; root.style.scrollBehavior = ''; }
      window.removeEventListener('wheel', stop);
      window.removeEventListener('touchstart', stop);
      window.removeEventListener('keydown', stop);
    };
    var play = function(target){
      stop();
      var from = window.scrollY, delta = target - from, t0 = null;
      var dur = Math.min(3600, Math.max(1400, Math.abs(delta) * 1.5));
      root.style.scrollBehavior = 'auto';
      window.addEventListener('wheel', stop, {passive: true});
      window.addEventListener('touchstart', stop, {passive: true});
      window.addEventListener('keydown', stop);
      var step = function(ts){
        if (t0 === null) t0 = ts;
        var x = clamp((ts - t0) / dur), e = x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
        window.scrollTo(0, from + delta * e);
        if (x < 1) auto = requestAnimationFrame(step); else stop();
      };
      auto = requestAnimationFrame(step);
    };
    intro.addEventListener('click', function(e){
      var t = e.target.closest ? e.target.closest('[data-open]') : null;
      if (!t || mode === 'static' || !next) return;
      e.preventDefault();
      play(next.getBoundingClientRect().top + window.scrollY - (header ? header.offsetHeight : 0));
    });

    var resizeTick = false;
    window.addEventListener('resize', function(){
      if (resizeTick) return;
      resizeTick = true;
      requestAnimationFrame(function(){ resizeTick = false; apply(); });
    });
    if (mqReduce){
      if (mqReduce.addEventListener) mqReduce.addEventListener('change', apply);
      else if (mqReduce.addListener) mqReduce.addListener(apply);
    }
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(apply);
    window.addEventListener('load', apply);
    apply();
  })();

  /* ---------- Einblenden beim Scrollen: einmalig, nur am Computer ----------
     Am Handy bleibt alles ruhig stehen, damit das Wischen sauber ausläuft. */
  (function(){
    if (reduced() || !hasIO || !finePointer()) return;
    var sel = '.section-head,.how > li,.door,.grid-2 > .item,.grid-3 > .item,.split-text,.split-visual,.route-step,.law,' +
              '.steps > li,.flow > li,.calc,.table-wrap,.acc-list,.grow-title,.grow-body,.cta-title,.cta-side,.faq-group';
    var vh = window.innerHeight || 800;
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if (en.isIntersecting){ en.target.classList.add('rv-in'); io.unobserve(en.target); }
      });
    }, {rootMargin: '0px 0px -6% 0px', threshold: .06});
    Array.prototype.slice.call(document.querySelectorAll(sel)).forEach(function(el){
      if (el.closest('.intro') || el.closest('.intro + .section') || el.closest('details:not([open])')) return;
      if (el.getBoundingClientRect().top < vh * .94) return; // schon sichtbar: bleibt, wie es ist
      var sibs = el.parentNode ? Array.prototype.filter.call(el.parentNode.children, function(s){ return s.className === el.className; }) : [];
      var i = sibs.indexOf(el);
      if (i > 0) el.style.transitionDelay = Math.min(i, 5) * 70 + 'ms';
      el.classList.add('rv');
      io.observe(el);
    });
  })();

  /* ---------- Links ----------
     Aufklappbare Abschnitte öffnen sich, wenn ein Link direkt auf sie zeigt.
     Ein Klick auf die Seite, auf der man schon ist, führt nach oben statt die Seite neu zu laden. */
  var findTarget = function(id){
    if (!id) return null;
    try { return document.getElementById(decodeURIComponent(id)); } catch (e) { return null; }
  };
  var openTarget = function(el){
    var d = el && (el.tagName === 'DETAILS' ? el : el.closest('details'));
    while (d){
      d.open = true;
      d = d.parentElement ? d.parentElement.closest('details') : null;
    }
  };
  var currentPage = function(){ return location.pathname.split('/').pop() || 'index.html'; };
  if (location.hash) setTimeout(function(){ openTarget(findTarget(location.hash.slice(1))); }, 60);
  window.addEventListener('hashchange', function(){ openTarget(findTarget(location.hash.slice(1))); });
  document.addEventListener('click', function(e){
    var a = e.target.closest ? e.target.closest('a[href]') : null;
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || a.target) return;
    var href = a.getAttribute('href');
    if (/^[a-z][a-z0-9+.-]*:/i.test(href)) return;   // mailto:, https: und Ähnliches normal öffnen
    var i = href.indexOf('#');
    var page = i > -1 ? href.slice(0, i) : href;
    if (page !== '' && page !== currentPage()) return;
    if (i > -1){ openTarget(findTarget(href.slice(i + 1))); return; }
    e.preventDefault();
    window.scrollTo({top: 0, behavior: reduced() ? 'auto' : 'smooth'});
  });

  /* ---------- Leiste „Auf dieser Seite“: zeigt, in welchem Abschnitt man gerade ist ---------- */
  (function(){
    var bar = document.querySelector('.pagebar');
    if (!bar) return;
    var links = Array.prototype.slice.call(bar.querySelectorAll('.pagebar-list a'));
    var secs = links.map(function(a){ return document.getElementById(a.getAttribute('href').slice(1)); });
    var scroller = bar.querySelector('.pagebar-scroll');
    var active = -1;
    // Ränder der Leiste nur dort ausblenden, wo es noch weitergeht
    var edges = function(){
      if (!scroller) return;
      var max = scroller.scrollWidth - scroller.clientWidth;
      scroller.classList.toggle('more-left', scroller.scrollLeft > 2);
      scroller.classList.toggle('more-right', scroller.scrollLeft < max - 2);
    };
    if (scroller) scroller.addEventListener('scroll', edges, {passive: true});
    // Aktiven Abschnitt in der Leiste sichtbar halten, falls die Leiste breiter ist als der Bildschirm
    var showLink = function(a){
      if (!scroller) return;
      var max = scroller.scrollWidth - scroller.clientWidth;
      if (max <= 2) return;
      var sr = scroller.getBoundingClientRect(), ar = a.getBoundingClientRect();
      var sl = scroller.scrollLeft, l = ar.left - sr.left + sl, r = l + ar.width, w = scroller.clientWidth;
      if (l < sl + 24 || r > sl + w - 32){
        var to = Math.round(Math.min(max, Math.max(0, l - (w - ar.width) / 2)));
        if (scroller.scrollTo) scroller.scrollTo({left: to, behavior: reduced() ? 'auto' : 'smooth'});
        else scroller.scrollLeft = to;
      }
    };
    var update = function(){
      var line = (header ? header.offsetHeight : 0) + bar.offsetHeight + Math.round(window.innerHeight * .2);
      var idx = -1;
      secs.forEach(function(s, i){ if (s && s.getBoundingClientRect().top <= line) idx = i; });
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) idx = secs.length - 1;
      if (idx === active) return;
      if (active > -1){ links[active].classList.remove('is-active'); links[active].removeAttribute('aria-current'); }
      active = idx;
      if (idx > -1){
        links[idx].classList.add('is-active');
        links[idx].setAttribute('aria-current', 'location');
        showLink(links[idx]);
      }
    };
    if (hasIO){
      var th = [];
      for (var t = 0; t <= 20; t++) th.push(t / 20);
      var io = new IntersectionObserver(update, {threshold: th});
      secs.forEach(function(s){ if (s) io.observe(s); });
    } else {
      window.addEventListener('scroll', update, {passive: true});
    }
    window.addEventListener('resize', function(){ edges(); update(); });
    edges();
    update();
  })();

  /* ---------- Häufige Fragen: aktuelles Thema in der Themenliste markieren ---------- */
  (function(){
    var fnav = document.querySelector('.faq-nav');
    if (!fnav || !hasIO) return;
    var links = Array.prototype.slice.call(fnav.querySelectorAll('a[href^="#"]'));
    var groups = links.map(function(a){ return document.getElementById(a.getAttribute('href').slice(1)); });
    var wrapEl = fnav.parentNode;
    var cur = -1;
    var update = function(){
      var line = (header ? header.offsetHeight : 0) + 150;
      var idx = -1;
      groups.forEach(function(g, i){ if (g && g.getBoundingClientRect().top <= line) idx = i; });
      if (wrapEl && wrapEl.getBoundingClientRect().bottom < line) idx = -1;
      if (idx === cur) return;
      if (cur > -1){ links[cur].classList.remove('is-active'); links[cur].removeAttribute('aria-current'); }
      cur = idx;
      if (idx > -1){ links[idx].classList.add('is-active'); links[idx].setAttribute('aria-current', 'location'); }
    };
    var th = [];
    for (var t = 0; t <= 10; t++) th.push(t / 10);
    var io = new IntersectionObserver(update, {threshold: th});
    groups.forEach(function(g){ if (g) io.observe(g); });
    update();
  })();

  /* ---------- Strichcodes (fest pro Seed) ---------- */
  var codes = document.querySelectorAll('svg[data-barcode]');
  for (var c = 0; c < codes.length; c++){
    var svg = codes[c];
    var seed = parseInt(svg.getAttribute('data-barcode'), 10) || 4711;
    var rnd = (function(s){ return function(){ s = (s * 16807) % 2147483647; return s / 2147483647; }; })(seed);
    var out = '<rect x="4" y="0" width="2" height="60"/><rect x="8" y="0" width="1" height="60"/>';
    var x = 12;
    while (x < 284){
      var w = 1 + Math.floor(rnd() * 3.4);
      if (x + w > 284) break;
      out += '<rect x="' + x + '" y="0" width="' + w + '" height="60"/>';
      x += w + 1 + Math.floor(rnd() * 2.8);
    }
    out += '<rect x="290" y="0" width="1" height="60"/><rect x="293" y="0" width="2" height="60"/>';
    svg.innerHTML = out;
  }

  /* ---------- Jahr im Fußbereich ---------- */
  try {
    var now = new Date();
    var ys = document.querySelectorAll('[data-year]');
    for (var y = 0; y < ys.length; y++) ys[y].textContent = String(now.getFullYear());
  } catch (e) {}

  /* ---------- Kopieren mit Rückfall auf Markieren ---------- */
  function selectNode(node){
    try {
      var range = document.createRange();
      range.selectNodeContents(node);
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    } catch (e) {}
  }
  function copyText(text, node, statusEl){
    var done = function(){ if (statusEl) statusEl.textContent = 'Kopiert.'; };
    var fallback = function(){
      selectNode(node);
      if (statusEl) statusEl.textContent = 'Text ist markiert. Bitte selbst kopieren.';
    };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(text).then(done, fallback);
      } else { fallback(); }
    } catch (e) { fallback(); }
  }
  var copyBtns = document.querySelectorAll('[data-copy]');
  for (var b = 0; b < copyBtns.length; b++){
    copyBtns[b].addEventListener('click', function(){
      var target = document.getElementById(this.getAttribute('data-copy'));
      var status = document.getElementById(this.getAttribute('data-status'));
      if (target) copyText(target.textContent.trim(), target, status);
    });
  }

  /* ---------- Stellplatz-Rechner ---------- */
  // Europalette 120 × 80 cm, Ladehöhe bis 150 cm, Kartons stehen aufrecht.
  function palletPlan(count, l, b, h){
    var FL = 120, FB = 80, MAXH = 150;
    if (!(count > 0 && l > 0 && b > 0 && h > 0)){
      return {error: 'Bitte alle Felder mit Zahlen größer als 0 ausfüllen.'};
    }
    count = Math.ceil(count);
    var perLayer = Math.max(Math.floor(FL / l) * Math.floor(FB / b), Math.floor(FL / b) * Math.floor(FB / l));
    var layers = Math.floor(MAXH / h);
    if (perLayer < 1){
      return {error: 'Ihre Kartons sind größer als die Grundfläche einer Europalette. Sprechen Sie uns an, dafür finden wir eine Lösung.'};
    }
    if (layers < 1){
      return {error: 'Ihre Kartons sind höher als 1,50 m. Sprechen Sie uns an, dafür finden wir eine Lösung.'};
    }
    var perPallet = perLayer * layers;
    var pallets = Math.ceil(count / perPallet);
    var lastCount = count - (pallets - 1) * perPallet;
    return {perLayer: perLayer, layers: layers, perPallet: perPallet, pallets: pallets, lastCount: lastCount};
  }
  window.kattapackPalletPlan = palletPlan;

  var calc = document.getElementById('calc');
  if (calc){
    var fCount = document.getElementById('c-count');
    var fL = document.getElementById('c-l');
    var fB = document.getElementById('c-b');
    var fH = document.getElementById('c-h');
    var oNum = document.getElementById('c-num');
    var oUnit = document.getElementById('c-unit');
    var oStatus = document.getElementById('c-status');
    var oBreak = document.getElementById('c-break');
    var oViz = document.getElementById('c-viz');
    var nf = function(n){ try { return n.toLocaleString('de-DE'); } catch (e) { return String(n); } };
    var val = function(el){ return parseFloat(String(el.value).replace(',', '.')); };

    // Paletten-Grafik einmal aufbauen und danach nur anpassen, damit Änderungen weich animiert werden
    var FRAME = 110, lastNum = null;
    var mkGroup = function(cls, label, n){
      var g = document.createElement('div');
      g.className = 'pal-group' + (cls ? ' ' + cls : '');
      var row = document.createElement('div');
      row.className = 'pal-row';
      var pals = [];
      for (var i = 0; i < n; i++){
        var pal = document.createElement('div');
        pal.className = 'pal';
        pal.innerHTML = '<div class="pal-frame"><div class="pal-load"></div></div><div class="pal-base"></div>';
        pal.hidden = true;
        row.appendChild(pal);
        pals.push(pal);
      }
      g.appendChild(row);
      g.insertAdjacentHTML('beforeend', '<div class="pal-brace"></div><div class="pal-label">' + label + '</div>');
      oViz.appendChild(g);
      return {el: g, pals: pals};
    };
    oViz.innerHTML = '';
    var gFree = mkGroup('', 'kostenfrei', 3), gPaid = mkGroup('paid', 'nach Angebot', 9);
    var more = document.createElement('div');
    more.className = 'pal-more';
    more.hidden = true;
    oViz.appendChild(more);
    var setPal = function(pal, layers, total){
      var load = pal.firstChild.firstChild;
      var lh = FRAME / total, h = Math.max(4, Math.round(layers * lh));
      load.style.setProperty('--lh', lh.toFixed(2) + 'px');
      if (pal.hidden){ pal.hidden = false; load.style.height = '0px'; void load.offsetHeight; }
      load.style.height = h + 'px';
    };

    var render = function(){
      var r = palletPlan(val(fCount), val(fL), val(fB), val(fH));
      if (r.error){
        oNum.textContent = '–';
        oUnit.textContent = 'Palettenstellplätze';
        oStatus.textContent = r.error;
        oStatus.className = 'calc-status';
        oBreak.textContent = '';
        gFree.el.hidden = true;
        gPaid.el.hidden = true;
        more.hidden = true;
        lastNum = null;
        return;
      }
      oNum.textContent = nf(r.pallets);
      oUnit.textContent = r.pallets === 1 ? 'Palettenstellplatz' : 'Palettenstellplätze';
      if (r.pallets <= 3){
        oStatus.textContent = 'Passt in die kostenfreien Stellplätze. Lagerkosten: 0,00 € im Monat.';
        oStatus.className = 'calc-status ok';
      } else {
        var extra = r.pallets - 3;
        oStatus.textContent = '3 Stellplätze sind kostenfrei. Für ' + (extra === 1 ? '1 weiteren Stellplatz' : nf(extra) + ' weitere Stellplätze') + ' gilt der Preis aus Ihrem Angebot.';
        oStatus.className = 'calc-status';
      }
      oBreak.textContent = nf(r.perLayer) + (r.perLayer === 1 ? ' Karton' : ' Kartons') + ' pro Lage × ' + nf(r.layers) + (r.layers === 1 ? ' Lage' : ' Lagen') + ' = ' + nf(r.perPallet) + (r.perPallet === 1 ? ' Karton' : ' Kartons') + ' pro Stellplatz';

      var shown = Math.min(r.pallets, 12);
      var lastLayers = Math.ceil(r.lastCount / r.perLayer);
      gFree.el.hidden = false;
      for (var i = 0; i < 12; i++){
        var pal = i < 3 ? gFree.pals[i] : gPaid.pals[i - 3];
        if (i < shown) setPal(pal, (i + 1 === r.pallets) ? lastLayers : r.layers, r.layers);
        else pal.hidden = true;
      }
      gPaid.el.hidden = shown <= 3;
      more.hidden = r.pallets <= shown;
      if (!more.hidden) more.textContent = '+ ' + nf(r.pallets - shown) + ' weitere';
      if (lastNum !== null && lastNum !== r.pallets){
        oNum.classList.remove('bump');
        void oNum.offsetWidth;
        oNum.classList.add('bump');
      }
      lastNum = r.pallets;
    };
    [fCount, fL, fB, fH].forEach(function(el){ el.addEventListener('input', render); });
    render();
  }

  /* ---------- Anfrageformular: Pflichtangaben prüfen, dann E-Mail-Text zusammenstellen ---------- */
  var form = document.getElementById('contact-form');
  if (form){
    var result = document.getElementById('result');
    var resultText = document.getElementById('result-text');
    var resultMail = document.getElementById('result-mailto');
    var resultStatus = document.getElementById('result-status');
    var formNote = document.getElementById('form-note');
    var defaultNote = formNote ? formNote.textContent : '';
    var get = function(n){ var el = form.elements[n]; return el && el.value ? String(el.value).trim() : ''; };

    var required = Array.prototype.slice.call(form.querySelectorAll('[required]'));
    var fieldOf = function(el){ return el.closest('.field') || el.parentNode; };
    var errorOf = function(el){
      var id = el.id + '-err', box = document.getElementById(id);
      if (!box){
        box = document.createElement('p');
        box.className = 'field-error';
        box.id = id;
        box.hidden = true;
        fieldOf(el).appendChild(box);
      }
      return box;
    };
    var check = function(el){
      var v = String(el.value || '').trim();
      var ok = v !== '';
      var msg = el.getAttribute('data-error') || 'Bitte füllen Sie dieses Feld aus.';
      if (ok && el.type === 'email' && !el.checkValidity()){ ok = false; msg = 'Bitte prüfen Sie die E-Mail-Adresse.'; }
      var box = errorOf(el);
      fieldOf(el).classList.toggle('invalid', !ok);
      el.setAttribute('aria-invalid', ok ? 'false' : 'true');
      if (ok){
        box.hidden = true;
        box.textContent = '';
        el.removeAttribute('aria-describedby');
      } else {
        box.textContent = msg;
        box.hidden = false;
        el.setAttribute('aria-describedby', box.id);
      }
      return ok;
    };
    required.forEach(function(el){
      el.addEventListener(el.tagName === 'SELECT' ? 'change' : 'input', function(){
        if (fieldOf(el).classList.contains('invalid')) check(el);
        if (!form.querySelector('.field.invalid')){ formNote.textContent = defaultNote; formNote.classList.remove('error'); }
      });
      if (el.type === 'email') el.addEventListener('blur', function(){ if (el.value) check(el); });
    });

    form.addEventListener('submit', function(e){
      e.preventDefault();
      var missing = required.filter(function(el){ return !check(el); });
      if (missing.length){
        formNote.textContent = missing.length === 1 ? 'Bitte füllen Sie das markierte Feld aus.' : 'Bitte füllen Sie die ' + missing.length + ' markierten Felder aus.';
        formNote.classList.add('error');
        missing[0].focus();
        return;
      }
      formNote.textContent = defaultNote;
      formNote.classList.remove('error');
      var name = get('name');
      var needs = Array.prototype.slice.call(form.querySelectorAll('input[name="needs"]:checked')).map(function(i){ return i.value; });
      var lines = ['Hallo kattapack-Team,', '', 'ich interessiere mich für ein Fulfillment-Angebot.', '',
        'Name: ' + name, 'E-Mail: ' + get('email'), 'Shop/Firma: ' + get('shop')];
      if (get('phone')) lines.push('Telefon: ' + get('phone'));
      if (get('website')) lines.push('Website: ' + get('website'));
      lines.push('', 'Shopsystem: ' + get('system'), 'Bestellungen pro Monat: ' + get('volume'),
        'Anzahl Artikel: ' + get('skus'), 'Bestand heute: ' + get('stock'), 'Produkte: ' + get('products'),
        'Gewünschte Leistungen: ' + (needs.length ? needs.join(', ') : '-'), 'Start: ' + get('start'));
      if (get('message')) lines.push('', 'Nachricht:', get('message'));
      lines.push('', 'Viele Grüße', name);
      var body = lines.join('\n');
      resultText.textContent = body;
      var subject = 'Anfrage Fulfillment: ' + get('shop');
      resultMail.href = 'mailto:' + EMAIL + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      resultStatus.textContent = '';
      form.hidden = true;
      result.hidden = false;
      var t = document.getElementById('result-title');
      if (t) t.focus();
    });

    var copyRes = document.getElementById('copy-result');
    if (copyRes){
      copyRes.addEventListener('click', function(){ copyText(resultText.textContent, resultText, resultStatus); });
    }
    var editRes = document.getElementById('edit-result');
    if (editRes){
      editRes.addEventListener('click', function(){
        result.hidden = true;
        form.hidden = false;
        form.elements.name.focus();
      });
    }
  }
})();
