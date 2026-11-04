#!/usr/bin/env python3
"""Generira statične HTML stranice u site/ iz content.json.
Sadržaj se mijenja u content.json, zatim: python3 scripts/build.py
"""
import json, os, re
from html import escape as e

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
C = json.load(open(os.path.join(ROOT, "content.json"), encoding="utf-8"))
S = C["site"]
DOMAIN = "https://www.vedranstimac.com"
MURAL_PATHS = {"/" + m["slug"] for m in C["street_art"] if isinstance(m, dict)}
ILL_PATHS = {"/" + m["slug"] for m in C["illustrations"] if isinstance(m, dict)}

def ill_img(it):
    """Slika ilustracije s opisnim imenom datoteke (bolje za Google slike)."""
    import shutil
    name = f"{it['slug']}-portrait-illustration-vedran-stimac.jpg"
    dst = os.path.join(SITE, "media", "illustrations", name)
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(SITE, web(it["image"]).lstrip("/")), dst)
    return "/media/illustrations/" + name

def web(wid):
    stem = wid.split("~")[0] if "~" in wid else os.path.splitext(wid)[0]
    return "/media/web/" + stem + ".jpg"

def orig(wid):
    return "/media/orig/" + wid

ICONS = {
    "behance": '<path d="M9.2 11.6c.6-.3 1-.9 1-1.7 0-1.6-1.2-2.1-2.7-2.1H4v8.4h3.6c1.6 0 3-.7 3-2.4 0-1.1-.5-1.9-1.4-2.2zM5.6 9.1h1.6c.6 0 1.2.2 1.2.9s-.4.9-1 .9H5.6V9.1zm1.8 5.8H5.6v-2.3h1.8c.8 0 1.2.3 1.2 1.2 0 .8-.6 1.1-1.2 1.1zm8-4.9c-1.9 0-3.1 1.3-3.1 3.1 0 1.9 1.2 3.1 3.1 3.1 1.4 0 2.4-.7 2.8-2h-1.5c-.2.5-.7.8-1.3.8-.9 0-1.4-.5-1.5-1.5H18.4c.1-2-1-3.5-3-3.5zm-1.5 2.5c.1-.8.6-1.3 1.4-1.3.8 0 1.2.5 1.3 1.3h-2.7zm-.2-3.9h3.4v.9h-3.4z"/>',
    "facebook": '<path d="M13.4 20v-7.3h2.4l.4-2.8h-2.8V8.1c0-.8.2-1.4 1.4-1.4h1.5V4.2c-.3 0-1.1-.1-2.1-.1-2.1 0-3.6 1.3-3.6 3.7v2.1H8.2v2.8h2.4V20h2.8z"/>',
    "instagram": '<path d="M12 7.3a4.7 4.7 0 1 0 0 9.4 4.7 4.7 0 0 0 0-9.4zm0 7.7a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm4.9-8.9a1.1 1.1 0 1 1-2.2 0 1.1 1.1 0 0 1 2.2 0zM12 4.6c2.4 0 2.7 0 3.6.1 2.4.1 3.6 1.3 3.7 3.7.1.9.1 1.2.1 3.6s0 2.7-.1 3.6c-.1 2.4-1.3 3.6-3.7 3.7-.9.1-1.2.1-3.6.1s-2.7 0-3.6-.1c-2.4-.1-3.6-1.3-3.7-3.7-.1-.9-.1-1.2-.1-3.6s0-2.7.1-3.6c.1-2.4 1.3-3.6 3.7-3.7.9-.1 1.2-.1 3.6-.1z" fill="none" stroke="#fff" stroke-width="1.6"/>',
}

def analytics():
    """Cloudflare Web Analytics (bez kolačića). Token se upisuje u content.json -> site.cf_analytics_token."""
    t = S.get("cf_analytics_token")
    if not t:
        return ""
    return ("\n<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" "
            f"data-cf-beacon='{{\"token\": \"{e(t)}\"}}'></script>")

