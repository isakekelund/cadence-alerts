// Cadence Alerts: Web Push for Cadence, sent from Supabase.
//   GET  ?action=key          -> { publicKey }   (creates the VAPID key pair the first time)
//   POST ?action=subscribe    { subscription, tz, vapidKey, device } -> { code, approved }
//   POST ?action=status       { endpoint } -> { known, approved, code, keyOk }
//   POST ?action=unsubscribe  { endpoint }
//   POST ?action=test         { endpoint } -> sends a test notification to that phone (approved phones only)
//   POST (no action)          header x-cron-secret: sends due rows from push_outbox (run by pg_cron)
// New phones start unapproved, so nobody who finds the page can read Isak's notifications.
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});
const SUBJECT = "https://isakekelund.github.io/cadence-alerts/";
const APP_URL = "https://claude.ai/artifact/JCcrHbJtuJMPXvsqPoTBSy";
const ORIGINS = ["https://isakekelund.github.io", "http://localhost:8790"];
const PUSH_HOSTS = [/\.push\.apple\.com$/, /^fcm\.googleapis\.com$/, /\.push\.services\.mozilla\.com$/, /\.notify\.windows\.com$/];
const MAX_AGE_H = 18; // outbox rows older than this are not sent

function cors(req: Request) {
  const o = req.headers.get("origin") || "";
  return {
    "Access-Control-Allow-Origin": ORIGINS.includes(o) ? o : ORIGINS[0],
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
    "Vary": "Origin",
  };
}
const json = (req: Request, body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors(req), "Content-Type": "application/json" } });

async function getKeys() {
  let { data, error } = await db.from("push_keys").select("*").eq("id", 1).single();
  if (error) throw error;
  if (!data.public_key) {
    const k = webpush.generateVAPIDKeys();
    await db.from("push_keys").update({ public_key: k.publicKey, private_key: k.privateKey }).eq("id", 1).is("public_key", null);
    ({ data, error } = await db.from("push_keys").select("*").eq("id", 1).single());
    if (error) throw error;
  }
  return data as { public_key: string; private_key: string; cron_secret: string };
}

async function codeFor(endpoint: string) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(endpoint));
  return Array.from(new Uint8Array(h)).slice(0, 3).map((b) => b.toString(16).padStart(2, "0")).join("").toUpperCase();
}

function validEndpoint(e: unknown): e is string {
  if (typeof e !== "string" || e.length > 1024) return false;
  try {
    const u = new URL(e);
    return u.protocol === "https:" && PUSH_HOSTS.some((r) => r.test(u.hostname));
  } catch { return false; }
}

