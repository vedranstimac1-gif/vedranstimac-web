// Dnevnik – mali servis za dnevnu evidenciju (trening, posao, prehrana) i podsjetnike.
// Bez vanjskih paketa: radi na čistom Node.js 20+.
//
// Okruženje:
//   DNEVNIK_KEY   šifra koju aplikacija šalje u zaglavlju X-Kljuc (obavezno)
//   DATA_DIR      mapa za podatke (zadano /data)
//   PORT          zadano 8080
//   PODSJETNICI   vremena podsjetnika po zagrebačkom vremenu, zadano "21:00,23:00"
"use strict";
const http = require("http");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const KEY = process.env.DNEVNIK_KEY || "";
const DATA_DIR = process.env.DATA_DIR || "/data";
const PORT = Number(process.env.PORT || 8080);
const TIMES = (process.env.PODSJETNICI || "21:00,23:00").split(",").map(s => s.trim()).filter(Boolean);
const TZ = "Europe/Zagreb";
const SUBJECT = "https://www.vedranstimac.com";

// ---------- spremište ----------
function file(name) { return path.join(DATA_DIR, name); }
function load(name, fallback) {
  try { return JSON.parse(fs.readFileSync(file(name), "utf8")); } catch { return fallback; }
}
function save(name, value) {
  const tmp = file(name + ".tmp");
  fs.writeFileSync(tmp, JSON.stringify(value, null, 1));
  fs.renameSync(tmp, file(name));
}

const b64u = buf => Buffer.from(buf).toString("base64url");
const fromB64u = s => Buffer.from(s, "base64url");

// ---------- VAPID ključevi ----------
function vapidKeys() {
  let v = load("vapid.json", null);
  if (!v) {
    const { privateKey } = crypto.generateKeyPairSync("ec", { namedCurve: "prime256v1" });
    const jwk = privateKey.export({ format: "jwk" });
    v = { d: jwk.d, x: jwk.x, y: jwk.y };
    save("vapid.json", v);
  }
  return {
    publicRaw: Buffer.concat([Buffer.from([4]), fromB64u(v.x), fromB64u(v.y)]),
    privateKey: crypto.createPrivateKey({ key: { kty: "EC", crv: "P-256", d: v.d, x: v.x, y: v.y }, format: "jwk" }),
  };
}

function vapidHeader(endpoint, vapid) {
  const aud = new URL(endpoint).origin;
  const header = b64u(JSON.stringify({ typ: "JWT", alg: "ES256" }));
  const claims = b64u(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: SUBJECT }));
  const unsigned = header + "." + claims;
  const sig = crypto.sign("sha256", Buffer.from(unsigned), { key: vapid.privateKey, dsaEncoding: "ieee-p1363" });
  return "vapid t=" + unsigned + "." + b64u(sig) + ", k=" + b64u(vapid.publicRaw);
}

// ---------- Web Push enkripcija (RFC 8291, aes128gcm) ----------
const hmac = (key, data) => crypto.createHmac("sha256", key).update(data).digest();

function encrypt(payload, p256dh, auth, opts = {}) {
  const uaPublic = fromB64u(p256dh);
  const authSecret = fromB64u(auth);
  const ecdh = crypto.createECDH("prime256v1");
  if (opts.asPrivate) ecdh.setPrivateKey(fromB64u(opts.asPrivate)); else ecdh.generateKeys();
  const asPublic = ecdh.getPublicKey();
  const secret = ecdh.computeSecret(uaPublic);
  const salt = opts.salt ? fromB64u(opts.salt) : crypto.randomBytes(16);

  const prkKey = hmac(authSecret, secret);
  const keyInfo = Buffer.concat([Buffer.from("WebPush: info\0"), uaPublic, asPublic, Buffer.from([1])]);
  const ikm = hmac(prkKey, keyInfo);
  const prk = hmac(salt, ikm);
  const cek = hmac(prk, Buffer.from("Content-Encoding: aes128gcm\0\x01")).subarray(0, 16);
  const nonce = hmac(prk, Buffer.from("Content-Encoding: nonce\0\x01")).subarray(0, 12);

  const cipher = crypto.createCipheriv("aes-128-gcm", cek, nonce);
  const body = Buffer.concat([cipher.update(Buffer.concat([Buffer.from(payload), Buffer.from([2])])), cipher.final(), cipher.getAuthTag()]);
  const rs = Buffer.alloc(4); rs.writeUInt32BE(4096);
  return Buffer.concat([salt, rs, Buffer.from([asPublic.length]), asPublic, body]);
}

async function sendPush(sub, message, vapid) {
  const body = encrypt(JSON.stringify(message), sub.keys.p256dh, sub.keys.auth);
  const res = await fetch(sub.endpoint, {
    method: "POST",
    headers: {
      "Content-Encoding": "aes128gcm",
      "Content-Type": "application/octet-stream",
      TTL: "10800",
      Urgency: "high",
      Authorization: vapidHeader(sub.endpoint, vapid),
    },
    body,
  });
  return res.status;
}

async function pushAll(message) {
  const vapid = vapidKeys();
  const subs = load("subs.json", []);
  const keep = [];
  const results = [];
  for (const s of subs) {
    try {
      const status = await sendPush(s, message, vapid);
      results.push(status);
      if (status !== 404 && status !== 410) keep.push(s);
      if (status >= 400) console.log("push", status, new URL(s.endpoint).host);
    } catch (e) {
      keep.push(s);
      results.push("greška");
      console.log("push greška", e.message);
    }
  }
  if (keep.length !== subs.length) save("subs.json", keep);
  return results;
}

// ---------- vrijeme ----------
function zagrebNow() {
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-GB", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).formatToParts(new Date()).map(p => [p.type, p.value]));
  return { date: `${parts.year}-${parts.month}-${parts.day}`, time: `${parts.hour}:${parts.minute}` };
}

