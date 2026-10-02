import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, CalendarDays, Camera, Coffee, Dumbbell, Heart, MapPin, MessageCircle, Music2, Plane, Search, ShoppingBag, Sparkles, Theater, Users } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import FeaturePage from '../components/FeaturePage';
import { fetchBookingRecords, fetchConversations, fetchPeople, formatPersonPrice, getPersonPrice } from './finderApi';
import { getMyProfile, getStoredUser } from '../auth/auth';

const shortcuts = [
  { name: 'Coffee Partner', icon: Coffee, to: '/browse', tone: 'text-fuchsia-600 bg-fuchsia-50' },
  { name: 'Café & Food', icon: Theater, to: '/browse', tone: 'text-rose-500 bg-rose-50' },
  { name: 'Event Partner', icon: Users, to: '/event-partner', tone: 'text-blue-600 bg-blue-50' },
  { name: 'Travel Buddy', icon: Plane, to: '/travel-buddy', tone: 'text-sky-600 bg-sky-50' },
  { name: 'Movie Buddy', icon: Camera, to: '/browse', tone: 'text-violet-600 bg-violet-50' },
  { name: 'Shopping Buddy', icon: ShoppingBag, to: '/browse', tone: 'text-pink-600 bg-pink-50' },
  { name: 'Gym Partner', icon: Dumbbell, to: '/fitness', tone: 'text-indigo-600 bg-indigo-50' },
  { name: 'Music Jam', icon: Music2, to: '/browse', tone: 'text-purple-600 bg-purple-50' },
];

function getList(result, key) {
  if (Array.isArray(result)) return result;
  return Array.isArray(result?.[key]) ? result[key] : [];
}

function getName(item) {
  return item?.name || item?.fullName || item?.full_name || item?.person_name || item?.other_user?.name || item?.participant?.name || item?.user?.name || 'RentPeople member';
}

function getImage(item) {
  return item?.image || item?.profile_image || item?.avatar_url || item?.photo || item?.person_image || item?.other_user?.image || item?.participant?.image || item?.user?.image || '';
}

function conversationUserId(conversation) {
  return String(conversation?.other_user_id || conversation?.participant_id || conversation?.user_id || conversation?.receiver_id || conversation?.other_user?.id || conversation?.participant?.id || conversation?.user?.id || conversation?.id || '');
}

function parseArray(value) {
  if (Array.isArray(value)) return value;
  if (typeof value !== 'string' || !value) return [];
  try { const parsed = JSON.parse(value); return Array.isArray(parsed) ? parsed : []; }
  catch { return value.split(',').map((part) => part.trim()).filter(Boolean); }
}

function completionFor(profile, role) {
  const fields = [
    Boolean(profile.fullName || profile.full_name || profile.name), Boolean(profile.city),
    Boolean(profile.bio?.trim()), Boolean(getImage(profile)), parseArray(profile.languages).length > 0,
  ];
  if (!role.includes('find')) fields.push(parseArray(profile.services || profile.interests).length > 0, Boolean(profile.availableTime || profile.available_time || profile.availability));
  return Math.round(fields.filter(Boolean).length / fields.length * 100);
}

