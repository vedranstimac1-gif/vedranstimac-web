#!/usr/bin/env python3
"""Generira statične HTML stranice u site/ iz content.json, na engleskom (/) i hrvatskom (/hr/).
Sadržaj se mijenja u content.json, zatim: python3 scripts/build.py

Hrvatska verzija je skrivena (noindex, bez prekidača jezika, nije u sitemapu)
dok se u content.json ne postavi site.hr_public = true.
"""
import json, os, re
from html import escape as e

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
C = json.load(open(os.path.join(ROOT, "content.json"), encoding="utf-8"))
S = C["site"]
M = C["media"]
DOMAIN = "https://www.vedranstimac.com"
HR_PUBLIC = bool(S.get("hr_public"))

def ver(f):
    """Kratki otisak datoteke – kad se CSS/JS promijeni, preglednik ga ponovo učita."""
    import hashlib
    return hashlib.md5(open(os.path.join(SITE, f), "rb").read()).hexdigest()[:8]
V_CSS, V_JS = ver("style.css"), ver("site.js")
LANGS = ("en", "hr")

# ---------- adrese ----------
PATHS = {
    "home":          {"en": "/",              "hr": "/hr/"},
    "about":         {"en": "/about",         "hr": "/hr/o-meni"},
    "work":          {"en": "/work",          "hr": "/hr/radovi"},
    "illustrations": {"en": "/illustrations", "hr": "/hr/ilustracije"},
    "street-art":    {"en": "/street-art",    "hr": "/hr/murali"},
    "paintings":     {"en": "/paintings",     "hr": "/hr/slike"},
    "contact":       {"en": "/contact",       "hr": "/hr/kontakt"},
}
for x in C["street_art"] + C["illustrations"]:
    PATHS[x["slug"]] = {"en": "/" + x["slug"], "hr": "/hr/" + x["slug"]}
MURALS = {m["slug"] for m in C["street_art"]}
ILLS = {i["slug"] for i in C["illustrations"]}

def P(key, lang):
    return PATHS[key][lang]

# ---------- tekstovi sučelja ----------
T = {
    "en": {
        "tagline": S["tagline"], "home": "HOME", "about": "ABOUT", "work": "WORK",
        "illustrations": "ILLUSTRATIONS", "street-art": "STREET ART", "paintings": "PAINTINGS", "contact": "CONTACT", "shop": "SHOP",
        "menu": "Menu", "about_h": "ABOUT", "exh_h": "EXHIBITIONS", "ill_h": "ILLUSTRATIONS", "street_h": "STREET ART",
        "contact_h": "HAVE A PROJECT<br>IN MIND?", "studio": "studio",
        "series": "Portrait illustration · Room of Portraits", "all_ill": "All illustrations",
        "back_murals": "← Street art", "buy": "Buy print on Etsy",
        "buy_note": 'Prints of other portraits are available in the <a href="{shop}" target="_blank" rel="noopener">Etsy shop</a>.',
        "photo": "photo", "of": "of", "portrait_of": "Portrait illustration of {n} by Vedran Štimac (PoliteBastART)",
        "mural_alt": "{n}, {c} – mural by Vedran Štimac", "me_alt": "Picture of Vedran", "me_mural_alt": "Vedran painting a mural",
        "locale": "en_US",
    },
    "hr": {
        "tagline": "Ilustracije i murali Vedrana Štimca", "home": "POČETNA", "about": "O MENI", "work": "RADOVI",
        "illustrations": "ILUSTRACIJE", "street-art": "MURALI", "paintings": "SLIKE", "contact": "KONTAKT", "shop": "SHOP",
        "menu": "Izbornik", "about_h": "O MENI", "exh_h": "IZLOŽBE", "ill_h": "ILUSTRACIJE", "street_h": "MURALI",
        "contact_h": "IMATE PROJEKT<br>NA UMU?", "studio": "atelijer",
        "series": "Portretna ilustracija · Room of Portraits", "all_ill": "Sve ilustracije",
        "back_murals": "← Murali", "buy": "Kupite print na Etsyju",
        "buy_note": 'Printovi ostalih portreta dostupni su u <a href="{shop}" target="_blank" rel="noopener">Etsy trgovini</a>.',
        "photo": "fotografija", "of": "od", "portrait_of": "Portretna ilustracija – {n}, autor Vedran Štimac (PoliteBastART)",
        "mural_alt": "{n}, {c} – mural, Vedran Štimac", "me_alt": "Vedran Štimac", "me_mural_alt": "Vedran slika mural",
        "locale": "hr_HR",
    },
}

