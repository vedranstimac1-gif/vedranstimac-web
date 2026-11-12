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
COMM_PUBLIC = bool(S.get("commissions_public"))
CILL_PUBLIC = COMM_PUBLIC and bool(S.get("commission_ill_public", True))  # ilustracije po narudžbi: skrivene dok nisu gotove  # narudžbe: skrivene (bez izbornika, noindex) dok nije true

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
    "work":          {"en": "/work",          "hr": "/hr/autorski-rad"},
    "illustrations": {"en": "/illustrations", "hr": "/hr/ilustracije"},
    "street-art":    {"en": "/street-art",    "hr": "/hr/street-art"},
    "paintings":     {"en": "/paintings",     "hr": "/hr/slike"},
    "contact":       {"en": "/contact",       "hr": "/hr/kontakt"},
    "commissions":   {"en": "/commissions",   "hr": "/hr/rad-po-narudzbi"},
    "c-ill":         {"en": "/commission-illustrations", "hr": "/hr/ilustracije-po-narudzbi"},
    "c-mur":         {"en": "/commission-murals",        "hr": "/hr/murali-po-narudzbi"},
}
CILL = C.get("commission_illustrations", [])
CMUR = C.get("commission_murals", [])
CPROJ = CILL + [m for m in CMUR if "slug" in m]
SHOP = C.get("shop", {"products": [], "sizes": []})
SHOP_PUBLIC = bool(SHOP.get("public"))
SHOPP = [next(i for i in C["illustrations"] if i["slug"] == sl) for sl in SHOP["products"]]
PATHS["shop"] = {"en": "/shop", "hr": "/hr/trgovina"}
PATHS["c-mur-preview"] = {"en": "/commission-murals-preview", "hr": "/hr/murali-po-narudzbi-pregled"}
MS = C.get("mural_service_hr")
PATHS["cart"] = {"en": "/shop/cart", "hr": "/hr/trgovina/kosarica"}
for it in SHOPP:
    PATHS["shop:" + it["slug"]] = {"en": f"/shop/{it['slug']}-print", "hr": f"/hr/trgovina/{it['slug']}-print"}
for x in C["street_art"] + C["illustrations"] + CPROJ:
    PATHS[x["slug"]] = {"en": "/" + x["slug"], "hr": "/hr/" + x["slug"]}
MURALS = {m["slug"] for m in C["street_art"]}
ILLS = {i["slug"] for i in C["illustrations"]}
COMM = {x["slug"] for x in CPROJ}
CILLS = {x["slug"] for x in CILL}

def P(key, lang):
    return PATHS[key][lang]

