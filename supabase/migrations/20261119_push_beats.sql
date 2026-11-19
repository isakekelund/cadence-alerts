-- Heartbeats from Cadence's routines, read by the watchdog in the push function.
create table public.push_beats (
  name text primary key,
  last_at timestamptz not null,
  updated_at timestamptz not null default now()
);
alter table public.push_beats enable row level security;
revoke all on public.push_beats from anon, authenticated;
