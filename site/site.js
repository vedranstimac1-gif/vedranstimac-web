(function () {
  var btn = document.querySelector('.menu-toggle');
  var nav = document.getElementById('nav');
  if (btn && nav) btn.addEventListener('click', function () {
    var open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', open);
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