function localDay(tz: string, d = new Date()) {
  try { return new Intl.DateTimeFormat("en-CA", { timeZone: tz }).format(d); }
  catch { return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Stockholm" }).format(d); }
}

type Sub = { endpoint: string; p256dh: string; auth: string; tz: string; vapid_key: string; approved: boolean; code: string };

async function send(keys: { public_key: string; private_key: string }, sub: Sub, msg: Record<string, unknown>) {
  try {
    await webpush.sendNotification(
      { endpoint: sub.endpoint, keys: { p256dh: sub.p256dh, auth: sub.auth } },
      JSON.stringify(msg),
      { vapidDetails: { subject: SUBJECT, publicKey: keys.public_key, privateKey: keys.private_key }, TTL: 6 * 3600, urgency: "normal" },
    );
    await db.from("push_subscriptions").update({ last_sent_at: new Date().toISOString() }).eq("endpoint", sub.endpoint);
    return "sent";
  } catch (e) {
    const status = (e as { statusCode?: number }).statusCode;
    if (status === 404 || status === 410) {
      await db.from("push_subscriptions").delete().eq("endpoint", sub.endpoint);
      return "gone";
    }
    console.error("push failed", status, (e as Error).message);
    return "failed";
  }
}

async function run() {
  const keys = await getKeys();
  const since = new Date(Date.now() - MAX_AGE_H * 3600e3).toISOString();
  const { data: msgs } = await db.from("push_outbox").select("*")
    .lte("not_before", new Date().toISOString()).gte("created_at", since).order("created_at");
  const { data: subs } = await db.from("push_subscriptions").select("*").eq("approved", true).eq("vapid_key", keys.public_key);
  const out: Record<string, number> = { sent: 0, gone: 0, failed: 0, skipped: 0 };
  for (const m of msgs || []) {
    for (const s of (subs || []) as Sub[]) {
      const day = localDay(s.tz);
      // Claim the (phone, notification, day) row first; only a new row gets sent.
      const { data: claimed } = await db.from("push_sent")
        .upsert({ endpoint: s.endpoint, key: m.key, day }, { onConflict: "endpoint,key,day", ignoreDuplicates: true })
        .select();
      if (!claimed || !claimed.length) { out.skipped++; continue; }
      const r = await send(keys, s, { title: m.title, body: m.body, url: m.url || APP_URL, tag: m.key });
      out[r]++;
      if (r === "failed") await db.from("push_sent").delete().match({ endpoint: s.endpoint, key: m.key, day });
    }
  }
  return out;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: cors(req) });
  const action = new URL(req.url).searchParams.get("action") || "";
  try {
    if (action === "key") {
      const k = await getKeys();
      return json(req, { publicKey: k.public_key });
    }
    if (req.method !== "POST") return json(req, { error: "method" }, 405);
    const body = action ? await req.json().catch(() => ({})) : {};

    if (action === "subscribe") {
      const sub = body.subscription || {};
      const endpoint = sub.endpoint, p256dh = sub.keys?.p256dh, auth = sub.keys?.auth;
      if (!validEndpoint(endpoint) || typeof p256dh !== "string" || typeof auth !== "string" || p256dh.length > 200 || auth.length > 100)
        return json(req, { error: "bad subscription" }, 400);
      const k = await getKeys();
      if (body.vapidKey !== k.public_key) return json(req, { error: "stale key", publicKey: k.public_key }, 409);
      const code = await codeFor(endpoint);
      const tz = typeof body.tz === "string" && body.tz.length < 64 ? body.tz : "Europe/Stockholm";
      const device = typeof body.device === "string" ? body.device.slice(0, 120) : null;
      const { data: old } = await db.from("push_subscriptions").select("approved").eq("endpoint", endpoint).maybeSingle();
      const { error } = await db.from("push_subscriptions").upsert({
        endpoint, p256dh, auth, tz, device, code, vapid_key: k.public_key, approved: old?.approved ?? false,
      });
      if (error) throw error;
      return json(req, { code, approved: old?.approved ?? false });
    }

    if (action === "status" || action === "unsubscribe" || action === "test") {
      if (!validEndpoint(body.endpoint)) return json(req, { error: "bad endpoint" }, 400);
      const { data: s } = await db.from("push_subscriptions").select("*").eq("endpoint", body.endpoint).maybeSingle();
      if (action === "unsubscribe") {
        await db.from("push_subscriptions").delete().eq("endpoint", body.endpoint);
        return json(req, { ok: true });
      }
      const k = await getKeys();
      if (action === "status") {
        return json(req, s ? { known: true, approved: s.approved, code: s.code, keyOk: s.vapid_key === k.public_key } : { known: false });
      }
      if (!s) return json(req, { error: "unknown" }, 404);
      if (!s.approved) return json(req, { error: "not approved", code: s.code }, 403);
      // At most one test per phone per minute.
      const minute = new Date().toISOString().slice(0, 16);
      const { data: claimed } = await db.from("push_sent")
        .upsert({ endpoint: s.endpoint, key: "test:" + minute, day: localDay(s.tz) }, { onConflict: "endpoint,key,day", ignoreDuplicates: true })
        .select();
      if (!claimed || !claimed.length) return json(req, { error: "wait a minute" }, 429);
      const r = await send(k, s as Sub, { title: "Cadence", body: "Test notification. Notifications are on.", url: APP_URL, tag: "test" });
      return json(req, { result: r }, r === "sent" ? 200 : 502);
    }

    if (!action) {
      const k = await getKeys();
      if (req.headers.get("x-cron-secret") !== k.cron_secret) return json(req, { error: "forbidden" }, 403);
      return json(req, await run());
    }
    return json(req, { error: "unknown action" }, 400);
  } catch (e) {
    console.error(e);
    return json(req, { error: "server" }, 500);
  }
});