# ---------- pomoćno ----------
def web(wid):
    stem = wid.split("~")[0] if "~" in wid else os.path.splitext(wid)[0]
    return "/media/web/" + stem + ".jpg"

def orig(wid):
    return "/media/orig/" + wid

def L(item, field, lang):
    """Polje na traženom jeziku (hrvatsko iz item['hr'] ako postoji)."""
    if lang == "hr" and field in item.get("hr", {}):
        return item["hr"][field]
    return item[field]

def place_year(caption):
    """'Pula, Croatia (2025)' -> ('Pula', 'Croatia', '2025')"""
    m = re.match(r"\s*([^,]+),\s*([^(]+?)\s*\((\d{4})\)", caption)
    return (m.group(1).strip(), m.group(2).strip(), m.group(3)) if m else (caption, "", "")

def short(text, n=155):
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"

ICONS = {
    "behance": '<path d="M9.2 11.6c.6-.3 1-.9 1-1.7 0-1.6-1.2-2.1-2.7-2.1H4v8.4h3.6c1.6 0 3-.7 3-2.4 0-1.1-.5-1.9-1.4-2.2zM5.6 9.1h1.6c.6 0 1.2.2 1.2.9s-.4.9-1 .9H5.6V9.1zm1.8 5.8H5.6v-2.3h1.8c.8 0 1.2.3 1.2 1.2 0 .8-.6 1.1-1.2 1.1zm8-4.9c-1.9 0-3.1 1.3-3.1 3.1 0 1.9 1.2 3.1 3.1 3.1 1.4 0 2.4-.7 2.8-2h-1.5c-.2.5-.7.8-1.3.8-.9 0-1.4-.5-1.5-1.5H18.4c.1-2-1-3.5-3-3.5zm-1.5 2.5c.1-.8.6-1.3 1.4-1.3.8 0 1.2.5 1.3 1.3h-2.7zm-.2-3.9h3.4v.9h-3.4z"/>',
    "facebook": '<path d="M13.4 20v-7.3h2.4l.4-2.8h-2.8V8.1c0-.8.2-1.4 1.4-1.4h1.5V4.2c-.3 0-1.1-.1-2.1-.1-2.1 0-3.6 1.3-3.6 3.7v2.1H8.2v2.8h2.4V20h2.8z"/>',
    "instagram": '<path d="M12 7.3a4.7 4.7 0 1 0 0 9.4 4.7 4.7 0 0 0 0-9.4zm0 7.7a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm4.9-8.9a1.1 1.1 0 1 1-2.2 0 1.1 1.1 0 0 1 2.2 0zM12 4.6c2.4 0 2.7 0 3.6.1 2.4.1 3.6 1.3 3.7 3.7.1.9.1 1.2.1 3.6s0 2.7-.1 3.6c-.1 2.4-1.3 3.6-3.7 3.7-.9.1-1.2.1-3.6.1s-2.7 0-3.6-.1c-2.4-.1-3.6-1.3-3.7-3.7-.1-.9-.1-1.2-.1-3.6s0-2.7.1-3.6c.1-2.4 1.3-3.6 3.7-3.7.9-.1 1.2-.1 3.6-.1z" fill="none" stroke="#fff" stroke-width="1.6"/>',
}

def analytics():
    """Cloudflare Web Analytics (bez kolačića). Token: content.json -> site.cf_analytics_token."""
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
    "image": DOMAIN + web(M["about_portrait"]),
    "email": "mailto:" + S["email"],
    "birthPlace": {"@type": "Place", "name": "Pula, Croatia"},
    "homeLocation": {"@type": "Place", "name": "Zagreb, Croatia"},
    "knowsAbout": ["Illustration", "Murals", "Street art", "Portrait illustration", "Screen printing"],
    "sameAs": [S["social"]["instagram"], S["social"]["behance"], S["social"]["facebook"], S["shop"]],
}

