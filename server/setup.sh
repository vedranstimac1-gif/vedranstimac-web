#!/usr/bin/env bash
# Postavlja vedranstimac.com na ovaj server (pokreni kao root, jednom):
#   curl -fsSL https://raw.githubusercontent.com/vedranstimac1-gif/vedranstimac-web/main/server/setup.sh | bash
# Ne dira postojeće stranice (Art Park ostaje kako jest).
set -euo pipefail

REPO=https://github.com/vedranstimac1-gif/vedranstimac-web
DIR=/var/www/vedranstimac-web

echo "== 1/4 Preuzimam stranicu s GitHuba"
command -v git >/dev/null || apt-get install -y git
if [ -d "$DIR/.git" ]; then git -C "$DIR" pull --ff-only; else git clone --depth 1 "$REPO" "$DIR"; fi

echo "== 2/4 Automatsko osvježavanje svakih 5 minuta"
CRON="*/5 * * * * git -C $DIR pull --ff-only -q"
( crontab -l 2>/dev/null | grep -v "$DIR" ; echo "$CRON" ) | crontab -

echo "== 3/4 Web server"
if systemctl is-active --quiet caddy; then
  WS=caddy
  if ! grep -q "vedranstimac.com" /etc/caddy/Caddyfile; then
    cat >> /etc/caddy/Caddyfile <<EOF

vedranstimac.com {
	redir https://www.vedranstimac.com{uri} permanent
}

www.vedranstimac.com {
	root * $DIR/site
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
  fi
  caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
  systemctl reload caddy
elif command -v nginx >/dev/null; then
  WS=nginx
  cp "$DIR/server/nginx-vedranstimac.conf" /etc/nginx/sites-available/vedranstimac
  ln -sf /etc/nginx/sites-available/vedranstimac /etc/nginx/sites-enabled/vedranstimac
  nginx -t
  systemctl reload nginx
  command -v certbot >/dev/null || apt-get install -y certbot python3-certbot-nginx
else
  echo "Nisam našao ni Caddy ni nginx. Javi Claudeu ovu poruku."; exit 1
fi

echo "== 4/4 Gotovo"
echo "Web server: $WS"
echo "IP adresa servera (upiši je u Cloudflare): $(curl -4 -fsS https://ifconfig.me || hostname -I | cut -d' ' -f1)"
if [ "$WS" = nginx ]; then
  echo "Kad Cloudflare DNS pokaže na ovaj server, pokreni:"
  echo "  certbot --nginx -d vedranstimac.com -d www.vedranstimac.com"
else
  echo "Caddy će sam napraviti SSL certifikat čim Cloudflare DNS pokaže na ovaj server."
fi
