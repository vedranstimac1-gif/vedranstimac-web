#!/usr/bin/env python3
"""Generira statične HTML stranice u site/ iz content.json.
Sadržaj se mijenja u content.json, zatim: python3 scripts/build.py
"""
import json, os
from html import escape as e

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
C = json.load(open(os.path.join(ROOT, "content.json"), encoding="utf-8"))
S = C["site"]
DOMAIN = "https://www.vedranstimac.com"

def web(wid):
    return "/media/web/" + wid.split("~")[0] + ".jpg"

def orig(wid):
    return "/media/orig/" + wid

ICONS = {
    "behance": '<path d="M9.2 11.6c.6-.3 1-.9 1-1.7 0-1.6-1.2-2.1-2.7-2.1H4v8.4h3.6c1.6 0 3-.7 3-2.4 0-1.1-.5-1.9-1.4-2.2zM5.6 9.1h1.6c.6 0 1.2.2 1.2.9s-.4.9-1 .9H5.6V9.1zm1.8 5.8H5.6v-2.3h1.8c.8 0 1.2.3 1.2 1.2 0 .8-.6 1.1-1.2 1.1zm8-4.9c-1.9 0-3.1 1.3-3.1 3.1 0 1.9 1.2 3.1 3.1 3.1 1.4 0 2.4-.7 2.8-2h-1.5c-.2.5-.7.8-1.3.8-.9 0-1.4-.5-1.5-1.5H18.4c.1-2-1-3.5-3-3.5zm-1.5 2.5c.1-.8.6-1.3 1.4-1.3.8 0 1.2.5 1.3 1.3h-2.7zm-.2-3.9h3.4v.9h-3.4z"/>',
    "facebook": '<path d="M13.4 20v-7.3h2.4l.4-2.8h-2.8V8.1c0-.8.2-1.4 1.4-1.4h1.5V4.2c-.3 0-1.1-.1-2.1-.1-2.1 0-3.6 1.3-3.6 3.7v2.1H8.2v2.8h2.4V20h2.8z"/>',
    "instagram": '<path d="M12 7.3a4.7 4.7 0 1 0 0 9.4 4.7 4.7 0 0 0 0-9.4zm0 7.7a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm4.9-8.9a1.1 1.1 0 1 1-2.2 0 1.1 1.1 0 0 1 2.2 0zM12 4.6c2.4 0 2.7 0 3.6.1 2.4.1 3.6 1.3 3.7 3.7.1.9.1 1.2.1 3.6s0 2.7-.1 3.6c-.1 2.4-1.3 3.6-3.7 3.7-.9.1-1.2.1-3.6.1s-2.7 0-3.6-.1c-2.4-.1-3.6-1.3-3.7-3.7-.1-.9-.1-1.2-.1-3.6s0-2.7.1-3.6c.1-2.4 1.3-3.6 3.7-3.7.9-.1 1.2-.1 3.6-.1z" fill="none" stroke="#fff" stroke-width="1.6"/>',
}

def page(path, title, body, desc=None, cls=""):
    desc = desc or S["description"]
    full_title = f"{title} | {S['title']}" if title else f"Vedran Štimac | {S['title']}"
    url = DOMAIN + path
    social = "".join(
        f'<li><a href="{S["social"][k]}" target="_blank" rel="noopener" aria-label="{k.title()}">'
        f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[k]}</svg></a></li>'
        for k in ("behance", "facebook", "instagram"))
    def nav(href, label):
        cur = ' aria-current="page"' if path == href else ""
        return f'<li><a href="{href}"{cur}>{label}</a></li>'
    work_cur = ' class="current"' if path in ("/illustrations", "/street-art") else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{S['title']}">