function formatDate(value) {
  if (!value) return 'Date to be confirmed';
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

function personCardName(person) {
  return getName(person);
}

function PersonCard({ person }) {
  const name = personCardName(person);
  const image = getImage(person);
  const tags = parseArray(person.tags || person.interests).slice(0, 2);
  const price = getPersonPrice(person);
  return (
    <article className="min-w-0 overflow-hidden rounded-2xl border border-violet-100 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <Link to={`/people/${person.id}`} className="relative block aspect-[4/3] overflow-hidden bg-violet-100">
        <img src={image || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=600&auto=format&fit=crop'} alt={name} className="h-full w-full object-cover object-center" loading="lazy" />
        <span className="absolute right-2 top-2 rounded-full bg-white/90 p-1.5 text-violet-500"><Heart className="h-3.5 w-3.5" /></span>
      </Link>
      <div className="p-3">
        <div className="flex items-center justify-between gap-2"><h3 className="truncate text-sm font-bold text-[#211a35]">{name}{person.age ? `, ${person.age}` : ''}</h3><span className="h-2 w-2 shrink-0 rounded-full bg-emerald-400" /></div>
        <p className="mt-1 flex items-center gap-1 truncate text-[11px] text-[#827b95]"><MapPin className="h-3 w-3 shrink-0" />{person.location || person.city || 'India'}</p>
        <p className="mt-2 text-sm font-extrabold text-[#211a35]">{formatPersonPrice(price)}<span className="text-[10px] font-medium text-[#827b95]">/hour</span></p>
        <div className="mt-2 flex min-h-5 flex-wrap gap-1">{tags.map((tag) => <span key={tag} className="rounded-full bg-violet-50 px-2 py-0.5 text-[10px] font-medium text-violet-700">{tag}</span>)}</div>
        <Link to={`/people/${person.id}`} className="mt-3 block rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-500 px-3 py-2 text-center text-xs font-semibold text-white">View profile</Link>
      </div>
    </article>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const storedUser = getStoredUser() || {};
  const [profile, setProfile] = useState(storedUser);
  const [people, setPeople] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [query, setQuery] = useState('');
  const [loadingPeople, setLoadingPeople] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let active = true;
    fetchPeople().then((items) => { if (active) setPeople(items); }).catch((error) => { if (active) setLoadError(error.message || 'Unable to load people.'); }).finally(() => { if (active) setLoadingPeople(false); });
    getMyProfile().then((result) => { if (active) setProfile({ ...storedUser, ...(result?.profile || result || {}) }); }).catch(() => {});
    fetchBookingRecords().then((result) => { if (active) setBookings(getList(result, 'bookings')); }).catch(() => {});
    fetchConversations().then((result) => { if (active) setConversations(getList(result, 'conversations')); }).catch(() => {});
    return () => { active = false; };
  }, []);

  const role = String(profile.want_to || profile.wantTo || profile.accountIntent || storedUser.want_to || '').toLowerCase();
  const completion = useMemo(() => completionFor(profile, role), [profile, role]);
  const displayName = profile.fullName || profile.full_name || profile.name || profile.email?.split('@')[0] || 'there';
  const sortedPeople = useMemo(() => [...people].sort((a, b) => getPersonPrice(a) - getPersonPrice(b)), [people]);
  const popularPeople = useMemo(() => {
    const city = String(profile.city || '').trim().toLowerCase();
    if (!city) return people.slice(0, 8);
    return [...people].sort((a, b) => {
      const aNearby = String(a.location || a.city || '').toLowerCase().includes(city) ? 1 : 0;
      const bNearby = String(b.location || b.city || '').toLowerCase().includes(city) ? 1 : 0;
      return bNearby - aNearby;
    }).slice(0, 8);
  }, [people, profile.city]);
  const recommendedPeople = sortedPeople.slice(0, 8);
  const upcomingBooking = bookings.find((booking) => !['completed', 'cancelled', 'rejected'].includes(String(booking.booking_status || '').toLowerCase()));
  const profileImage = getImage(profile);

  function submitSearch(event) {
    event.preventDefault();
    navigate(`/search${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ''}`);
  }

  return (
    <FeaturePage>
      <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1fr)_260px]">
        <div className="min-w-0 space-y-5">
          <section className="relative isolate overflow-hidden rounded-2xl border border-violet-100 bg-gradient-to-br from-[#eadcff] via-[#f6e8ff] to-[#fff0f5] p-5 sm:p-7">
            <div className="absolute inset-y-0 right-0 -z-10 hidden w-2/5 overflow-hidden sm:block"><img src={getImage(people[0]) || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=800&auto=format&fit=crop'} alt="" className="h-full w-full object-cover object-top opacity-90" /><div className="absolute inset-0 bg-gradient-to-r from-[#f3e4ff] via-[#f3e4ff]/50 to-transparent" /></div>
            <div className="relative max-w-xl">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-violet-700">Real people. Real moments.</p>
              <h1 className="mt-2 text-2xl font-extrabold tracking-tight text-[#211538] sm:text-3xl">Good morning, {displayName}! <span aria-hidden="true">👋</span></h1>
              <p className="mt-1 text-sm text-[#706482]">Find the perfect companion for your next plan.</p>
              <form onSubmit={submitSearch} className="mt-5 flex flex-col gap-2 rounded-xl border border-white/80 bg-white/90 p-2 shadow-md sm:flex-row sm:items-center">
                <label className="flex min-w-0 flex-1 items-center gap-2 px-2"><Search className="h-4 w-4 shrink-0 text-violet-600" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="What are you looking for?" className="min-w-0 flex-1 bg-transparent py-2 text-xs outline-none placeholder:text-[#9a92a8]" /></label>
                <span className="hidden items-center gap-1 border-l border-violet-100 px-3 text-[11px] text-[#706a80] sm:flex"><MapPin className="h-3.5 w-3.5 text-violet-600" />{profile.city || 'Delhi, India'}</span>
                <button type="submit" className="rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-500 px-5 py-2.5 text-xs font-semibold text-white">Search</button>
              </form>
            </div>
          </section>

          <nav aria-label="Popular services" className="grid grid-cols-4 gap-2 sm:grid-cols-4 md:grid-cols-8">
            {shortcuts.map(({ name, icon: Icon, to, tone }) => <Link key={name} to={to} className="group flex min-w-0 flex-col items-center gap-1.5 rounded-xl border border-transparent bg-white/75 px-1.5 py-3 text-center shadow-sm transition hover:border-violet-100 hover:bg-white"><span className={`grid h-9 w-9 place-items-center rounded-xl ${tone}`}><Icon className="h-4 w-4" /></span><span className="line-clamp-2 text-[10px] font-semibold leading-tight text-[#4c455f] sm:text-[11px]">{name}</span></Link>)}
          </nav>

          <section>
            <div className="mb-3 flex items-end justify-between gap-2"><div><h2 className="text-lg font-extrabold text-[#241b39]">Popular near you</h2><p className="text-xs text-[#827b95]">Meet people ready to make a great plan.</p></div><Link to="/browse" className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-violet-700">View all <ArrowRight className="h-3.5 w-3.5" /></Link></div>
            {loadingPeople && <p className="rounded-xl bg-white p-5 text-sm text-[#706a80]">Loading people…</p>}
            {loadError && <p role="alert" className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">{loadError}</p>}
            {!loadingPeople && !loadError && popularPeople.length === 0 && <p className="rounded-xl bg-white p-5 text-sm text-[#706a80]">No profiles are available yet.</p>}
            {!loadingPeople && !loadError && popularPeople.length > 0 && <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">{popularPeople.slice(0, 4).map((person) => <PersonCard key={person.id} person={person} />)}</div>}
          </section>

          <section>
            <div className="mb-3 flex items-end justify-between gap-2"><div><h2 className="text-lg font-extrabold text-[#241b39]">Recommended for you</h2><p className="text-xs text-[#827b95]">Explore more companions and services.</p></div><Link to="/browse" className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-violet-700">View all <ArrowRight className="h-3.5 w-3.5" /></Link></div>
            {recommendedPeople.length > 0 && <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">{recommendedPeople.slice(4, 8).map((person) => <PersonCard key={person.id} person={person} />)}</div>}
          </section>
        </div>

        <aside className="space-y-4 xl:sticky xl:top-20 xl:self-start">
          <section className="rounded-2xl border border-violet-100 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between"><h2 className="text-sm font-extrabold text-[#241b39]">Your profile</h2><Sparkles className="h-4 w-4 text-violet-500" /></div>
            <div className="mt-3 flex items-center gap-3"><span className="grid h-12 w-12 shrink-0 place-items-center overflow-hidden rounded-full bg-violet-100 text-lg font-bold text-violet-700">{profileImage ? <img src={profileImage} alt={displayName} className="h-full w-full object-cover" /> : displayName.charAt(0).toUpperCase()}</span><div className="min-w-0"><p className="truncate text-xs font-bold">{displayName}</p><p className="mt-1 text-[10px] text-[#827b95]">RentPeople member</p></div></div>
            <div className="mt-3 rounded-full bg-emerald-50 px-3 py-2 text-center text-[11px] font-bold text-emerald-700">● Profile complete ({completion}%)</div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-violet-100"><div className="h-full rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-500" style={{ width: `${completion}%` }} /></div>
            <Link to="/my-profile" className="mt-3 block rounded-lg bg-violet-50 px-3 py-2 text-center text-xs font-semibold text-violet-700 hover:bg-violet-100">Edit profile <ArrowRight className="ml-1 inline h-3.5 w-3.5" /></Link>
          </section>

          <section className="rounded-2xl border border-violet-100 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between"><h2 className="text-sm font-extrabold text-[#241b39]">Upcoming booking</h2><Link to="/bookings" className="text-[10px] font-semibold text-violet-700">View all →</Link></div>
            {upcomingBooking ? <div className="mt-3"><div className="flex items-center gap-2.5"><img src={getImage(upcomingBooking) || getImage(upcomingBooking.rent_person) || 'https://i.pravatar.cc/100?img=12'} alt={getName(upcomingBooking)} className="h-10 w-10 rounded-xl object-cover" /><div className="min-w-0 flex-1"><p className="truncate text-xs font-bold">{upcomingBooking.person_name || getName(upcomingBooking.rent_person) || 'Appointment'}</p><p className="text-[10px] text-[#827b95]">{upcomingBooking.service_name || 'Booking'}</p></div><span className="rounded-full bg-emerald-50 px-2 py-1 text-[9px] font-bold text-emerald-700">{upcomingBooking.booking_status || 'Pending'}</span></div><p className="mt-3 flex items-center gap-1.5 text-[10px] text-[#706a80]"><CalendarDays className="h-3.5 w-3.5 text-violet-600" />{formatDate(upcomingBooking.booking_date)} · {upcomingBooking.start_time || 'Time TBD'}</p><Link to="/bookings" className="mt-3 block rounded-lg bg-violet-50 px-3 py-2 text-center text-xs font-semibold text-violet-700">View details</Link></div> : <p className="mt-3 text-xs text-[#827b95]">No upcoming bookings yet.</p>}
          </section>

          <section className="rounded-2xl border border-violet-100 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between"><h2 className="text-sm font-extrabold text-[#241b39]">Messages</h2><Link to="/messages" className="text-[10px] font-semibold text-violet-700">View all →</Link></div>
            <div className="mt-2 divide-y divide-violet-50">{conversations.slice(0, 3).map((conversation, index) => <Link key={conversation.id || conversationUserId(conversation) || index} to={`/messages?userId=${encodeURIComponent(conversationUserId(conversation))}`} className="flex items-center gap-2.5 py-2.5"><img src={getImage(conversation) || `https://i.pravatar.cc/100?u=${index}`} alt={getName(conversation)} className="h-9 w-9 rounded-full object-cover" /><span className="min-w-0 flex-1"><span className="block truncate text-xs font-bold">{getName(conversation)}</span><span className="block truncate text-[10px] text-[#827b95]">{conversation.last_message?.content || conversation.last_message || conversation.latest_message || 'Open conversation'}</span></span></Link>)}{conversations.length === 0 && <p className="py-3 text-xs text-[#827b95]">No messages yet.</p>}</div>
          </section>
        </aside>
      </div>
    </FeaturePage>
  );
}
