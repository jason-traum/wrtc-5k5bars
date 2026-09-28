-- 5K 5 Bars database for a NEW Supabase project (not In.'s).
-- Paste this whole file into Supabase > SQL Editor > New query, then click Run. Safe to run again.
-- BEFORE RUNNING: put the organizer email on the line below. Add more organizers with the same insert.
-- Also turn on Authentication > Sign In / Providers > "Allow anonymous sign-ins" (runners join with a bib).

create table if not exists public.admins (email text primary key);
insert into public.admins (email) values (lower('YOUR_EMAIL_HERE')) on conflict do nothing;

-- ---------------------------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------------------------

-- The race itself: one row. start_at is a placeholder (Saturday after next, 2 PM) until the organizer sets it.
create table if not exists public.event (
  id smallint primary key default 1 check (id = 1),
  name text not null default 'Beer Club × WRTC 5K 5 Bars' check (char_length(name) <= 60),
  start_at timestamptz not null default ((date_trunc('week', now() at time zone 'America/New_York') + interval '12 days 14 hours') at time zone 'America/New_York'),
  go_at timestamptz,
  bib_max smallint not null default 300 check (bib_max between 1 and 999),
  updated_at timestamptz not null default now()
);
insert into public.event (id) values (1) on conflict do nothing;

-- The course, in order. Stop 0 is the start; the last stop is the finish.
create table if not exists public.stops (
  ord smallint primary key check (ord between 0 and 12),
  name text not null check (char_length(name) between 1 and 40),
  short text not null check (char_length(short) between 1 and 18),
  addr text not null default '' check (char_length(addr) <= 60),
  lat double precision not null check (lat between 39.8 and 40.2),
  lng double precision not null check (lng between -75.4 and -74.9),
  radius_m smallint not null default 150 check (radius_m between 30 and 400),
  km numeric(4, 2) not null default 0 check (km between 0 and 10),
  leave_by timestamptz
);
insert into public.stops (ord, name, short, addr, lat, lng, radius_m, km, leave_by)
select v.ord, v.name, v.short, v.addr, v.lat, v.lng, v.radius_m, v.km,
       case when v.mins is null then null else e.start_at + make_interval(mins => v.mins) end
from public.event e, (values
  (0, 'Rittenhouse Square', 'Rittenhouse', 'Start, 18th & Walnut', 39.9495, -75.1719, 150, 0.00, 0),
  (1, 'PHS Pop Up Garden', 'PHS Garden', '1438 South St', 39.94368, -75.16623, 120, 1.14, 45),
  (2, 'McGillin''s Olde Ale House', 'McGillin''s', '1310 Drury St', 39.95016, -75.16204, 120, 1.00, 85),
  (3, 'Independence Beer Garden', 'Indy Beer Garden', '100 S Independence Mall W', 39.94918, -75.15085, 150, 1.01, 125),
  (4, 'Bar 4', 'Bar 4', 'Still being picked', 39.95224, -75.14508, 150, 0.85, 165),
  (5, 'Morgan''s Pier', 'Morgan''s Pier', '221 N Columbus Blvd', 39.9553, -75.1393, 150, 0.85, null)
) as v(ord, name, short, addr, lat, lng, radius_m, km, mins)
where e.id = 1 and not exists (select 1 from public.stops);

-- A runner is a bib and a first name. auth_uid is the phone's anonymous sign-in, never shown to anyone.
create table if not exists public.runners (
  id uuid primary key default gen_random_uuid(),
  auth_uid uuid unique references auth.users (id) on delete set null,
  bib smallint not null unique check (bib between 1 and 999),
  name text not null check (char_length(btrim(name)) between 1 and 24),
  created_at timestamptz not null default now()
);

-- Every tap: "I'm at" (arrive) or "Leaving" (leave) a stop; leaving stop 0 is the runner's own Start.
-- Location itself is never stored, only the distance.
create table if not exists public.taps (
  id uuid primary key,
  runner_id uuid not null references public.runners (id) on delete cascade,
  stop smallint not null check (stop between 0 and 12),
  kind text not null check (kind in ('arrive', 'leave')),
  at timestamptz not null,
  verified boolean not null default false,
  dist_m integer check (dist_m between 0 and 100000),
  acc_m integer check (acc_m between 0 and 100000),
  source text not null default 'gps' check (source in ('gps', 'anyway', 'organizer')),
  created_at timestamptz not null default now(),
  unique (runner_id, stop, kind)
);
create index if not exists taps_runner_idx on public.taps (runner_id);

-- ---------------------------------------------------------------------------------------------
-- Access: signed-in phones (including anonymous runners) can read the race. Every write goes
-- through a function below that checks who is asking. Start from zero grants.
-- ---------------------------------------------------------------------------------------------
alter table public.admins enable row level security;
alter table public.event enable row level security;
alter table public.stops enable row level security;
alter table public.runners enable row level security;
alter table public.taps enable row level security;

grant usage on schema public to authenticated;
revoke all on public.admins, public.event, public.stops, public.runners, public.taps from anon, authenticated;
grant select on public.event, public.stops to authenticated;
-- Other runners see when and where you checked in, not how far off your GPS was.
grant select (id, runner_id, stop, kind, at, verified, source, created_at) on public.taps to authenticated;
grant select (id, bib, name, created_at) on public.runners to authenticated;

drop policy if exists event_read on public.event;
drop policy if exists stops_read on public.stops;
drop policy if exists runners_read on public.runners;
drop policy if exists taps_read on public.taps;
create policy event_read on public.event for select to authenticated using (true);
create policy stops_read on public.stops for select to authenticated using (true);
create policy runners_read on public.runners for select to authenticated using (true);
create policy taps_read on public.taps for select to authenticated using (true);

-- ---------------------------------------------------------------------------------------------
-- Functions
-- ---------------------------------------------------------------------------------------------
-- An organizer is a confirmed, non-anonymous account on the admins list that signed in with an email code
-- (not a password, so nobody can make a password account with an organizer's address and walk in).
create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
      select 1 from auth.users u join admins a on a.email = lower(u.email)
      where u.id = auth.uid() and u.email_confirmed_at is not null and not coalesce(u.is_anonymous, false))
    and exists (
      select 1 from jsonb_array_elements(coalesce(auth.jwt() -> 'amr', '[]'::jsonb)) m
      where m ->> 'method' in ('otp', 'magiclink'));
$$;

create or replace function public.my_runner() returns table (id uuid, bib smallint, name text)
language sql stable security definer set search_path = public as $$
  select r.id, r.bib, r.name from runners r where auth.uid() is not null and r.auth_uid = auth.uid();
$$;

-- Claim a bib. The same first name on a new phone moves the bib (Safari and the Home Screen app are separate).
create or replace function public.claim_bib(p_bib integer, p_name text) returns table (id uuid, bib smallint, name text)
language plpgsql security definer set search_path = public as $$
declare
  me uuid := auth.uid();
  nm text;
  mx integer;
  r runners;
begin
  if me is null then raise exception 'Not allowed: sign in first.'; end if;
  if char_length(p_name) > 60 then raise exception 'Use just your first name.'; end if;
  nm := btrim(regexp_replace(coalesce(p_name, ''), '\s+', ' ', 'g'));
  -- No invisible or direction-flipping characters on the leaderboard.
  if nm ~ '[\u0001-\u001f\u007f-\u009f\u200b-\u200f\u2028-\u202e\u2060-\u2069\ufeff]' then
    raise exception 'Use plain letters for your first name.';
  end if;
  select e.bib_max into mx from event e where e.id = 1;
  if p_bib is null or p_bib < 1 or p_bib > mx then raise exception 'Bibs run from 1 to %.', mx; end if;
  if nm = '' then raise exception 'Add your first name so people know who bib % is.', p_bib; end if;
  nm := left(nm, 24);
  select * into r from runners x where x.bib = p_bib for update;
  if found then
    if r.auth_uid = me then
      -- Same phone, same bib: this is a name fix.
      if r.name is distinct from nm then update runners x set name = nm where x.id = r.id returning * into r; end if;
      return query select r.id, r.bib, r.name;
      return;
    end if;
    if lower(r.name) <> lower(nm) then
      raise exception 'Bib % is already %''s. Check the number on your bib, or ask the organizer.', p_bib, r.name;
    end if;
    -- Moving a bib to a new phone is fine until it has checked in somewhere. After that only an organizer
    -- can free it, so nobody can take over a runner's bib using the name on the leaderboard.
    if r.auth_uid is not null and not is_admin() and exists (select 1 from taps t where t.runner_id = r.id) then
      raise exception 'Bib % is already checking in on another phone. Find an organizer to move it.', p_bib;
    end if;
    -- This phone's old bib: drop it if it never checked in, otherwise leave it for the organizer.
    delete from runners x where x.auth_uid = me and x.id <> r.id and not exists (select 1 from taps t where t.runner_id = x.id);
    update runners x set auth_uid = null where x.auth_uid = me and x.id <> r.id;
    update runners x set auth_uid = me where x.id = r.id;
    return query select r.id, r.bib, r.name;
    return;
  end if;
  begin
    -- This phone already has a bib: correct it (a typo at the bib table).
    update runners x set bib = p_bib, name = nm where x.auth_uid = me returning * into r;
    if not found then
      insert into runners (auth_uid, bib, name) values (me, p_bib, nm) returning * into r;
    end if;
  exception when unique_violation then
    raise exception 'Bib % was just taken. Check the number on your bib and try again.', p_bib;
  end;
  return query select r.id, r.bib, r.name;
end $$;

-- Save a tap from this phone. Taps made offline arrive later with their real time.
create or replace function public.add_tap(p_id uuid, p_stop integer, p_kind text, p_at timestamptz, p_verified boolean, p_dist integer, p_acc integer, p_source text)
returns setof public.taps
language plpgsql security definer set search_path = public as $$
declare
  rid uuid;
  n integer;
  t timestamptz := least(coalesce(p_at, now()), now() + interval '1 minute');
  src text := case when p_source = 'gps' then 'gps' else 'anyway' end;
begin
  select x.id into rid from runners x where auth.uid() is not null and x.auth_uid = auth.uid();
  if rid is null then raise exception 'Not allowed: no runner on this phone. Join with your bib first.'; end if;
  select max(ord) into n from stops;
  -- Stop 0 only takes "leave" (the runner's own Start tap); the finish only takes "arrive".
  if p_kind not in ('arrive', 'leave') or p_stop < 0 or p_stop > n or (p_kind = 'arrive' and p_stop = 0) or (p_kind = 'leave' and p_stop >= n) then
    raise exception 'Not allowed: that stop is not on the course.';
  end if;
  begin
    insert into taps (id, runner_id, stop, kind, at, verified, dist_m, acc_m, source)
    values (p_id, rid, p_stop, p_kind, t, coalesce(p_verified, false) and src = 'gps', greatest(p_dist, 0), greatest(p_acc, 0), src)
    on conflict (id) do nothing;
  exception when unique_violation then
    raise exception 'You already tapped that one.';
  end;
  return query select * from taps x where x.id = p_id and x.runner_id = rid;
end $$;

-- Undo your own tap within 10 minutes.
create or replace function public.undo_tap(p_id uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  delete from taps x using runners r
  where x.id = p_id and x.runner_id = r.id and auth.uid() is not null and r.auth_uid = auth.uid()
    and x.created_at > now() - interval '10 minutes';
end $$;

-- Organizer: GO opens the start (or undo it with null), the start time, the course, and fixes.
create or replace function public.set_go(p_at timestamptz) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Not allowed: organizers only.'; end if;
  update event set go_at = p_at, updated_at = now() where id = 1;
end $$;

create or replace function public.admin_save_event(p_start timestamptz) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Not allowed: organizers only.'; end if;
  update event set start_at = p_start, updated_at = now() where id = 1;
end $$;

create or replace function public.admin_save_route(p_stops jsonb) returns void
language plpgsql security definer set search_path = public as $$
declare cnt integer := jsonb_array_length(p_stops);
begin
  if not is_admin() then raise exception 'Not allowed: organizers only.'; end if;
  if cnt < 2 or cnt > 13 then raise exception 'Not allowed: a course needs a start, a finish, and at most 11 bars.'; end if;
  if exists (select 1 from taps) and (select go_at from event where id = 1) is not null and cnt <> (select count(*) from stops) then
    raise exception 'Not allowed: adding or removing bars is locked once anyone has checked in.';
  end if;
  delete from stops where ord >= cnt;
  insert into stops (ord, name, short, addr, lat, lng, radius_m, km, leave_by)
  select x.ord, left(btrim(x.name), 40), left(btrim(coalesce(x.short, x.name)), 18), left(coalesce(x.addr, ''), 60), x.lat, x.lng, x.radius_m, x.km,
         case when x.ord = cnt - 1 then null else x.leave_by end
  from jsonb_to_recordset(p_stops) as x(ord integer, name text, short text, addr text, lat double precision, lng double precision, radius_m integer, km numeric, leave_by timestamptz)
  on conflict (ord) do update set name = excluded.name, short = excluded.short, addr = excluded.addr, lat = excluded.lat, lng = excluded.lng,
    radius_m = excluded.radius_m, km = excluded.km, leave_by = excluded.leave_by;
end $$;

create or replace function public.admin_delete_tap(p_id uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Not allowed: organizers only.'; end if;
  delete from taps where id = p_id;
end $$;

-- Let a bib move to a new phone (lost phone, a different browser mid-race).
create or replace function public.admin_unlock_runner(p_id uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Not allowed: organizers only.'; end if;
  update runners set auth_uid = null where id = p_id;
end $$;

-- After a practice run: wipe every check-in (runners and bibs stay).
create or replace function public.admin_clear_taps() returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Not allowed: organizers only.'; end if;
  delete from taps where true;
  update event set go_at = null, updated_at = now() where id = 1;
end $$;

create or replace function public.admin_remove_runner(p_id uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'Not allowed: organizers only.'; end if;
  delete from runners where id = p_id;
end $$;

revoke execute on function public.is_admin(), public.my_runner(), public.claim_bib(integer, text),
  public.add_tap(uuid, integer, text, timestamptz, boolean, integer, integer, text), public.undo_tap(uuid),
  public.set_go(timestamptz), public.admin_save_event(timestamptz), public.admin_save_route(jsonb),
  public.admin_delete_tap(uuid), public.admin_clear_taps(), public.admin_remove_runner(uuid), public.admin_unlock_runner(uuid) from public, anon;
grant execute on function public.is_admin(), public.my_runner(), public.claim_bib(integer, text),
  public.add_tap(uuid, integer, text, timestamptz, boolean, integer, integer, text), public.undo_tap(uuid),
  public.set_go(timestamptz), public.admin_save_event(timestamptz), public.admin_save_route(jsonb),
  public.admin_delete_tap(uuid), public.admin_clear_taps(), public.admin_remove_runner(uuid), public.admin_unlock_runner(uuid) to authenticated;

-- ---------------------------------------------------------------------------------------------
-- Live updates for the leaderboard.
-- ---------------------------------------------------------------------------------------------
do $$
declare t text;
begin
  foreach t in array array['event', 'stops', 'runners', 'taps'] loop
    begin
      execute format('alter publication supabase_realtime add table public.%I', t);
    exception when duplicate_object then null;
    end;
  end loop;
end $$;