// Dan je upisan kad je odgovoreno na pitanje o prehrani (to se odgovara svaki dan).
function dayEntered(e) { return !!(e && e.prehrana); }

let lastReminder = load("podsjetnici.json", {});
async function tick() {
  const { date, time } = zagrebNow();
  for (const t of TIMES) {
    const id = date + " " + t;
    if (time < t || lastReminder[id]) continue;
    // ne šalji zakašnjele podsjetnike nakon restarta (više od 20 min kasnije)
    const [h, m] = t.split(":").map(Number), [ch, cm] = time.split(":").map(Number);
    lastReminder[id] = true;
    save("podsjetnici.json", Object.fromEntries(Object.entries(lastReminder).filter(([k]) => k >= date)));
    if (ch * 60 + cm - (h * 60 + m) > 20) continue;
    const days = load("days.json", {});
    if (dayEntered(days[date])) continue;
    const late = t >= "23:00";
    await pushAll({
      title: late ? "Još stigneš do ponoći" : "Kako je prošao dan?",
      body: late ? "Današnji dan još nije upisan – treba ti 10 sekundi." : "Upiši trening, posao i prehranu za danas.",
      url: "/dnevnik/",
    });
  }
}

// ---------- HTTP ----------
function send(res, status, obj) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  res.end(JSON.stringify(obj));
}
function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on("data", c => { size += c.length; if (size > 200000) { reject(new Error("prevelik zahtjev")); req.destroy(); } else chunks.push(c); });
    req.on("end", () => { try { resolve(chunks.length ? JSON.parse(Buffer.concat(chunks).toString("utf8")) : {}); } catch (e) { reject(e); } });
  });
}
function authorized(req) {
  const given = Buffer.from(String(req.headers["x-kljuc"] || ""));
  const want = Buffer.from(KEY);
  return KEY.length >= 8 && given.length === want.length && crypto.timingSafeEqual(given, want);
}
const fails = new Map();
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

function cleanEntry(date, e) {
  const list = (v, allowed) => Array.isArray(v) ? v.filter(x => typeof x === "string").slice(0, 20).map(x => x.slice(0, 60)) : [];
  return {
    datum: date,
    trening: { done: !!(e.trening && e.trening.done), vrste: list(e.trening && e.trening.vrste) },
    posao: { done: !!(e.posao && e.posao.done), vrste: list(e.posao && e.posao.vrste) },
    prehrana: ["da", "djelomicno", "ne"].includes(e.prehrana) ? e.prehrana : null,
    biljeska: typeof e.biljeska === "string" ? e.biljeska.slice(0, 2000) : "",
    updatedAt: Date.now(),
  };
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  const p = url.pathname.replace(/^\/dnevnik\/api/, "");
  const ip = String(req.headers["x-forwarded-for"] || req.socket.remoteAddress || "").split(",")[0];
  try {
    if (p === "/health") return send(res, 200, { ok: true });

    const f = fails.get(ip) || { n: 0, t: 0 };
    if (f.n >= 10 && Date.now() - f.t < 15 * 60 * 1000) return send(res, 429, { greska: "Previše pokušaja. Pokušaj za 15 minuta." });
    if (!authorized(req)) {
      fails.set(ip, { n: f.n + 1, t: Date.now() });
      return send(res, 401, { greska: "Kriva šifra." });
    }
    fails.delete(ip);

    if (p === "/days" && req.method === "GET") return send(res, 200, { days: load("days.json", {}), danas: zagrebNow().date });

    const m = p.match(/^\/days\/([\d-]+)$/);
    if (m && req.method === "PUT" && DATE_RE.test(m[1])) {
      const body = await readBody(req);
      const days = load("days.json", {});
      days[m[1]] = cleanEntry(m[1], body);
      save("days.json", days);
      return send(res, 200, { ok: true, entry: days[m[1]] });
    }

    if (p === "/vapid" && req.method === "GET") return send(res, 200, { publicKey: b64u(vapidKeys().publicRaw), podsjetnici: TIMES });

    if (p === "/subscribe" && req.method === "POST") {
      const { subscription } = await readBody(req);
      if (!subscription || !/^https:\/\//.test(subscription.endpoint || "") || !subscription.keys || !subscription.keys.p256dh || !subscription.keys.auth)
        return send(res, 400, { greska: "Neispravna pretplata." });
      const subs = load("subs.json", []).filter(s => s.endpoint !== subscription.endpoint);
      subs.push({ endpoint: subscription.endpoint, keys: { p256dh: subscription.keys.p256dh, auth: subscription.keys.auth }, od: Date.now() });
      save("subs.json", subs.slice(-10));
      return send(res, 200, { ok: true });
    }

    if (p === "/test" && req.method === "POST") {
      const r = await pushAll({ title: "Podsjetnici rade", body: "Ovako će izgledati podsjetnik kad zaboraviš upisati dan.", url: "/dnevnik/" });
      return send(res, 200, { poslano: r });
    }

    send(res, 404, { greska: "Nema toga." });
  } catch (e) {
    console.error(e);
    send(res, 500, { greska: "Greška na serveru." });
  }
});

if (require.main === module) {
  if (KEY.length < 8) { console.error("DNEVNIK_KEY nije postavljen (barem 8 znakova)."); process.exit(1); }
  fs.mkdirSync(DATA_DIR, { recursive: true });
  vapidKeys();
  server.listen(PORT, () => console.log("Dnevnik sluša na", PORT, "· podsjetnici", TIMES.join(", ")));
  setInterval(() => tick().catch(e => console.error("podsjetnik", e)), 30 * 1000);
}

module.exports = { encrypt, zagrebNow, server, cleanEntry };