PERSON = {
    "@type": "Person",
    "@id": DOMAIN + "/#vedran",
    "name": "Vedran Štimac",
    "alternateName": "PoliteBastART",
    "jobTitle": "Illustrator and muralist",
    "description": "Croatian illustrator, muralist and street artist from Pula, based in Zagreb.",
    "url": DOMAIN + "/",
    "image": DOMAIN + "/media/web/068c28_e11b793a722f4617a98d37fa5b3d1205.jpg",
    "email": "mailto:" + S["email"],
    "birthPlace": {"@type": "Place", "name": "Pula, Croatia"},
    "homeLocation": {"@type": "Place", "name": "Zagreb, Croatia"},
    "knowsAbout": ["Illustration", "Murals", "Street art", "Portrait illustration", "Screen printing"],
    "sameAs": [S["social"]["instagram"], S["social"]["behance"], S["social"]["facebook"], S["shop"]],
}

def place_year(caption):
    """'Pula, Croatia (2025)' -> ('Pula', 'Croatia', '2025')"""
    m = re.match(r"\s*([^,]+),\s*([^(]+?)\s*\((\d{4})\)", caption)
    return (m.group(1).strip(), m.group(2).strip(), m.group(3)) if m else (caption, "", "")

def short(text, n=155):
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"

