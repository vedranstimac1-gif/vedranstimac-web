"""Pomoćno za slike: WebP verzije (700 i 1400 px) i dimenzije za <img>.
Pokreće se iz build.py; radi samo slike kojima WebP još ne postoji."""
import json, os, re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "site", "media", "web")
OUT = os.path.join(ROOT, "site", "media", "webp")
DIMS_FILE = os.path.join(ROOT, "scripts", "image-dims.json")
SIZES = (700, 1400)

def prepare():
    dims = {}
    if os.path.exists(DIMS_FILE):
        dims = json.load(open(DIMS_FILE))
    for s in SIZES:
        os.makedirs(os.path.join(OUT, str(s)), exist_ok=True)
    for f in sorted(os.listdir(WEB)):
        if not f.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        base = os.path.splitext(f)[0]
        src = os.path.join(WEB, f)
        targets = [os.path.join(OUT, str(s), base + ".webp") for s in SIZES]
        mt = os.path.getmtime(src)
        if f in dims and all(os.path.exists(t) and os.path.getmtime(t) >= mt for t in targets):
            continue
        im = Image.open(src)
        im = im.convert("RGB")
        dims[f] = list(im.size)
        for s, t in zip(SIZES, targets):
            c = im.copy()
            c.thumbnail((s, s), Image.LANCZOS)
            c.save(t, "WEBP", quality=80, method=6)
    json.dump(dims, open(DIMS_FILE, "w"), indent=0, sort_keys=True)
    return dims

IMG_RE = re.compile(r'<img src="/media/web/([^"?]+)"([^>]*)>')

def enhance(html, dims):
    """Zamijeni <img src="/media/web/X.jpg"> s <picture> (WebP + JPG) i dodaj width/height."""
    def rep(m):
        f, rest = m.group(1), m.group(2)
        if f not in dims:
            return m.group(0)
        w, h = dims[f]
        base = os.path.splitext(f)[0]
        if "width=" not in rest:
            rest += f' width="{w}" height="{h}"'
        src = (f'/media/webp/700/{base}.webp 700w, /media/webp/1400/{base}.webp 1400w')
        return (f'<picture><source type="image/webp" srcset="{src}" '
                f'sizes="(max-width: 860px) 100vw, 50vw">'
                f'<img src="/media/web/{f}"{rest}></picture>')
    return IMG_RE.sub(rep, html)