# ---------- okvir stranice ----------
def page(key, lang, title, body, desc, cls="", image=None, ld=None):
    t = T[lang]
    path = P(key, lang)
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

    def nav(k):
        cur = ' aria-current="page"' if key == k else ""
        return f'<li><a href="{P(k, lang)}"{cur}>{t[k]}</a></li>'
    work_cur = ' class="current"' if key in ("work", "illustrations", "street-art", "paintings") or key in MURALS or key in ILLS else ""

    other = "hr" if lang == "en" else "en"
    if HR_PUBLIC:
        alt = "".join(f'\n<link rel="alternate" hreflang="{l}" href="{DOMAIN}{P(key, l)}">' for l in LANGS)
        alt += f'\n<link rel="alternate" hreflang="x-default" href="{DOMAIN}{P(key, "en")}">'
        switch = (f'<li class="lang"><a href="{P(key, other)}" hreflang="{other}" lang="{other}">'
                  f'{other.upper()}</a></li>')
        robots = ""
    else:
        alt, switch = "", ""
        robots = '\n<meta name="robots" content="noindex, nofollow">' if lang == "hr" else ""

    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">{robots}
<link rel="canonical" href="{url}">{alt}
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{S['title']}">
<meta property="og:image" content="{image}">
<meta property="og:locale" content="{t['locale']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
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
<link rel="stylesheet" href="/style.css?v={V_CSS}">
</head>
<body class="{cls}">
<header class="site-header">
  <a class="brand" href="{P('home', lang)}">
    <span class="brand-name">{S['title']}</span>
    <span class="brand-tag">{t['tagline']}</span>
  </a>
  <button class="menu-toggle" aria-expanded="false" aria-controls="nav" aria-label="{t['menu']}"><span></span><span></span><span></span></button>
  <nav id="nav">
    <ul>
      {nav("home")}
      {nav("about")}
      <li class="has-sub"><a href="{P('work', lang)}"{work_cur}>{t['work']}</a>
        <ul class="sub">
          {nav("paintings")}
          {nav("street-art")}
          {nav("illustrations")}
        </ul>
      </li>
      {nav("contact")}
      <li><a href="{S['shop']}" target="_blank" rel="noopener">{t['shop']}</a></li>
      {switch}
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
<script src="/site.js?v={V_JS}" defer></script>{analytics()}
</body>
</html>
"""

# ---------- dijelovi ----------
def gallery(items, kind, lang):
    t = T[lang]
    out = []
    for it in items:
        name, caption = L(it, "name", lang), L(it, "caption", lang)
        if "image" in it:   # ilustracija
            src = web(it["image"])
            alt = t["portrait_of"].format(n=name)
        else:               # mural
            src = web(it.get("thumb") or it["images"][0])
            alt = t["mural_alt"].format(n=name, c=caption)
        out.append(
            f'<figure class="item"><a href="{P(it["slug"], lang)}">'
            f'<img src="{src}" alt="{e(alt)}" loading="lazy" decoding="async"></a>'
            f'<figcaption><strong>{e(name)}</strong><span>{e(caption)}</span></figcaption>'
            f'</figure>')
    return f'<div class="gallery {kind}">' + "\n".join(out) + "</div>"

def mural_page(m, lang):
    t = T[lang]
    name, cap, text = L(m, "name", lang), L(m, "caption", lang), L(m, "text", lang)
    n = len(m["images"])
    photos = "".join(
        f'<a href="{orig(w)}" class="lb" data-caption="{e(name)} — {e(cap)}">'
        f'<img src="{web(w)}" alt="{e(name)}, {e(cap)} – {t["photo"]} {i} {t["of"]} {n}" loading="lazy" decoding="async"></a>'
        for i, w in enumerate(m["images"], 1))
    paras = "".join(f"<p>{e(p)}</p>" for p in text)
    return f"""
<section class="mural">
  <div class="mural-photos n{n}">{photos}</div>
  <div class="mural-text">
    <h1>{e(name)}</h1>
    {paras}
    <p class="place">{e(cap)}</p>
    <p class="back"><a href="{P('street-art', lang)}">{t['back_murals']}</a></p>
  </div>
</section>"""

def ill_page(it, prev, nxt, lang):
    t = T[lang]
    cap = L(it, "caption", lang)
    text = "".join(f"<p>{e(p)}</p>" for p in it["text"]) if (S.get("show_illustration_text") and lang == "en") else ""
    buy = (f'<p class="buy"><a class="btn" href="{it["etsy"]}" target="_blank" rel="noopener">{t["buy"]}</a></p>'
           if it.get("etsy") else f'<p class="buy-note">{t["buy_note"].format(shop=S["shop"])}</p>')
    extra = "".join(
        f'<a href="{orig(w)}" class="lb" data-caption="{e(it["name"])} — {e(cap)}">'
        f'<img src="{web(w)}" alt="{e(t["portrait_of"].format(n=it["name"]))} ({i})" loading="lazy"></a>'
        for i, w in enumerate(it.get("extra", []), 2))
    return f"""
