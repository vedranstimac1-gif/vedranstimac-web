#!/usr/bin/env bash
# Dodaje vedranstimac.com u postojeći Caddy (Docker) koji već poslužuje Art Park.
# Pokreni kao root na serveru, jednom:
#   curl -fsSL https://raw.githubusercontent.com/vedranstimac1-gif/vedranstimac-web/main/server/add-to-artpark-caddy.sh | bash
# Art Park aplikaciju ne dira; Caddy se samo ponovo pokrene (par sekundi).
set -euo pipefail

AP=/opt/artpark
SITE=/var/www/vedranstimac-web/site
CADDYFILE=$AP/Caddyfile
CONTAINER=artpark-caddy-1

cd "$AP"
[ -d "$SITE" ] || { echo "Nema $SITE – prvo pokreni setup.sh"; exit 1; }
[ -f "$CADDYFILE" ] || { echo "Nema $CADDYFILE"; exit 1; }

# Ime Caddy servisa i glavna compose datoteka
SVC=$(docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' "$CONTAINER")
MAIN=""
for f in compose.yaml compose.yml docker-compose.yaml docker-compose.yml; do
  [ -f "$f" ] && { MAIN=$f; break; }
done
[ -n "$MAIN" ] || { echo "Ne nalazim compose datoteku u $AP"; exit 1; }
OV="${MAIN%.*}.override.${MAIN##*.}"
echo "== Compose: $MAIN, servis: $SVC, dodatak: $OV"

STAMP=$(date +%Y%m%d-%H%M%S)
cp "$CADDYFILE" "$CADDYFILE.backup-$STAMP"

# 1) Mapa sa stranicom unutar Caddy kontejnera (u zasebnoj override datoteci)
if [ -f "$OV" ]; then
  if grep -q "/srv/vedranstimac" "$OV"; then
    echo "== Override već postoji."
  else
    echo "Datoteka $OV već postoji s drugim sadržajem – stajem da ništa ne pokvarim. Pošalji Claudeu: cat $AP/$OV"
    exit 1
  fi
else
  cat > "$OV" <<EOF
services:
  $SVC:
    volumes:
      - $SITE:/srv/vedranstimac:ro
EOF
  echo "== Napravljen $OV"
fi
docker compose config >/dev/null

# 2) Blok za vedranstimac.com u Caddyfile
if grep -q "vedranstimac.com" "$CADDYFILE"; then
  echo "== Caddyfile već sadrži vedranstimac.com"
else
  cat >> "$CADDYFILE" <<'EOF'

vedranstimac.com {
	redir https://www.vedranstimac.com{uri} permanent
}

www.vedranstimac.com {
	root * /srv/vedranstimac
	encode gzip
	@git path /.git*
	respond @git 404
	try_files {path} {path}/index.html
	file_server
	handle_errors {
		rewrite * /404.html
		file_server
	}
}
EOF
  echo "== Dodan blok u Caddyfile (kopija: Caddyfile.backup-$STAMP)"
fi

# 3) Provjera prije primjene; ako ne valja, vraćam staro
if ! docker exec "$CONTAINER" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/tmp/caddy-validate.log 2>&1; then
  cp "$CADDYFILE.backup-$STAMP" "$CADDYFILE"
  echo "Caddyfile nije prošao provjeru – vratio sam staro stanje, Art Park radi kao prije. Pošalji Claudeu:"
  tail -5 /tmp/caddy-validate.log
  exit 1
fi

# 4) Ponovo pokreni samo Caddy s novom mapom
docker compose up -d "$SVC"
sleep 3
docker exec "$CONTAINER" test -f /srv/vedranstimac/index.html && echo "== Caddy vidi stranicu: OK"

echo
echo "== GOTOVO"
echo "IP adresa servera (za Cloudflare): $(curl -4 -fsS https://ifconfig.me || hostname -I | cut -d' ' -f1)"