# ---------- tekstovi sučelja ----------
T = {
    "en": {
        "tagline": S["tagline"], "home": "HOME", "about": "ABOUT", "work": "WORK",
        "illustrations": "ILLUSTRATIONS", "street-art": "STREET ART", "paintings": "PAINTINGS", "contact": "CONTACT",
        "commissions": "COMMISSIONS", "c-ill": "ILLUSTRATIONS", "c-mur": "MURALS",
        "c-ill_h": "COMMISSION ILLUSTRATIONS", "c-mur_h": "COMMISSION MURALS",
        "back_c-ill": "← Commission illustrations", "back_c-mur": "← Commission murals", "client": "Client",
        "shop": "SHOP", "shop_h": "PRINTS", "cart": "Cart", "from": "from", "size": "Size", "add": "Add to cart", "added": "Added to cart",
        "print_kind": "Fine art print", "all_prints": "← All prints", "cart_h": "CART", "cart_empty": "Your cart is empty.",
        "subtotal": "Subtotal", "ship_note": "Shipping is calculated at checkout.", "checkout": "Checkout", "remove": "Remove",
        "soon": "Checkout is not open yet.", "qty": "Qty", "continue": "← Continue shopping",
        "details": ["Printed on museum-quality matte fine art paper (200 g/m²) with archival pigment inks.", "Printed to order and shipped worldwide in protective packaging, usually within 3–7 working days.", "Frame not included."],
        "menu": "Menu", "about_h": "ABOUT", "exh_h": "EXHIBITIONS", "ill_h": "ILLUSTRATIONS", "street_h": "STREET ART",
        "contact_h": "HAVE A PROJECT<br>IN MIND?", "studio": "studio",
        "series": "Room of Portraits", "all_ill": "All illustrations",
        "back_murals": "← Street art",
        "photo": "photo", "of": "of", "portrait_of": "{n} – illustration by Vedran Štimac (PoliteBastART)",
        "mural_alt": "{n}, {c} – mural by Vedran Štimac", "me_alt": "Picture of Vedran", "me_mural_alt": "Vedran painting a mural",
        "locale": "en_US",
    },
    "hr": {
        "tagline": "Slikarstvo, muralizam i ilustracije Vedrana Štimca", "home": "POČETNA", "about": "O MENI", "work": "AUTORSKI RAD",
        "illustrations": "ILUSTRACIJE", "street-art": "STREET ART", "paintings": "SLIKE", "contact": "KONTAKT",
        "commissions": "RAD PO NARUDŽBI", "c-ill": "ILUSTRACIJE", "c-mur": "MURALI",
        "c-ill_h": "ILUSTRACIJE PO NARUDŽBI", "c-mur_h": "MURALI PO NARUDŽBI",
        "back_c-ill": "← Ilustracije po narudžbi", "back_c-mur": "← Murali po narudžbi", "client": "Naručitelj",
        "shop": "TRGOVINA", "shop_h": "GRAFIKE", "cart": "Košarica", "from": "od", "size": "Veličina", "add": "Dodaj u košaricu", "added": "Dodano u košaricu",
        "print_kind": "Umjetnički print", "all_prints": "← Sve grafike", "cart_h": "KOŠARICA", "cart_empty": "Košarica je prazna.",
        "subtotal": "Ukupno", "ship_note": "Dostava se obračunava pri plaćanju.", "checkout": "Na plaćanje", "remove": "Ukloni",
        "soon": "Plaćanje još nije otvoreno.", "qty": "Kom.", "continue": "← Nastavi kupovati",
        "details": ["Tiskano na mat papiru muzejske kvalitete (200 g/m²) arhivskim pigmentnim tintama.", "Tiska se po narudžbi i šalje na adrese diljem svijeta u zaštitnom pakiranju, obično u roku od 3 do 7 radnih dana.", "Okvir nije uključen."],
        "menu": "Izbornik", "about_h": "O MENI", "exh_h": "IZLOŽBE", "ill_h": "ILUSTRACIJE", "street_h": "STREET ART",
        "contact_h": "IMATE PROJEKT<br>NA UMU?", "studio": "atelijer",
        "series": "Room of Portraits", "all_ill": "Sve ilustracije",
        "back_murals": "← Street art",
        "photo": "fotografija", "of": "od", "portrait_of": "{n} – ilustracija, autor Vedran Štimac (PoliteBastART)",
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

def capshow(cap, lang):
    """Prikaz mjesta i godine: na hrvatskom 'Pula, Hrvatska, 2025.'"""
    return re.sub(r"\s*\((\d{4})\)\s*$", r", \1.", cap) if lang == "hr" else cap

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
    "sameAs": [S["social"]["instagram"], S["social"]["behance"], S["social"]["facebook"]],
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
    comm_cur = ' class="current"' if key in ("commissions", "c-ill", "c-mur") or key in COMM else ""
    comm_menu = (f'''<li class="has-sub"><a href="{P('commissions', lang)}"{comm_cur}>{t['commissions']}</a>
        <ul class="sub">
          {nav("c-ill") if CILL_PUBLIC else ""}
          {nav("c-mur")}
        </ul>
      </li>''' if COMM_PUBLIC else "")

    other = "hr" if lang == "en" else "en"
    if HR_PUBLIC:
        alt = "".join(f'\n<link rel="alternate" hreflang="{l}" href="{DOMAIN}{P(key, l)}">' for l in LANGS)
        alt += f'\n<link rel="alternate" hreflang="x-default" href="{DOMAIN}{P(key, "en")}">'
        def lk(l, label):
            cur = ' class="on" aria-current="true"' if l == lang else ""
            return f'<a href="{P(key, l)}" hreflang="{l}" lang="{l}"{cur}>{label}</a>'
        switch = f'<li class="lang">{lk("hr", "HR")}<span>/</span>{lk("en", "ENG")}</li>'
        robots = ""
    else:
        alt, switch = "", ""
        robots = '\n<meta name="robots" content="noindex, nofollow">' if lang == "hr" else ""
    if key == "c-mur-preview" or (not SHOP_PUBLIC and (key in ("shop", "cart") or key.startswith("shop:"))) or \
       (not COMM_PUBLIC and (key in ("commissions", "c-ill", "c-mur") or key in COMM)) or \
       (not CILL_PUBLIC and (key == "c-ill" or key in CILLS)):
        robots = '\n<meta name="robots" content="noindex, nofollow">'

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
      {comm_menu}
      {nav("contact")}
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
        if "image" not in it:
            caption = capshow(caption, lang)
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
    name, cap, text = L(m, "name", lang), capshow(L(m, "caption", lang), lang), L(m, "text", lang)
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
    nm, pn, nn = L(it, "name", lang), L(prev, "name", lang), L(nxt, "name", lang)
    text = "".join(f"<p>{e(p)}</p>" for p in it["text"]) if (S.get("show_illustration_text") and lang == "en") else ""
    buy = ""
    extra = "".join(
        f'<a href="{orig(w)}" class="lb" data-caption="{e(nm)} — {e(cap)}">'
        f'<img src="{web(w)}" alt="{e(t["portrait_of"].format(n=nm))} ({i})" loading="lazy"></a>'
        for i, w in enumerate(it.get("extra", []), 2))
    return f"""
<section class="mural illus">
  <div class="mural-photos n1"><a href="{orig(it['image'])}" class="lb" data-caption="{e(nm)} — {e(cap)}">
    <img src="{web(it['image'])}" alt="{e(t['portrait_of'].format(n=nm))}"></a>{extra}</div>
  <div class="mural-text">
    <h1>{e(nm)}</h1>
    <p class="series">{t['series']}</p>
    {text}
    <p class="place">{e(cap)}</p>
    {buy}
    <p class="back"><a href="{P(prev['slug'], lang)}">← {e(pn)}</a> &nbsp;·&nbsp; <a href="{P('illustrations', lang)}">{t['all_ill']}</a> &nbsp;·&nbsp; <a href="{P(nxt['slug'], lang)}">{e(nn)} →</a></p>
  </div>
</section>"""

def cfull(x, lang):
    """Naručitelj i godina, uvijek oboje (za galeriju bez naslova)."""
    hr = lang == "hr"
    parts = [p for p in (L(x, "client", lang) if x.get("client") else "",
                         (x["year"] + ("." if hr else "")) if x.get("year") else "") if p]
    return ", ".join(parts)

def cmeta(x, lang):
    """Opis narudžbe: samo 'Naručitelj, godina' (bez mjesta)."""
    hr = lang == "hr"
    client = L(x, "client", lang) if x.get("client") else ""
    if "kind" in x and client == L(x, "name", lang):  # ilustracija: naziv = naručitelj, ne ponavljaj
        client = ""
    parts = [p for p in (client,
                         (x["year"] + ("." if hr else "")) if x.get("year") else "") if p]
    return ", ".join(parts)

def cgallery(items, kind, lang):
    out = []
    for x in items:
        if "ref" in x:  # mural koji već postoji među muralima
            m = next(s for s in C["street_art"] if s["slug"] == x["ref"])
            name, cap = L(m, "name", lang), cmeta(x, lang)
            src = web(m.get("thumb") or m["images"][0])
            slug = m["slug"]
        else:
            name, cap = L(x, "name", lang), cmeta(x, lang)
            src, slug = web(x["images"][0]), x["slug"]
        out.append(
            f'<figure class="item"><a href="{P(slug, lang)}">'
            f'<img src="{src}" alt="{e(name)}{" – " + e(cap) if cap else ""}, Vedran Štimac" loading="lazy" decoding="async"></a>'
            f'<figcaption><span>{e(cfull(x, lang))}</span></figcaption></figure>')
    return f'<div class="gallery {kind}">' + "\n".join(out) + "</div>"

def cproj_page(x, back, lang):
    t = T[lang]
    name, meta = L(x, "name", lang), cmeta(x, lang)
    n = len(x["images"])
    label = name + (f" — {meta}" if meta else "")
    photos = "".join(
        f'<a href="{orig(w)}" class="lb" data-caption="{e(label)}">'
        f'<img src="{web(w)}" alt="{e(name)}, Vedran Štimac – {i}/{n}" loading="lazy" decoding="async"></a>'
        for i, w in enumerate(x["images"], 1))
    paras = "".join(f"<p>{e(p)}</p>" for p in L(x, "text", lang)) if x.get("text") else ""
    kind = f'<p class="series">{e(L(x, "kind", lang)[:1].upper() + L(x, "kind", lang)[1:])}</p>' if x.get("kind") else ""
    place = f'<p class="place">{e(meta)}</p>' if meta else ""
    return f"""
<section class="mural illus">
  <div class="mural-photos n{n}">{photos}</div>
  <div class="mural-text">
    <h1>{e(name)}</h1>
    {kind}
    {paras}
    {place}
    <p class="back"><a href="{P(back, lang)}">{t['back_' + back]}</a></p>
  </div>
</section>"""

def home_lang(lang):
    if not HR_PUBLIC:
        return ""
    def lk(l, label):
        cur = ' class="on" aria-current="true"' if l == lang else ""
        return f'<a href="{P("home", l)}" hreflang="{l}" lang="{l}"{cur}>{label}</a>'
    return f'\n<p class="home-lang">{lk("hr", "HR")}<span>/</span>{lk("en", "ENG")}</p>'

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
          "Vedran Štimac (PoliteBastART)",
          f"""
<h1 class="sr-only">{"Vedran Štimac (PoliteBastART) – ilustrator i muralist iz Pule" if hr else "Vedran Štimac (PoliteBastART) – illustrator and muralist from Pula, Croatia"}</h1>
<section class="hero-video">
  <video autoplay muted loop playsinline preload="auto" poster="/media/home-poster.jpg">
    <source src="/media/home.mp4" type="video/mp4">
  </video>
</section>{home_lang(lang)}""",
          ("Slike, murali i ilustracije Vedrana Štimca (PoliteBastART), Pula / Zagreb."
           if hr else
           "Paintings, murals and illustrations by Vedran Štimac (PoliteBastART), Pula / Zagreb."),
          cls="home")

    # O MENI
    ex = []
    for year, items in (C["exhibitions_hr"] if hr else C["exhibitions"]):
        ex.append(f"<h3>{year}</h3>")
        for tt, place in items:
            ex.append(f"<p>{e(tt)}<br>{e(place)}</p>")
    build("about", lang,
          "O meni – Vedran Štimac (PoliteBastART)" if hr else "About – Vedran Štimac (PoliteBastART)",
          f"""
<section class="about">
  <div class="about-text">
    <h1>{t['about_h']}</h1>
    {''.join('<p>' + re.sub(r'\[\[(.+?)\]\]', lambda mm: f'<a href="{P("commissions", lang)}">{mm.group(1)}</a>', e(p)) + '</p>' for p in (C['about_hr'] if hr else C['about']))}
  </div>
  <div class="about-photo"><img src="{web(M['about_portrait'])}" alt="{t['me_alt']}"></div>
  <div class="about-photo wide"><img src="{web(M['about_mural'])}" alt="{t['me_mural_alt']}" loading="lazy"></div>
  <div class="exhibitions">
    <h2>{t['exh_h']}</h2>
    {''.join(ex)}
  </div>
</section>""",
          ("Vedran Štimac (PoliteBastART) – slikar, muralist i ilustrator iz Pule."
           if hr else
           "Vedran Štimac (PoliteBastART) – painter, muralist and illustrator from Pula."),
          image=web(M["about_portrait"]),
          ld=[{"@type": "ProfilePage", "url": DOMAIN + P("about", lang), "mainEntity": {"@id": DOMAIN + "/#vedran"}}])

    # ILUSTRACIJE
    IL = C["illustrations"]
    build("illustrations", lang,
          "Ilustracije – Vedran Štimac (PoliteBastART)" if hr else "Illustrations – Vedran Štimac (PoliteBastART)",
          f"""
<section class="work">
  <h1 class="page-title">{t['ill_h']}</h1>
  {gallery(IL, 'portraits', lang)}
</section>""",
          ("Ilustracije Vedrana Štimca (PoliteBastART) iz serije Room of Portraits: Albert Camus, Alfred Hitchcock, Nikola Tesla, Franz Kafka, Salvador Dalí, Che Guevara, Quentin Tarantino i drugi."
           if hr else
           "Illustrations by Vedran Štimac (PoliteBastART) from the series Room of Portraits: Albert Camus, Alfred Hitchcock, Nikola Tesla, Franz Kafka, Salvador Dalí, Che Guevara, Quentin Tarantino and more."),
          image=web(IL[0]["image"]))

    for i, it in enumerate(IL):
        year = it["caption"][:4]
        cap = L(it, "caption", lang)
        nm = L(it, "name", lang)
        art = {"@type": "VisualArtwork", "name": nm, "artform": "Illustration",
               "artMedium": it["caption"][6:], "dateCreated": year, "url": DOMAIN + P(it["slug"], lang),
               "creator": {"@id": DOMAIN + "/#vedran"}, "about": {"@type": "Person", "name": it["name"]},
               "image": [DOMAIN + web(w) for w in [it["image"]] + it.get("extra", [])]}
        if S.get("show_illustration_text") and not hr:
            art["description"] = " ".join(it["text"])
        if hr:
            title = f"{nm} – ilustracija | Vedran Štimac (PoliteBastART)"
            desc = f"{nm} – ilustracija, autor Vedran Štimac (PoliteBastART), {cap}. Iz serije Room of Portraits."
        else:
            kind_en = "Illustration" if it.get("not_portrait") else "Portrait Illustration"
            title = f"{nm} – {kind_en} | Vedran Štimac (PoliteBastART)"
            desc = (short(f"{nm} – {kind_en.lower()} by Vedran Štimac (PoliteBastART), {year}. " + it["text"][0])
                    if (S.get("show_illustration_text") and it["text"]) else
                    f"{nm} – illustration by Vedran Štimac (PoliteBastART), {year}. {it['caption'][6:]}. From the series Room of Portraits.")
        build(it["slug"], lang, title, ill_page(it, IL[i - 1], IL[(i + 1) % len(IL)], lang), desc,
              image=web(it["image"]), ld=[art])

    # MURALI
    SA = C["street_art"]
    build("street-art", lang,
          "Street art – Vedran Štimac (PoliteBastART)",
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
              short(f"{name}, {'autor' if hr else 'by'} Vedran Štimac, {city} {year}. " + (text[0] if text else "")),
              image=web(m["images"][0]), ld=[art])

    # RADOVI – popis velikim slovima
    cards = "".join(f'<li><a href="{P(k, lang)}">{t[k]}</a></li>' for k in ("paintings", "street-art", "illustrations"))
    build("work", lang,
          "Autorski rad – Vedran Štimac (PoliteBastART)" if hr else "Work – Vedran Štimac (PoliteBastART)",
          f"""
<section class="work-index">
  <h1 class="sr-only">{t['work']}</h1>
  <ul class="work-list">{cards}</ul>
</section>""",
          ("Autorski rad Vedrana Štimca (PoliteBastART): slike, street art i ilustracije." if hr else
           "Work by Vedran Štimac (PoliteBastART): paintings, street art and illustrations."))

    # SLIKE (Vikendom rekreativno)
    PT = C["paintings"]
    works = []
    for w in PT["items"]:
        tech = w["tech_hr"] if hr else w["tech"]
        sub = "" if (hr or not w.get("name_en")) else f' <span class="tr">({e(w["name_en"])})</span>'
        size = w.get("size", "")
        cap = f"{w['name']}, {w['year']}{'.' if hr else ''}, {tech}" + (f", {size}" if size else "")
        works.append(f"""
    <figure class="painting">
      <a href="{orig(w['image'])}" class="lb" data-caption="{e(cap)}">
        <img src="{web(w['image'])}" alt="{e(w['name'])} – {'slika, ' if hr else 'painting by '}Vedran Štimac" loading="lazy" decoding="async"></a>
      <figcaption><strong>{e(w['name'])}</strong>{sub}<span>{w['year']}{'.' if hr else ''}, {e(tech)}{', ' + size if size else ''}</span></figcaption>
    </figure>""")
    build("paintings", lang,
          "Vikendom rekreativno – Vedran Štimac (PoliteBastART)",
          f"""
<section class="paintings">
  <div class="paint-text">
    <h1>{e(PT['title'])}{f' <span class="tr">({e(PT["title_en"])})</span>' if (PT.get("title_en") and not hr) else ''}</h1>
    <p class="meta">{e(PT['meta_hr'] if hr else PT['meta_en'])}</p>
    {''.join(f'<p>{e(p)}</p>' for p in (PT['text_hr'] if hr else PT['text_en']))}
  </div>
  <div class="paint-works">{''.join(works)}
  </div>
</section>""",
          ("Vikendom rekreativno – ciklus slika Vedrana Štimca (PoliteBastART), 2026.: vikend kao pukotina u svakodnevici, kroz magični realizam i naivni izričaj."
           if hr else
           "Vikendom rekreativno – a 2026 series of paintings by Vedran Štimac (PoliteBastART): the weekend as a crack in everyday life, through magical realism and a naive idiom."),
          image=web(PT["items"][0]["image"]))

    # PO NARUDŽBI
    clist = "".join(f'<li><a href="{P(k, lang)}">{t[k + "_h"]}</a></li>' for k in (("c-ill", "c-mur") if CILL_PUBLIC else ("c-mur",)))
    build("commissions", lang,
          "Rad po narudžbi – Vedran Štimac (PoliteBastART)" if hr else "Commissions – Vedran Štimac (PoliteBastART)",
          f"""
<section class="work-index">
  <h1 class="sr-only">{t['commissions']}</h1>
  <ul class="work-list">{clist}</ul>
</section>""",
          ("Ilustracije i murali po narudžbi Vedrana Štimca (PoliteBastART): naslovnice, plakati, ilustracije za tisak te oslikavanje unutarnjih i vanjskih zidnih površina autorskim radom." if hr else
           "Commissioned illustrations and murals by Vedran Štimac (PoliteBastART): covers, posters, editorial illustration, and original murals for interior and exterior walls."))
    build("c-ill", lang,
          "Ilustracije po narudžbi – Vedran Štimac (PoliteBastART)" if hr else
          "Commission Illustrations – Vedran Štimac (PoliteBastART)",
          f"""
<section class="work">
  <h1 class="page-title">{t['c-ill_h']}</h1>
  {cgallery(CILL, 'portraits', lang)}
</section>""",
          ("Ilustracije po narudžbi Vedrana Štimca (PoliteBastART): naslovnice, plakati, ilustracije za tisak i dizajn za proizvode." if hr else
           "Commissioned illustrations by Vedran Štimac (PoliteBastART): covers, posters, editorial illustration and product design."),
          image=web(CILL[0]["images"][0]))
    build("c-mur", lang,
          "Murali po narudžbi – Vedran Štimac (PoliteBastART)" if hr else
          "Commission Murals – Vedran Štimac (PoliteBastART)",
          f"""
<section class="banner">
  <video autoplay muted loop playsinline preload="auto" poster="/media/commission-murals-poster.jpg?v={ver('media/commission-murals-poster.jpg')}">
    <source src="/media/commission-murals.mp4?v={ver('media/commission-murals.mp4')}" type="video/mp4">
  </video>
  <h1>{t['c-mur_h']}</h1>
</section>
<section class="work">
  {cgallery(CMUR, 'murals', lang)}
</section>""",
          ("Murali po narudžbi Vedrana Štimca (PoliteBastART): oslikavanje unutarnjih i vanjskih zidnih površina autorskim radom." if hr else
           "Commissioned murals by Vedran Štimac (PoliteBastART): original murals for interior and exterior walls."),
          image=web(CMUR[0]["images"][0]))
    if hr and MS:
        email = S.get("email", "")
        svc = f"""
<section class="service">
  <h2>{e(MS['title'])}</h2>
  {''.join(f'<p>{e(p)}</p>' for p in MS['intro'])}
  <h3>{e(MS['steps_h'])}</h3>
  <ol>{''.join(f'<li>{e(x)}</li>' for x in MS['steps'])}</ol>
  <h3>{e(MS['faq_h'])}</h3>
  <dl>{''.join(f'<dt>{e(q)}</dt><dd>{e(a)}</dd>' for q, a in MS['faq'])}</dl>
  <p class="cta">{e(MS['cta'])}</p>
  <p class="cta-mail"><a href="mailto:{email}">{email}</a></p>
</section>"""
        mur_body = f"""
<section class="banner">
  <video autoplay muted loop playsinline preload="auto" poster="/media/commission-murals-poster.jpg?v={ver('media/commission-murals-poster.jpg')}">
    <source src="/media/commission-murals.mp4?v={ver('media/commission-murals.mp4')}" type="video/mp4">
  </video>
  <h1>{t['c-mur_h']}</h1>
</section>
<section class="work">
  {cgallery(CMUR, 'murals', lang)}
</section>"""
        build("c-mur-preview", lang, "Murali po narudžbi (pregled) – Vedran Štimac (PoliteBastART)", mur_body + svc,
              "Pregled", image=web(CMUR[0]["images"][0]))
    for back, items, form in (("c-ill", CILL, "Illustration"), ("c-mur", [m for m in CMUR if "slug" in m], "Mural")):
        for x in items:
            name, client, meta = L(x, "name", lang), L(x, "client", lang), cmeta(x, lang)
            art = {"@type": "VisualArtwork", "name": x["name"], "artform": form, "url": DOMAIN + P(x["slug"], lang),
                   "creator": {"@id": DOMAIN + "/#vedran"}, "image": [DOMAIN + web(w) for w in x["images"]]}
            if x.get("year"):
                art["dateCreated"] = x["year"]
            if client:
                art["sourceOrganization"] = {"@type": "Organization", "name": client}
            what = L(x, "kind", lang) if x.get("kind") else ("mural po narudžbi" if hr else "commissioned mural")
            who = f" {'za' if hr else 'for'} {client}" if client and client != name else ""
            yr = f", {x['year']}{'.' if hr else ''}" if x.get("year") else ""
            desc = f"{name} – {what}{who}{yr}. {'Autor' if hr else 'By'} Vedran Štimac (PoliteBastART)."
            if x.get("text"):
                desc = short(desc + " " + L(x, "text", lang)[0])
            yr = f", {x['year']}{'.' if hr else ''}" if x.get("year") else ""
            build(x["slug"], lang, f"{name} – {what}{yr} | Vedran Štimac (PoliteBastART)", cproj_page(x, back, lang), desc,
                  image=web(x["images"][0]), ld=[art])

    # TRGOVINA (skrivena dok shop.public nije true)
    if SHOPP:
        sizes = SHOP["sizes"]; low = min(z["price"] for z in sizes)
        bar = f'<p class="shop-bar"><a href="{P("cart", lang)}" class="cart-link">{t["cart"]} (<span class="cart-count">0</span>)</a></p>'
        cards = "".join(
            f'<figure class="item"><a href="{P("shop:" + it["slug"], lang)}" style="cursor:pointer">'
            f'<img src="{web(it["image"])}" alt="{e(L(it, "name", lang))} – {t["print_kind"].lower()}" loading="lazy"></a>'
            f'<figcaption><strong>{e(L(it, "name", lang))}</strong><span>{t["from"]} {low} €</span></figcaption></figure>'
            for it in SHOPP)
        build("shop", lang, ("Grafike – Vedran Štimac (PoliteBastART)" if hr else "Prints – Vedran Štimac (PoliteBastART)"),
              f"""
<section class="work shop">
  {bar}
  <h1 class="page-title">{t['shop_h']}</h1>
  <div class="gallery portraits">{cards}</div>
</section>""",
              ("Umjetnički printovi ilustracija Vedrana Štimca (PoliteBastART)." if hr else "Fine art prints of illustrations by Vedran Štimac (PoliteBastART)."))
        for it in SHOPP:
            nm = L(it, "name", lang)
            opts = "".join(
                f'<label class="size-opt"><input type="radio" name="size" value="{z["id"]}" data-price="{z["price"]}" data-label="{z["label"]}"{" checked" if k == 0 else ""}>'
                f'<span><b>{z["label"]}</b><i>{z["dim"]}</i><em>{z["price"]} €</em></span></label>'
                for k, z in enumerate(sizes))
            desc_p = "".join(f"<p>{e(p)}</p>" for p in it["text"]) if (lang == "en" and it["text"]) else ""
            body = f"""
<section class="mural illus product" data-slug="{it['slug']}" data-name="{e(nm)}" data-img="{web(it['image'])}" data-url="{P('shop:' + it['slug'], lang)}">
  {bar}
  <div class="mural-photos n1"><a href="{orig(it['image'])}" class="lb" data-caption="{e(nm)}"><img src="{web(it['image'])}" alt="{e(nm)} – {t['print_kind'].lower()}"></a></div>
  <div class="mural-text">
    <h1>{e(nm)}</h1>
    <p class="series">{t['print_kind']} · Room of Portraits</p>
    {desc_p}
    <form class="buy-form">
      <p class="opt-h">{t['size']}</p>
      <div class="sizes">{opts}</div>
      <button type="submit" class="btn">{t['add']} · <span class="price">{sizes[0]['price']}</span> €</button>
      <p class="added" hidden>{t['added']} – <a href="{P('cart', lang)}">{t['cart']}</a></p>
    </form>
    <ul class="details">{''.join(f'<li>{e(d)}</li>' for d in t['details'])}</ul>
    <p class="back"><a href="{P('shop', lang)}">{t['all_prints']}</a></p>
  </div>
</section>"""
            build("shop:" + it["slug"], lang, f"{nm} – {'umjetnički print' if hr else 'Fine Art Print'} | Vedran Štimac (PoliteBastART)", body,
                  (f"{nm} – umjetnički print ilustracije Vedrana Štimca (PoliteBastART)." if hr else f"{nm} – fine art print of the illustration by Vedran Štimac (PoliteBastART)."),
                  image=web(it["image"]))
        build("cart", lang, f"{t['cart']} – Vedran Štimac (PoliteBastART)", f"""
<section class="cart-page" data-empty="{e(t['cart_empty'])}" data-remove="{e(t['remove'])}" data-qty="{e(t['qty'])}">
  <h1 class="page-title">{t['cart_h']}</h1>
  <div class="cart-items"></div>
  <div class="cart-sum" hidden>
    <p class="subtotal">{t['subtotal']}: <b><span class="sum">0</span> €</b></p>
    <p class="note">{t['ship_note']}</p>
    <button class="btn checkout" type="button" data-soon="{e(t['soon'])}">{t['checkout']}</button>
    <p class="soon" hidden></p>
  </div>
  <p class="back"><a href="{P('shop', lang)}">{t['continue']}</a></p>
</section>""", t["cart"])

    # KONTAKT
    build("contact", lang,
          "Kontakt – Vedran Štimac (PoliteBastART)" if hr else "Contact – Vedran Štimac (PoliteBastART)",
          f"""
<section class="contact">
  <h1>{t['contact_h']}</h1>
  <p>e-mail: <a href="mailto:{S['email']}">{S['email']}</a></p>
  <p>{t['studio']}: {S['studio']}</p>
</section>""",
          ("Imate li projekt na umu? Javite se."
           if hr else
           "Have a project in mind? Get in touch."))

# 404 (zajednička)
PATHS["404"] = {"en": "/404", "hr": "/404"}
open(os.path.join(SITE, "404.html"), "w", encoding="utf-8").write(page("404", "en", "Page not found | PoliteBastART", """
<section class="contact">
  <h1>PAGE NOT FOUND</h1>
  <p><a href="/">Back to home</a> · <a href="/hr/">Natrag na početnu</a></p>
</section>""", "Page not found."))

# SITEMAP (sa slikama za Google Images)
IMG = {}
for it in C["illustrations"]:
    IMG[it["slug"]] = [web(w) for w in [it["image"]] + it.get("extra", [])]
for m in C["street_art"]:
    IMG[m["slug"]] = [web(w) for w in m["images"]]
for x in CPROJ:
    IMG[x["slug"]] = [web(w) for w in x["images"]]
IMG["paintings"] = [web(w["image"]) for w in C["paintings"]["items"]]
IMG["about"] = [web(M["about_portrait"])]
def urlxml(k, lang):
    imgs = "".join(f"<image:image><image:loc>{DOMAIN}{u}</image:loc></image:image>" for u in IMG.get(k, []))
    return f"  <url><loc>{DOMAIN}{P(k, lang)}</loc>{imgs}</url>\n"
keys = (["home", "about", "work", "illustrations", "street-art", "paintings", "contact"] + sorted(MURALS) + sorted(ILLS)
        + (["commissions", "c-mur"] + sorted(COMM - CILLS) if COMM_PUBLIC else [])
        + (["c-ill"] + sorted(CILLS) if CILL_PUBLIC else [])
        + (["shop"] + ["shop:" + it["slug"] for it in SHOPP] if SHOP_PUBLIC else []))
pairs = [(k, "en") for k in keys] + ([(k, "hr") for k in keys] if HR_PUBLIC else [])
open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
    + "".join(urlxml(k, l) for k, l in pairs) + "</urlset>\n")

print("Stranice generirane u", SITE, "| HR javno:", HR_PUBLIC)