<section class="mural illus">
  <div class="mural-photos n1"><a href="{orig(it['image'])}" class="lb" data-caption="{e(it['name'])} — {e(cap)}">
    <img src="{web(it['image'])}" alt="{e(t['portrait_of'].format(n=it['name']))}"></a>{extra}</div>
  <div class="mural-text">
    <h1>{e(it['name'])}</h1>
    <p class="series">{t['series']}</p>
    {text}
    <p class="place">{e(cap)}</p>
    {buy}
    <p class="back"><a href="{P(prev['slug'], lang)}">← {e(prev['name'])}</a> &nbsp;·&nbsp; <a href="{P('illustrations', lang)}">{t['all_ill']}</a> &nbsp;·&nbsp; <a href="{P(nxt['slug'], lang)}">{e(nxt['name'])} →</a></p>
  </div>
</section>"""

def write(path, html):
    rel = path.strip("/")
    f = os.path.join(SITE, rel, "index.html") if rel else os.path.join(SITE, "index.html")
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, "w", encoding="utf-8").write(html)

def build(key, lang, *a, **k):
    write(P(key, lang), page(key, lang, *a, **k))

# ---------- stranice ----------
for lang in LANGS:
    t = T[lang]
    hr = lang == "hr"

    # POČETNA
    build("home", lang,
          "Vedran Štimac (PoliteBastART) – ilustrator i muralist, Pula / Zagreb" if hr else
          "Vedran Štimac (PoliteBastART) – Illustrator & Muralist, Croatia",
          f"""
<h1 class="sr-only">{"Vedran Štimac (PoliteBastART) – ilustrator i muralist iz Pule" if hr else "Vedran Štimac (PoliteBastART) – illustrator and muralist from Pula, Croatia"}</h1>
<section class="hero-video">
  <video autoplay muted loop playsinline preload="auto" poster="/media/home-poster.jpg">
    <source src="/media/home.mp4" type="video/mp4">
  </video>
</section>""",
          ("Portretne ilustracije i murali Vedrana Štimca (PoliteBastART), ilustratora i muralista iz Pule sa sjedištem u Zagrebu. Printovi dostupni na Etsyju."
           if hr else
           "Portrait illustrations and murals by Vedran Štimac (PoliteBastART), illustrator and street artist from Pula, based in Zagreb. Prints available on Etsy."),
          cls="home")

    # O MENI
    ex = []
    for year, items in (C["exhibitions_hr"] if hr else C["exhibitions"]):
        ex.append(f"<h3>{year}</h3>")
        for tt, place in items:
            ex.append(f"<p>{e(tt)}<br>{e(place)}</p>")
    build("about", lang,
          "O meni – Vedran Štimac, ilustrator i muralist" if hr else "About Vedran Štimac – Illustrator & Street Artist",
          f"""
<section class="about">
  <div class="about-text">
    <h1>{t['about_h']}</h1>
    {''.join(f'<p>{e(p)}</p>' for p in (C['about_hr'] if hr else C['about']))}
  </div>
  <div class="about-photo"><img src="{web(M['about_portrait'])}" alt="{t['me_alt']}"></div>
  <div class="about-photo wide"><img src="{web(M['about_mural'])}" alt="{t['me_mural_alt']}" loading="lazy"></div>
  <div class="exhibitions">
    <h2>{t['exh_h']}</h2>
    {''.join(ex)}
  </div>
</section>""",
          ("Vedran Štimac (PoliteBastART) – ilustrator, muralist i sitotiskar iz Pule. Društveno angažirani portreti na papiru i na zidovima, izložbe diljem regije."
           if hr else
           "Vedran Štimac (PoliteBastART) is an illustrator, muralist and screen printer from Pula, Croatia. Socially engaged portraits on paper and on walls; exhibitions across the region."),
          image=web(M["about_portrait"]),
          ld=[{"@type": "ProfilePage", "url": DOMAIN + P("about", lang), "mainEntity": {"@id": DOMAIN + "/#vedran"}}])

    # ILUSTRACIJE
    IL = C["illustrations"]
    build("illustrations", lang,
          "Portretne ilustracije – Room of Portraits | Vedran Štimac" if hr else
          "Portrait Illustrations – Room of Portraits | Vedran Štimac",
          f"""
