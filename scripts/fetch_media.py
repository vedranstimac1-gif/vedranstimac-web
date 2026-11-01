#!/usr/bin/env python3
"""Preuzima sve slike i videe sa stare Wix stranice u mapu site/media.

Pokreće se jednom (GitHub Action ili ručno). Već preuzete datoteke preskače.
  media/orig/<wix-id>   originalna datoteka u punoj rezoluciji (arhiva, lightbox)
  media/web/<id>.jpg    smanjena verzija za galeriju (max 1200 px)
"""
import json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(ROOT, "site", "media")
C = json.load(open(os.path.join(ROOT, "content.json"), encoding="utf-8"))
IMG = "https://static.wixstatic.com/media/"
VID = "https://video.wixstatic.com/video/"

def get(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return "postoji"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest + ".part", "wb") as f:
                while True:
                    b = r.read(1 << 16)
                    if not b:
                        break
                    f.write(b)
            os.replace(dest + ".part", dest)
            return "ok"
        except Exception as e:
            err = e
            time.sleep(2)
    raise SystemExit(f"GREŠKA {url}: {err}")

jobs = []
images = [C["media"]["about_portrait"], C["media"]["about_mural"], C["media"]["og"]]
images += [x[2] for x in C["illustrations"]] + [x[2] for x in C["street_art"] if isinstance(x, list)]
for wid in images:
    if "~mv2" not in wid:
        continue  # nije sa Wixa (dodano kasnije, već je u repozitoriju)
    jobs.append((IMG + wid, os.path.join(MEDIA, "orig", wid)))
    if not wid.endswith(".gif"):
        stem = wid.split("~")[0]
        jobs.append((f"{IMG}{wid}/v1/fit/w_1200,h_1600,q_85/{stem}.jpg", os.path.join(MEDIA, "web", stem + ".jpg")))
for name, vid in (("home", C["media"]["home_video"]), ("street-art", C["media"]["street_video"])):
    jobs.append((f"{VID}{vid}/1080p/mp4/file.mp4", os.path.join(MEDIA, f"{name}.mp4")))
    jobs.append((f"{IMG}{vid}f000.jpg", os.path.join(MEDIA, f"{name}-poster.jpg")))

for url, dest in jobs:
    print(get(url, dest), os.path.relpath(dest, ROOT), flush=True)
print(f"Gotovo: {len(jobs)} datoteka.")
