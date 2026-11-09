(function () {
  var btn = document.querySelector('.menu-toggle');
  var nav = document.getElementById('nav');
  if (btn && nav) btn.addEventListener('click', function () {
    var open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', open);
  });

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
