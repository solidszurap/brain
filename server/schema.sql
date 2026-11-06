-- Ember's tables. Run once in Supabase: SQL Editor -> New query -> paste -> Run.
-- Row level security is on with no policies: the public ("anon") key can't read or
-- write anything. Only Ember's server, with the service key, can.

create table if not exists public.embers (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  self       jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.lines (
  id      bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  t       double precision not null,
  who     text not null,
  text    text not null,
  extra   jsonb
);
create index if not exists lines_user_t on public.lines (user_id, t);

create table if not exists public.usage (
  user_id    uuid not null references auth.users(id) on delete cascade,
  day        date not null,
  calls      integer not null default 0,        -- times Ember's mind ran (cost)
  messages   integer not null default 0,        -- messages that count against the free limit
  tokens_in  bigint not null default 0,
  tokens_out bigint not null default 0,
  primary key (user_id, day)
);
alter table public.usage add column if not exists messages integer not null default 0;

-- Ember Plus, as Stripe last reported it
create table if not exists public.plans (
  user_id      uuid primary key references auth.users(id) on delete cascade,
  status       text,
  customer     text,
  subscription text,
  updated_at   timestamptz not null default now()
);

-- what people send from the ⋯ menu's "Send feedback" (Supabase -> Table Editor -> feedback to read it)
create table if not exists public.feedback (
  id         bigserial primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  email      text,
  kind       text not null,                     -- idea, problem or other
  text       text not null,
  extra      jsonb,                             -- level, plan, screen, browser: to understand a problem
  created_at timestamptz not null default now()
);

alter table public.embers enable row level security;
alter table public.lines  enable row level security;
alter table public.usage  enable row level security;
alter table public.plans  enable row level security;
alter table public.feedback enable row level security;