<section class="work">
  <h1 class="page-title">{t['ill_h']}</h1>
  {gallery(IL, 'portraits', lang)}
</section>""",
          ("Portretne ilustracije iz serije „Room of Portraits“ Vedrana Štimca: tuš na papiru, digitalno bojano. Louise Michel, Mercedes Sosa, Nikola Tesla, Franz Kafka i drugi."
           if hr else
           'Portrait illustrations from the series "Room of Portraits" by Vedran Štimac: ink on paper, digitally coloured. Louise Michel, Mercedes Sosa, Nikola Tesla, Franz Kafka and more.'),
          image=web(IL[0]["image"]))

    for i, it in enumerate(IL):
        year = it["caption"][:4]
        cap = L(it, "caption", lang)
        art = {"@type": "VisualArtwork", "name": f"Portrait of {it['name']}", "artform": "Illustration",
               "artMedium": it["caption"][6:], "dateCreated": year, "url": DOMAIN + P(it["slug"], lang),
               "creator": {"@id": DOMAIN + "/#vedran"}, "about": {"@type": "Person", "name": it["name"]},
               "image": [DOMAIN + web(w) for w in [it["image"]] + it.get("extra", [])]}
        if S.get("show_illustration_text") and not hr:
            art["description"] = " ".join(it["text"])
        if it.get("etsy"):
            art["offers"] = {"@type": "Offer", "url": it["etsy"], "availability": "https://schema.org/InStock"}
        if hr:
            title = f"{it['name']} – portretna ilustracija | Vedran Štimac"
            desc = f"Portretna ilustracija – {it['name']}, autor Vedran Štimac (PoliteBastART), {cap}. Iz serije Room of Portraits."
        else:
            title = f"{it['name']} – Portrait Illustration | Vedran Štimac"
            desc = (short(f"Portrait illustration of {it['name']} by Vedran Štimac (PoliteBastART), {year}. " + it["text"][-1])
                    if S.get("show_illustration_text") else
                    f"Portrait illustration of {it['name']} by Vedran Štimac (PoliteBastART), {year}. {it['caption'][6:]}. From the series Room of Portraits.")
        build(it["slug"], lang, title, ill_page(it, IL[i - 1], IL[(i + 1) % len(IL)], lang), desc,
              image=web(it["image"]), ld=[art])

    # MURALI
    SA = C["street_art"]
    build("street-art", lang,
          "Murali i street art – Pula, Zagreb i svijet | Vedran Štimac" if hr else
          "Murals & Street Art in Croatia and Abroad | Vedran Štimac",
          f"""
<section class="banner">
  <video autoplay muted loop playsinline preload="auto" poster="/media/street-art-poster.jpg">
    <source src="/media/street-art.mp4" type="video/mp4">
  </video>
  <h1>{t['street_h']}</h1>
</section>
<section class="work">
  {gallery(SA, 'murals', lang)}
</section>""",
          ("Murali i street art Vedrana Štimca (PoliteBastART) u Puli, Pazinu, Zagrebu, Krapini, Sisku, Umagu, Ljubljani i Buenos Airesu – svaki sa svojom pričom i fotografijama."
           if hr else
           "Murals and street art by Vedran Štimac (PoliteBastART) in Pula, Pazin, Zagreb, Krapina, Sisak, Umag, Ljubljana and Buenos Aires – each with its story and photos."),
          image=web(SA[0].get("thumb") or SA[0]["images"][0]))

    for m in SA:
        name, cap, text = L(m, "name", lang), L(m, "caption", lang), L(m, "text", lang)
        city, country, year = place_year(cap)
        art = {"@type": "VisualArtwork", "name": name, "artform": "Mural", "url": DOMAIN + P(m["slug"], lang),
               "creator": {"@id": DOMAIN + "/#vedran"}, "dateCreated": year,
               "locationCreated": {"@type": "Place", "address": {"@type": "PostalAddress", "addressLocality": city, "addressCountry": country}},
               "image": [DOMAIN + web(w) for w in m["images"]], "description": " ".join(text)}
        build(m["slug"], lang, f"{name} – {city}, {year} | Vedran Štimac", mural_page(m, lang),
              short(f"{name}, {'autor' if hr else 'by'} Vedran Štimac, {city} {year}. " + text[0]),
              image=web(m["images"][0]), ld=[art])

    # RADOVI – popis velikim slovima
    cards = "".join(f'<li><a href="{P(k, lang)}">{t[k]}</a></li>' for k in ("paintings", "street-art", "illustrations"))
    build("work", lang,
          "Radovi – slike, murali i ilustracije | Vedran Štimac" if hr else "Work – Paintings, Street Art & Illustrations | Vedran Štimac",
          f"""