def page(path, title, body, desc=None, cls="", image=None, ld=None):
    desc = desc or S["description"]
    full_title = title
    url = DOMAIN + path
    image = DOMAIN + (image or "/media/share.jpg")
    graph = [PERSON, {"@type": "WebSite", "@id": DOMAIN + "/#site", "url": DOMAIN + "/",
                      "name": "PoliteBastART – Vedran Štimac", "publisher": {"@id": DOMAIN + "/#vedran"}}]
    graph += ld or []
    ldjson = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")
    social = "".join(
        f'<li><a href="{S["social"][k]}" target="_blank" rel="noopener" aria-label="{k.title()}">'
        f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[k]}</svg></a></li>'
        for k in ("behance", "facebook", "instagram"))
    def nav(href, label):
        cur = ' aria-current="page"' if path == href else ""
        return f'<li><a href="{href}"{cur}>{label}</a></li>'
    work_cur = ' class="current"' if path in ("/illustrations", "/street-art") or path in MURAL_PATHS or path in ILL_PATHS else ""
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
<meta property="og:image" content="{image}">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(full_title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{image}">
<meta name="author" content="Vedran Štimac">
<script type="application/ld+json">{ldjson}</script>
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
<script src="/site.js" defer></script>{analytics()}
</body>
</html>
"""

def gallery(items, kind):
    """Ilustracije: [naziv, natpis, slika] -> klik otvara sliku.
    Murali: {"slug","name","caption","thumb","images","text"} -> klik vodi na stranicu murala."""
    out = []
    for it in items:
        if isinstance(it, dict) and "image" in it:
            name, caption = it["name"], it["caption"]
            link = f'<a href="/{it["slug"]}">'
            img = None
            src = ill_img(it)
            alt = f"Portrait illustration of {name} by Vedran Štimac (PoliteBastART)"
        elif isinstance(it, dict):
            name, caption = it["name"], it["caption"]
            link = f'<a href="/{it["slug"]}">'
            img = it.get("thumb") or it["images"][0]
            alt = f"{name}, {caption} – mural by Vedran Štimac"
        else:
            name, caption, img = it
            alt = f"Portrait illustration of {name} by Vedran Štimac (PoliteBastART)"
            link = f'<a href="{orig(img)}" class="lb" data-caption="{e(name)} — {e(caption)}">'
        out.append(
            f'<figure class="item">{link}'
            f'<img src="{src if img is None else web(img)}" alt="{e(alt)}" loading="lazy" decoding="async"></a>'
            f'<figcaption><strong>{e(name)}</strong><span>{e(caption)}</span></figcaption>'
            f'</figure>')
    return f'<div class="gallery {kind}">' + "\n".join(out) + "</div>"

def mural_page(m):
    photos = "".join(
        f'<a href="{orig(w)}" class="lb" data-caption="{e(m["name"])} — {e(m["caption"])}">'
        f'<img src="{web(w)}" alt="{e(m["name"])}, {e(m["caption"])} – photo {i} of {len(m["images"])}" loading="lazy" decoding="async"></a>'
        for i, w in enumerate(m["images"], 1))
    text = "".join(f"<p>{e(p)}</p>" for p in m["text"])
    return f"""
<section class="mural">
  <div class="mural-photos n{len(m['images'])}">{photos}</div>
  <div class="mural-text">
    <h1>{e(m['name'])}</h1>
    {text}
    <p class="place">{e(m['caption'])}</p>
    <p class="back"><a href="/street-art">← Street art</a></p>
  </div>
</section>"""

def ill_page(it, prev, nxt):
    src = ill_img(it)
    text = "".join(f"<p>{e(p)}</p>" for p in it["text"]) if S.get("show_illustration_text") else ""
    buy = (f'<p class="buy"><a class="btn" href="{it["etsy"]}" target="_blank" rel="noopener">Buy print on Etsy</a></p>'
           if it.get("etsy") else
           f'<p class="buy-note">Prints of other portraits are available in the <a href="{S["shop"]}" target="_blank" rel="noopener">Etsy shop</a>.</p>')
    return f"""
<section class="mural illus">
  <div class="mural-photos n1"><a href="{orig(it['image'])}" class="lb" data-caption="{e(it['name'])} — {e(it['caption'])}">
    <img src="{src}" alt="Portrait illustration of {e(it['name'])} by Vedran Štimac (PoliteBastART)"></a></div>
  <div class="mural-text">
    <h1>{e(it['name'])}</h1>
    <p class="series">Portrait illustration · Room of Portraits</p>
    {text}
    <p class="place">{e(it['caption'])}</p>
    {buy}
    <p class="back"><a href="/{prev['slug']}">← {e(prev['name'])}</a> &nbsp;·&nbsp; <a href="/illustrations">All illustrations</a> &nbsp;·&nbsp; <a href="/{nxt['slug']}">{e(nxt['name'])} →</a></p>
  </div>
</section>"""

def write(rel, html):
    p = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(html)

M = C["media"]

# HOME
write("index.html", page("/", "Vedran Štimac (PoliteBastART) – Illustrator & Muralist, Croatia", f"""
<h1 class="sr-only">Vedran Štimac (PoliteBastART) – illustrator and muralist from Pula, Croatia</h1>
<section class="hero-video">
  <video autoplay muted loop playsinline preload="auto" poster="/media/home-poster.jpg">
    <source src="/media/home.mp4" type="video/mp4">
  </video>
</section>""", cls="home",
    desc="Portrait illustrations and murals by Vedran Štimac (PoliteBastART), illustrator and street artist from Pula, based in Zagreb. Prints available on Etsy."))

# ABOUT
ex = []
for year, items in C["exhibitions"]:
    ex.append(f"<h3>{year}</h3>")
    for t, place in items:
        ex.append(f"<p>{e(t)}<br>{e(place)}</p>")
write("about/index.html", page("/about", "About Vedran Štimac – Illustrator & Street Artist", f"""
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
</section>""", desc="Vedran Štimac (PoliteBastART) is an illustrator, muralist and screen printer from Pula, Croatia. Socially engaged portraits on paper and on walls; exhibitions across the region.",
    image=web(M['about_portrait']), ld=[{"@type": "ProfilePage", "url": DOMAIN + "/about", "mainEntity": {"@id": DOMAIN + "/#vedran"}}]))

# ILLUSTRATIONS
write("illustrations/index.html", page("/illustrations", "Portrait Illustrations – Room of Portraits | Vedran Štimac", f"""
<section class="work">
  <h1 class="page-title">ILLUSTRATIONS</h1>
  {gallery(C['illustrations'], 'portraits')}
</section>""", desc='Portrait illustrations from the series "Room of Portraits" by Vedran Štimac: ink on paper, digitally coloured. Louise Michel, Mercedes Sosa, Nikola Tesla, Franz Kafka and more.',
    image=ill_img(C['illustrations'][0])))

# STRANICE ILUSTRACIJA (npr. /louise-michel)
IL = C["illustrations"]
for i, it in enumerate(IL):
    year = it["caption"][:4]
    art = {"@type": "VisualArtwork", "name": f"Portrait of {it['name']}", "artform": "Illustration",
           "artMedium": it["caption"][6:], "dateCreated": year, "url": DOMAIN + "/" + it["slug"],
           "creator": {"@id": DOMAIN + "/#vedran"}, "about": {"@type": "Person", "name": it["name"]},
           "image": DOMAIN + ill_img(it)}
    if S.get("show_illustration_text"):
        art["description"] = " ".join(it["text"])
    if it.get("etsy"):
        art["offers"] = {"@type": "Offer", "url": it["etsy"], "availability": "https://schema.org/InStock"}
    write(f"{it['slug']}/index.html", page("/" + it["slug"], f"{it['name']} – Portrait Illustration | Vedran Štimac",
          ill_page(it, IL[i - 1], IL[(i + 1) % len(IL)]),
          desc=(short(f"Portrait illustration of {it['name']} by Vedran Štimac (PoliteBastART), {year}. " + it["text"][-1])
                if S.get("show_illustration_text") else
                f"Portrait illustration of {it['name']} by Vedran Štimac (PoliteBastART), {year}. {it['caption'][6:]}. From the series Room of Portraits."),
          image=ill_img(it), ld=[art]))

# STREET ART
write("street-art/index.html", page("/street-art", "Murals & Street Art in Croatia and Abroad | Vedran Štimac", f"""
<section class="banner">
  <video autoplay muted loop playsinline preload="auto" poster="/media/street-art-poster.jpg">
    <source src="/media/street-art.mp4" type="video/mp4">
  </video>
  <h1>STREET ART</h1>
</section>
<section class="work">
  {gallery(C['street_art'], 'murals')}
</section>""", desc="Murals and street art by Vedran Štimac (PoliteBastART) in Pula, Zagreb, Krapina, Sisak, Umag, Ljubljana and Buenos Aires – each with its story and photos.",
    image=web(C['street_art'][0].get('thumb') or C['street_art'][0]['images'][0])))

# STRANICE MURALA (iste adrese kao na Wixu, npr. /julije-knifer)
for m in C["street_art"]:
    if isinstance(m, dict):
        city, country, year = place_year(m["caption"])
        art = {"@type": "VisualArtwork", "name": m["name"], "artform": "Mural", "url": DOMAIN + "/" + m["slug"],
               "creator": {"@id": DOMAIN + "/#vedran"}, "dateCreated": year,
               "locationCreated": {"@type": "Place", "address": {"@type": "PostalAddress", "addressLocality": city, "addressCountry": country}},
               "image": [DOMAIN + web(w) for w in m["images"]], "description": " ".join(m["text"])}
        write(f"{m['slug']}/index.html", page("/" + m["slug"], f"{m['name']} – {city}, {year} | Vedran Štimac", mural_page(m),
              desc=short(f"{m['name']} by Vedran Štimac, {city} {year}. " + m["text"][0]),
              image=web(m["images"][0]), ld=[art]))

# SITEMAP
urls = ["/", "/about", "/illustrations", "/street-art", "/contact"] + sorted(MURAL_PATHS) + sorted(ILL_PATHS)
open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{DOMAIN}{u}</loc></url>\n" for u in urls) + "</urlset>\n")

# CONTACT
write("contact/index.html", page("/contact", "Contact – Commission a Mural or Illustration | Vedran Štimac", f"""
<section class="contact">
  <h1>HAVE A PROJECT<br>IN MIND?</h1>
  <p>e-mail: <a href="mailto:{S['email']}">{S['email']}</a></p>
  <p>studio: {S['studio']}</p>
</section>""", desc="Commission a mural, portrait or illustration from Vedran Štimac (PoliteBastART). E-mail vedran.stimac1@gmail.com, studio at Ilica 73, Zagreb."))

# 404
write("404.html", page("/404", "Page not found | PoliteBastART", """
<section class="contact">
  <h1>PAGE NOT FOUND</h1>
  <p><a href="/">Back to home</a></p>
</section>"""))

print("Stranice generirane u", SITE)
