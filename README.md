# Cadence Alerts

Push notifications for Cadence on iPhone. Cadence itself runs as a claude.ai artifact, which cannot have its own service worker or Home Screen app, so this small web app does only that: it lives on the Home Screen, receives notifications, and opens Cadence when one is tapped.

- `index.html`, `sw.js`, `manifest.webmanifest`: the web app, served by GitHub Pages.
- `supabase/functions/push`: the Edge Function (Web Push with VAPID via `web-push`).
- `supabase/migrations`: tables and cron jobs in the Supabase project "Cadence".

## Sending a notification

Insert a row into `public.push_outbox` (Supabase connector, `execute_sql`). The cron job sends it within five minutes to every approved phone, once per phone per day.

```sql
insert into public.push_outbox (key, title, body)
values ('morning:2026-11-20', 'Morning brief is ready', 'Top item for today in one line')
on conflict (key) do nothing;
```

Use a stable `key` per event (`morning:<date>`, `news:<week>`) so a rerun never sends twice. `url` is optional and defaults to Cadence. `not_before` can delay a row.

## Approving a phone

New phones start unapproved and show a six-character code. Approve with:

```sql
update public.push_subscriptions set approved = true where code = 'A1B2C3';
```

No secrets live in this repo: the VAPID private key and the cron secret are in `public.push_keys`, readable only by the service role.

## Watchdog

Each routine reports in when it finishes: `python3 ~/.cadence-alerts/notify.py --beat <morning|sync|ranking|news>`. If one goes quiet for longer than its limit (see `WATCH` in the function), every approved device gets one notification for that outage. The heartbeats live in `push_beats`.

## Cadence apps on the Home Screen

`apps/` holds one launcher per Cadence app (built by `tools/make_launchers.py` from the icons in the Cadence repo). Open https://isakekelund.github.io/cadence-alerts/apps/ in Safari on the iPhone, tap an app, and add it to the Home Screen. A launcher opens its part of Cadence on claude.ai, so changes to the artifact show up without touching these pages.

`apps/cadence-apps.mobileconfig` (built by `tools/make_profile.py`) is a configuration profile with the same ten apps as full-screen web clips: own icon, no Safari bars. `apps/cadence-test.mobileconfig` holds Habits only, to try it first.
