# vedranstimac.com

Portfolio stranica Vedrana Štimca (PoliteBastART). Kopija stare Wix stranice, sada kao obična statična stranica na vlastitom serveru (Hetzner).

## Struktura

| Mapa / datoteka | Što je |
|---|---|
| `content.json` | Sav sadržaj: tekstovi, izložbe, popis ilustracija i murala |
| `scripts/build.py` | Iz `content.json` generira HTML stranice u `site/` |
| `scripts/fetch_media.py` | Jednokratno preuzimanje slika i videa sa stare Wix stranice |
| `site/` | Gotova stranica koju server prikazuje |
| `site/media/orig/` | Originalne slike u punoj rezoluciji (arhiva) |
| `site/media/web/` | Smanjene slike za galerije |
| `server/` | Postavke za nginx i skripta za postavljanje na server |

## Izmjena sadržaja

1. Promijeni `content.json` (ili dodaj sliku u `site/media/`).
2. `python3 scripts/build.py`
3. Commit i push na `main`. Server sam povlači promjene svakih 5 minuta.

## URL-ovi (isti kao na Wixu)

`/`, `/about`, `/illustrations`, `/street-art`, `/contact`; Shop vodi na Etsy.