<section class="work-index">
  <h1 class="sr-only">{t['work']}</h1>
  <ul class="work-list">{cards}</ul>
</section>""",
          ("Radovi Vedrana Štimca (PoliteBastART): slike, murali i ilustracije." if hr else
           "Work by Vedran Štimac (PoliteBastART): paintings, murals and street art, and portrait illustrations."))

    # SLIKE (Vikendom rekreativno)
    PT = C["paintings"]
    works = []
    for w in PT["items"]:
        tech = w["tech_hr"] if hr else w["tech"]
        sub = "" if not w.get("name_en") else f' <span class="tr">({e(w["name_en"])})</span>'
        size = w.get("size", "")
        cap = f"{w['name']}, {w['year']}{'.' if hr else ''}, {tech}" + (f", {size}" if size else "")
        works.append(f"""
    <figure class="painting">
      <a href="{orig(w['image'])}" class="lb" data-caption="{e(cap)}">
        <img src="{web(w['image'])}" alt="{e(w['name'])} – {'slika, ' if hr else 'painting by '}Vedran Štimac" loading="lazy" decoding="async"></a>
      <figcaption><strong>{e(w['name'])}</strong>{sub}<span>{w['year']}{'.' if hr else ''}, {e(tech)}{', ' + size if size else ''}</span></figcaption>
    </figure>""")
    build("paintings", lang,
          "Vikendom rekreativno – slike | Vedran Štimac" if hr else "Vikendom rekreativno – Paintings | Vedran Štimac",
          f"""
<section class="paintings">
  <div class="paint-text">
    <h1>{e(PT['title'])}{f' <span class="tr">({e(PT["title_en"])})</span>' if PT.get("title_en") else ''}</h1>
    <p class="meta">{e(PT['meta_hr'] if hr else PT['meta_en'])}</p>
    {''.join(f'<p>{e(p)}</p>' for p in (PT['text_hr'] if hr else PT['text_en']))}
  </div>
  <div class="paint-works">{''.join(works)}
  </div>
</section>""",
          ("„Vikendom rekreativno“ – ciklus slika Vedrana Štimca (2026.): vikend kao pukotina u svakodnevici, kroz magični realizam i naivni izričaj. Ulje na platnu."
           if hr else
           "“Vikendom rekreativno” – a 2026 series of paintings by Vedran Štimac: the weekend as a crack in everyday life, through magical realism and a naive idiom. Oil on canvas."),
          image=web(PT["items"][0]["image"]))

    # KONTAKT
    build("contact", lang,
          "Kontakt – narudžba murala ili ilustracije | Vedran Štimac" if hr else
          "Contact – Commission a Mural or Illustration | Vedran Štimac",
          f"""
<section class="contact">
  <h1>{t['contact_h']}</h1>
  <p>e-mail: <a href="mailto:{S['email']}">{S['email']}</a></p>
  <p>{t['studio']}: {S['studio']}</p>
</section>""",
          ("Naručite mural, portret ili ilustraciju od Vedrana Štimca (PoliteBastART). E-mail vedran.stimac1@gmail.com, atelijer Ilica 73, Zagreb."
           if hr else
           "Commission a mural, portrait or illustration from Vedran Štimac (PoliteBastART). E-mail vedran.stimac1@gmail.com, studio at Ilica 73, Zagreb."))

# 404 (zajednička)
PATHS["404"] = {"en": "/404", "hr": "/404"}
open(os.path.join(SITE, "404.html"), "w", encoding="utf-8").write(page("404", "en", "Page not found | PoliteBastART", """
<section class="contact">
  <h1>PAGE NOT FOUND</h1>
  <p><a href="/">Back to home</a> · <a href="/hr/">Natrag na početnu</a></p>
</section>""", "Page not found."))

# SITEMAP
keys = ["home", "about", "work", "illustrations", "street-art", "paintings", "contact"] + sorted(MURALS) + sorted(ILLS)
urls = [P(k, "en") for k in keys] + ([P(k, "hr") for k in keys] if HR_PUBLIC else [])
open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{DOMAIN}{u}</loc></url>\n" for u in urls) + "</urlset>\n")

print("Stranice generirane u", SITE, "| HR javno:", HR_PUBLIC)
