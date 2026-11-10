// Service worker za Dnevnik: podsjetnici (push) i rad bez interneta.
const CACHE = "dnevnik-v1";
const FILES = ["/dnevnik/", "/dnevnik/manifest.json", "/dnevnik/apple-touch-icon.png", "/dnevnik/icon-192.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

// Uvijek najprije svježa verzija s mreže, a bez interneta zadnja spremljena.
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/dnevnik/api/")) return;
  e.respondWith(
    fetch(e.request).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
      return res;
    }).catch(() => caches.match(e.request).then(r => r || caches.match("/dnevnik/")))
  );
});

self.addEventListener("push", e => {
  let msg = { title: "Dnevnik", body: "Upiši današnji dan.", url: "/dnevnik/" };
  try { msg = Object.assign(msg, e.data.json()); } catch (_) {}
  e.waitUntil(self.registration.showNotification(msg.title, {
    body: msg.body,
    icon: "/dnevnik/icon-192.png",
    badge: "/dnevnik/icon-192.png",
    tag: "dnevnik-podsjetnik",
    data: { url: msg.url },
  }));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || "/dnevnik/";
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
    for (const c of list) if (c.url.includes("/dnevnik/")) return c.focus();
    return self.clients.openWindow(url);
  }));
});
