#!/usr/bin/env bash
# Postavlja Dnevnik (www.vedranstimac.com/dnevnik/) na server: mali servis za spremanje i podsjetnike.
# Pokreni kao root na serveru, jednom:
#   curl -fsSL https://raw.githubusercontent.com/vedranstimac1-gif/vedranstimac-web/main/server/dnevnik/install.sh | bash
# Art Park i stranica ostaju kako jesu; ako nešto ne prođe provjeru, sve se vraća na staro.
# Ponovno pokretanje je sigurno: šifra i podaci ostaju.
set -euo pipefail

AP=/opt/artpark
CADDYFILE=$AP/Caddyfile
CADDY=artpark-caddy-1
REPO_DIR=/var/www/vedranstimac-web
DN=/opt/dnevnik

[ "$(id -u)" = 0 ] || { echo "Pokreni kao root."; exit 1; }
[ -f "$CADDYFILE" ] || { echo "Nema $CADDYFILE – javi Claudeu."; exit 1; }

echo "== 1/5 Svježa verzija stranice s GitHuba"
git -C "$REPO_DIR" pull --ff-only -q
[ -f "$REPO_DIR/server/dnevnik/server.js" ] && [ -f "$REPO_DIR/site/dnevnik/index.html" ] || { echo "Datoteke Dnevnika nisu na serveru – javi Claudeu."; exit 1; }

echo "== 2/5 Šifra i mapa za podatke"
mkdir -p "$DN/data"
if [ ! -f "$DN/.env" ]; then
  KEY=$(tr -dc 'a-z0-9' </dev/urandom | head -c 12 | sed 's/.\{4\}/&-/g; s/-$//')
  printf 'DNEVNIK_KEY=%s\nPODSJETNICI=21:00,23:00\n' "$KEY" > "$DN/.env"
  chmod 600 "$DN/.env"
fi
KEY=$(grep '^DNEVNIK_KEY=' "$DN/.env" | cut -d= -f2)

echo "== 3/5 Pokrećem servis u Dockeru"
NET=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$CADDY" | awk '{print $1}')
[ -n "$NET" ] || { echo "Ne nalazim Docker mrežu Caddyja – javi Claudeu."; exit 1; }
cat > "$DN/compose.yaml" <<EOF
services:
  dnevnik:
    image: node:22-alpine
    container_name: dnevnik
    restart: unless-stopped
    command: ["node", "/app/server.js"]
    env_file: .env
    environment:
      DATA_DIR: /data
      TZ: Europe/Zagreb
    volumes:
      - $REPO_DIR/server/dnevnik:/app:ro
      - $DN/data:/data
    networks: [web]
networks:
  web:
    external: true
    name: $NET
EOF
cd "$DN"
docker compose up -d --force-recreate
for i in $(seq 1 20); do
  docker exec dnevnik wget -qO- http://localhost:8080/dnevnik/api/health >/dev/null 2>&1 && break
  sleep 1
done
docker exec dnevnik wget -qO- http://localhost:8080/dnevnik/api/health >/dev/null 2>&1 || { echo "Servis se nije pokrenuo:"; docker logs --tail 20 dnevnik; exit 1; }
echo "   servis radi"

echo "== 4/5 Caddy: /dnevnik/api/ ide na servis"
if grep -q "reverse_proxy /dnevnik/api/" "$CADDYFILE"; then
  echo "   već postavljeno"
else
  grep -q "root \* /srv/vedranstimac" "$CADDYFILE" || { echo "Ne nalazim blok stranice u Caddyfileu – ništa nisam mijenjao. Javi Claudeu."; exit 1; }
  STAMP=$(date +%Y%m%d-%H%M%S)
  cp "$CADDYFILE" "$CADDYFILE.backup-$STAMP"
  awk '{print} /root \* \/srv\/vedranstimac/ && !done {print "\treverse_proxy /dnevnik/api/* dnevnik:8080"; done=1}' "$CADDYFILE" > /tmp/Caddyfile.novi
  cat /tmp/Caddyfile.novi > "$CADDYFILE"   # piše u istu datoteku (kontejner je vidi odmah)
  if ! docker exec "$CADDY" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/tmp/caddy-validate.log 2>&1; then
    cat "$CADDYFILE.backup-$STAMP" > "$CADDYFILE"
    echo "Caddyfile nije prošao provjeru – vratio sam staro, sve radi kao prije. Pošalji Claudeu:"
    tail -5 /tmp/caddy-validate.log; exit 1
  fi
  docker exec "$CADDY" caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
  echo "   dodano (kopija: Caddyfile.backup-$STAMP)"
fi

echo "== 5/5 Provjera izvana"
sleep 2
if curl -fsS https://www.vedranstimac.com/dnevnik/api/health >/dev/null; then echo "   https://www.vedranstimac.com/dnevnik/ radi"; else echo "   Vanjska provjera nije prošla – javi Claudeu."; fi

echo
echo "=============================================="
echo "  GOTOVO. Otvori na iPhoneu u Safariju:"
echo "    https://www.vedranstimac.com/dnevnik/"
echo "  Šifra (upiši je jednom u aplikaciji):"
echo "    $KEY"
echo "=============================================="