<meta property="og:image" content="{DOMAIN}/media/orig/{C['media']['og']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="google-site-verification" content="{S['google_site_verification']}">
<meta name="p:domain_verify" content="{S['pinterest_verify']}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Roboto:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
</head>
<body class="{cls}">
<header class="site-header">
  <a class="brand" href="/">
    <span class="brand-name">{S['title']}</span>
    <span class="brand-tag">{S['tagline']}</span>
  </a>
  <button class="menu-toggle" aria-expanded="false" aria-controls="nav" aria-label="Menu"><span></span><span></span><span></span></button>
  <nav id="nav">
    <ul>
      {nav("/", "HOME")}
      {nav("/about", "ABOUT")}
      <li class="has-sub"><a href="/illustrations"{work_cur}>WORK</a>
        <ul class="sub">
          {nav("/illustrations", "ILLUSTRATIONS")}
          {nav("/street-art", "STREET ART")}
        </ul>
      </li>
      {nav("/contact", "CONTACT")}
      <li><a href="{S['shop']}" target="_blank" rel="noopener">SHOP</a></li>
    </ul>
  </nav>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <p>{S['copyright']}</p>
  <ul class="social">{social}</ul>
</footer>
<script src="/site.js" defer></script>
</body>
</html>
"""

def gallery(items, kind):
    out = []
    for name, caption, wid in items:
        out.append(
            f'<figure class="item">'
            f'<a href="{orig(wid)}" class="lb" data-caption="{e(name)} — {e(caption)}">'
            f'<img src="{web(wid)}" alt="{e(name)}" loading="lazy" decoding="async"></a>'
            f'<figcaption><strong>{e(name)}</strong><span>{e(caption)}</span></figcaption>'
            f'</figure>')
    return f'<div class="gallery {kind}">' + "\n".join(out) + "</div>"

def write(rel, html):
    p = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(html)

M = C["media"]

# HOME
write("index.html", page("/", None, f"""
<section class="hero-video">
  <video autoplay muted loop playsinline preload="auto" poster="/media/home-poster.jpg">
    <source src="/media/home.mp4" type="video/mp4">
  </video>
</section>""", cls="home"))

# ABOUT
ex = []
for year, items in C["exhibitions"]:
    ex.append(f"<h3>{year}</h3>")
    for t, place in items:
        ex.append(f"<p>{e(t)}<br>{e(place)}</p>")
write("about/index.html", page("/about", "ABOUT", f"""
<section class="about">
  <div class="about-text">
    <h1>ABOUT</h1>
    {''.join(f'<p>{e(p)}</p>' for p in C['about'])}
  </div>
  <div class="about-photo"><img src="{web(M['about_portrait'])}" alt="Picture of Vedran"></div>
  <div class="about-photo wide"><img src="{web(M['about_mural'])}" alt="Vedran painting a mural" loading="lazy"></div>
  <div class="exhibitions">
    <h2>EXHIBITIONS</h2>
    {''.join(ex)}
  </div>
</section>"""))

# ILLUSTRATIONS
write("illustrations/index.html", page("/illustrations", "ILLUSTRATIONS", f"""
<section class="work">
  <h1 class="page-title">ILLUSTRATIONS</h1>
  {gallery(C['illustrations'], 'portraits')}
</section>""", desc='Illustrations from series "Room of Portraits".'))

# STREET ART
write("street-art/index.html", page("/street-art", "STREET ART", f"""
<section class="banner">
  <video autoplay muted loop playsinline preload="auto" poster="/media/street-art-poster.jpg">
    <source src="/media/street-art.mp4" type="video/mp4">
  </video>
  <h1>STREET ART</h1>
</section>
<section class="work">
  {gallery(C['street_art'], 'murals')}
</section>""", desc="Murals and street art by Vedran Štimac (PoliteBastART)."))

# CONTACT
write("contact/index.html", page("/contact", "CONTACT", f"""
<section class="contact">
  <h1>HAVE A PROJECT<br>IN MIND?</h1>
  <p>e-mail: <a href="mailto:{S['email']}">{S['email']}</a></p>
  <p>studio: {S['studio']}</p>
</section>"""))

# 404
write("404.html", page("/404", "NOT FOUND", """
<section class="contact">
  <h1>PAGE NOT FOUND</h1>
  <p><a href="/">Back to home</a></p>
</section>"""))

print("Stranice generirane u", SITE)
