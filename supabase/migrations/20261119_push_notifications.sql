-- Applied to Supabase project "Cadence" (bttliinpthrngngohbcv) on 2026-11-19.
create extension if not exists pg_cron;
create extension if not exists pg_net;

create table public.push_subscriptions (
  endpoint text primary key, p256dh text not null, auth text not null,
  tz text not null default 'Europe/Stockholm', vapid_key text not null, device text,
  code text not null, approved boolean not null default false,
  created_at timestamptz not null default now(), last_sent_at timestamptz
);
create table public.push_keys (
  id int primary key default 1 check (id = 1), public_key text, private_key text,
  cron_secret text not null default encode(extensions.gen_random_bytes(24), 'hex'),
  created_at timestamptz not null default now()
);
insert into public.push_keys (id) values (1);
create table public.push_outbox (
  key text primary key, title text not null, body text not null default '', url text,
  not_before timestamptz not null default now(), created_at timestamptz not null default now()
);
create table public.push_sent (
  endpoint text not null, key text not null, day date not null,
  sent_at timestamptz not null default now(), primary key (endpoint, key, day)
);
alter table public.push_subscriptions enable row level security;
alter table public.push_keys enable row level security;
alter table public.push_outbox enable row level security;
alter table public.push_sent enable row level security;
revoke all on public.push_subscriptions, public.push_keys, public.push_outbox, public.push_sent from anon, authenticated;

-- Cron (run once with execute_sql):
select cron.schedule('push-send', '*/5 * * * *', $$
  select net.http_post(
    url := 'https://bttliinpthrngngohbcv.supabase.co/functions/v1/push',
    headers := jsonb_build_object('content-type','application/json','x-cron-secret',(select cron_secret from public.push_keys where id = 1)),
    body := '{}'::jsonb, timeout_milliseconds := 30000)
$$);
select cron.schedule('push-cleanup', '17 3 * * *', $$
  delete from public.push_sent where day < current_date - 30;
  delete from public.push_outbox where created_at < now() - interval '30 days';
  delete from net._http_response where created < now() - interval '1 day';
$$);
