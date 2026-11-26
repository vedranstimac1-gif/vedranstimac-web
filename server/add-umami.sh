#!/usr/bin/env bash
# Postavlja Umami analitiku na stats.vedranstimac.com, uz postojeći Caddy (Art Park).
# PRIJE pokretanja: u Cloudflareu dodaj DNS zapis  A  stats  -> IP servera  (siv oblak, DNS only).
# Pokreni kao root na serveru, jednom:
#   curl -fsSL https://raw.githubusercontent.com/vedranstimac1-gif/vedranstimac-web/main/server/add-umami.sh | bash
# Art Park aplikaciju ne dira; Caddy samo učita novu postavku (bez prekida).
set -euo pipefail

AP=/opt/artpark
CADDYFILE=$AP/Caddyfile
CADDY=artpark-caddy-1
DIR=/opt/umami
HOST=stats.vedranstimac.com

[ -f "$CADDYFILE" ] || { echo "Nema $CADDYFILE"; exit 1; }
docker inspect "$CADDY" >/dev/null || { echo "Nema kontejnera $CADDY"; exit 1; }

# Mreža na kojoj je Caddy – Umami ide na istu, pa mu Caddy može proslijediti promet
NET=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$CADDY" | awk '{print $1}')
echo "== Caddy mreža: $NET"

mkdir -p "$DIR"
cd "$DIR"

# Tajne (samo prvi put)
if [ ! -f .env ]; then
  cat > .env <<EOF
DB_PASSWORD=$(openssl rand -hex 24)
APP_SECRET=$(openssl rand -hex 32)
EOF
  chmod 600 .env
  echo "== Napravljene lozinke u $DIR/.env"
fi

cat > docker-compose.yml <<EOF
services:
  umami:
    image: ghcr.io/umami-software/umami:latest
    container_name: umami
    environment:
      DATABASE_URL: postgresql://umami:\${DB_PASSWORD}@umami-db:5432/umami
      APP_SECRET: \${APP_SECRET}
    depends_on:
      umami-db:
        condition: service_healthy
    init: true
    restart: always
    networks: [default, caddy]
  umami-db:
    image: postgres:15-alpine
    container_name: umami-db
    environment:
      POSTGRES_DB: umami
      POSTGRES_USER: umami
      POSTGRES_PASSWORD: \${DB_PASSWORD}
    volumes:
      - umami-db-data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U umami -d umami"]
      interval: 5s
      timeout: 5s
      retries: 10
volumes:
  umami-db-data:
networks:
  caddy:
    external: true
    name: $NET
EOF

docker compose up -d
echo "== Umami pokrenut, čekam da se baza pripremi..."
for i in $(seq 1 40); do
  docker exec "$CADDY" wget -qO- http://umami:3000/api/heartbeat >/dev/null 2>&1 && { echo "== Umami odgovara"; break; }
  sleep 3
done

# Caddy blok
STAMP=$(date +%Y%m%d-%H%M%S)
cp "$CADDYFILE" "$CADDYFILE.backup-$STAMP"
if grep -q "$HOST" "$CADDYFILE"; then
  echo "== Caddyfile već sadrži $HOST"
else
  cat >> "$CADDYFILE" <<EOF

$HOST {
	encode gzip
	reverse_proxy umami:3000
}
EOF
  echo "== Dodan $HOST u Caddyfile (kopija: Caddyfile.backup-$STAMP)"
fi

if ! docker exec "$CADDY" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/tmp/caddy-validate.log 2>&1; then
  cp "$CADDYFILE.backup-$STAMP" "$CADDYFILE"
  echo "Caddyfile nije prošao provjeru – vratio sam staro stanje, sve radi kao prije. Pošalji Claudeu:"
  tail -5 /tmp/caddy-validate.log
  exit 1
fi
docker exec "$CADDY" caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile

echo
echo "== GOTOVO"
echo "Otvori https://$HOST  (prvi put može trebati minuta za HTTPS certifikat)"
echo "Prijava: admin / umami  -> ODMAH promijeni lozinku (Settings -> Profile)"
