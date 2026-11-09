(function () {
  var btn = document.querySelector('.menu-toggle');
  var nav = document.getElementById('nav');
  if (btn && nav) btn.addEventListener('click', function () {
    var open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', open);
  });

  // Početna: video sporije (pola brzine), na računalu i mobitelu
  var hv = document.querySelector('.hero-video video');
  if (hv) {
    var slow = function () { hv.playbackRate = 0.5; };
    slow(); hv.addEventListener('loadedmetadata', slow); hv.addEventListener('play', slow);
  }

  // Galerije: rasporedi radove u stupce tako da se redoslijed čita s lijeva na desno
  Array.prototype.forEach.call(document.querySelectorAll('.gallery'), function (g) {
    var items = Array.prototype.slice.call(g.querySelectorAll(':scope > .item, :scope > .gcol > .item'));
    var min = g.classList.contains('murals') ? 280 : 230, max = g.classList.contains('murals') ? 3 : 4, gap = 24, last = 0;
    function layout() {
      var w = g.clientWidth, n = Math.max(1, Math.min(max, Math.floor((w + gap) / (min + gap))));
      if (n === last) return;
      last = n;
      var cols = [];
      for (var c = 0; c < n; c++) { var d = document.createElement('div'); d.className = 'gcol'; cols.push(d); }
      items.forEach(function (it, i) { cols[i % n].appendChild(it); });
      g.innerHTML = '';
      cols.forEach(function (d) { g.appendChild(d); });
      g.classList.add('masonry');
    }
    layout();
    var t; window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(layout, 150); });
  });


  // Trgovina: košarica u pregledniku (localStorage)
  var CART_KEY = 'vs-cart';
  function cartGet() { try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; } catch (e) { return []; } }
  function cartSet(c) { try { localStorage.setItem(CART_KEY, JSON.stringify(c)); } catch (e) {} cartBadge(); }
  function cartBadge() {
    var n = cartGet().reduce(function (a, x) { return a + x.qty; }, 0);
    Array.prototype.forEach.call(document.querySelectorAll('.cart-count'), function (el) { el.textContent = n; });
  }
  cartBadge();
  var prod = document.querySelector('.product');
  if (prod) {
    var form = prod.querySelector('.buy-form'), priceEl = form.querySelector('.price');
    function sel() { return form.querySelector('input[name=size]:checked'); }
    form.addEventListener('change', function () { priceEl.textContent = sel().getAttribute('data-price'); });
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var s = sel(), c = cartGet(), id = prod.getAttribute('data-slug') + ':' + s.value;
      var hit = c.filter(function (x) { return x.id === id; })[0];
      if (hit) hit.qty += 1;
      else c.push({ id: id, slug: prod.getAttribute('data-slug'), name: prod.getAttribute('data-name'),
        size: s.getAttribute('data-label'), price: +s.getAttribute('data-price'), qty: 1,
        img: prod.getAttribute('data-img'), url: prod.getAttribute('data-url') });
      cartSet(c);
      form.querySelector('.added').hidden = false;
    });
  }
  var cp = document.querySelector('.cart-page');
  if (cp) {
    var box = cp.querySelector('.cart-items'), sum = cp.querySelector('.cart-sum');
    function render() {
      var c = cartGet(), total = 0;
      if (!c.length) { box.innerHTML = '<p class="empty">' + cp.getAttribute('data-empty') + '</p>'; sum.hidden = true; return; }
      box.innerHTML = c.map(function (x, i) {
        total += x.price * x.qty;
        return '<div class="cart-row"><a href="' + x.url + '"><img src="' + x.img + '" alt=""></a>' +
          '<div class="ci"><a href="' + x.url + '"><b>' + x.name + '</b></a><span>' + x.size + '</span>' +
          '<span class="qty">' + cp.getAttribute('data-qty') + ' <button data-d="-1" data-i="' + i + '">−</button> ' + x.qty +
          ' <button data-d="1" data-i="' + i + '">+</button></span>' +
          '<button class="rm" data-i="' + i + '">' + cp.getAttribute('data-remove') + '</button></div>' +
          '<div class="cp">' + (x.price * x.qty) + ' €</div></div>';
      }).join('');
      cp.querySelector('.sum').textContent = total; sum.hidden = false;
    }
    box.addEventListener('click', function (ev) {
      var b = ev.target.closest('button'); if (!b) return;
      var c = cartGet(), i = +b.getAttribute('data-i');
      if (b.classList.contains('rm')) c.splice(i, 1);
      else { c[i].qty += +b.getAttribute('data-d'); if (c[i].qty < 1) c.splice(i, 1); }
      cartSet(c); render();
    });
    cp.querySelector('.checkout').addEventListener('click', function () {
      var p = cp.querySelector('.soon'); p.textContent = this.getAttribute('data-soon'); p.hidden = false;
    });
    render();
  }

  var links = Array.prototype.slice.call(document.querySelectorAll('a.lb'));
  if (!links.length) return;
  var box = document.createElement('div');
  box.className = 'lightbox';
  box.innerHTML = '<button class="lb-close" aria-label="Close">×</button>' +
    '<button class="lb-prev" aria-label="Previous">‹</button>' +
    '<img alt=""><p></p><p class="lb-desc"></p>' +
    '<button class="lb-next" aria-label="Next">›</button>';
  document.body.appendChild(box);
  var img = box.querySelector('img'), cap = box.querySelector('p'),
      desc = box.querySelector('.lb-desc'), i = 0;
  function show(n) {
    i = (n + links.length) % links.length;
    img.src = links[i].href;
    img.alt = links[i].querySelector('img').alt;
    cap.textContent = links[i].getAttribute('data-caption');
    desc.textContent = links[i].getAttribute('data-desc') || '';
    desc.hidden = !desc.textContent;
    box.classList.add('open');
  }
  function close() { box.classList.remove('open'); img.removeAttribute('src'); }
  links.forEach(function (a, n) {
    a.addEventListener('click', function (ev) { ev.preventDefault(); show(n); });
  });
  box.querySelector('.lb-close').onclick = close;
  box.querySelector('.lb-prev').onclick = function () { show(i - 1); };
  box.querySelector('.lb-next').onclick = function () { show(i + 1); };
  box.addEventListener('click', function (ev) { if (ev.target === box) close(); });
  document.addEventListener('keydown', function (ev) {
    if (!box.classList.contains('open')) return;
    if (ev.key === 'Escape') close();
    if (ev.key === 'ArrowLeft') show(i - 1);
    if (ev.key === 'ArrowRight') show(i + 1);
  });
})();
