import { useEffect, useMemo, useState } from 'react';
import { CalendarDays, MessageCircle, Search, UserRound } from 'lucide-react';
import { Link } from 'react-router-dom';
import FeaturePage from '../components/FeaturePage';
import { getMyProfile, getStoredUser } from '../auth/auth';

function parseArray(value) {
  if (Array.isArray(value)) return value;
  if (typeof value !== 'string' || !value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return value.split(',').map((item) => item.trim()).filter(Boolean);
  }
}

function accountRole(profile, user) {
  return String(profile?.want_to || profile?.wantTo || profile?.accountIntent || user?.want_to || user?.wantTo || user?.accountIntent || '').toLowerCase();
}

function completionFor(profile, role) {
  const fields = [
    Boolean(profile.fullName || profile.full_name || profile.name),
    Boolean(profile.city),
    Boolean(profile.bio?.trim()),
    Boolean(profile.image || profile.profile_image || profile.avatar_url),
    parseArray(profile.languages).length > 0,
  ];
  if (!role.includes('find')) {
    fields.push(parseArray(profile.services || profile.interests).length > 0);
    fields.push(Boolean(profile.availableTime || profile.available_time || (profile.availability && Object.keys(profile.availability).length)));
  }
  return Math.round((fields.filter(Boolean).length / fields.length) * 100);
}

export default function DashboardPage() {
  const user = getStoredUser() || {};
  const [profile, setProfile] = useState(user);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let active = true;
    getMyProfile()
      .then((result) => { if (active) setProfile({ ...user, ...(result || {}) }); })
      .catch((error) => { if (active) setLoadError(error.message || 'Unable to load profile completion.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const role = accountRole(profile, user);
  const completion = useMemo(() => completionFor(profile, role), [profile, role]);
  const name = profile.fullName || profile.full_name || profile.name || 'there';

  return (
    <FeaturePage title={`Welcome, ${name}`} subtitle="Your RentPeople dashboard">
      <section className="mb-6 max-w-5xl rounded-2xl border border-violet-100 bg-white p-5 shadow-sm" aria-label="Profile completion">
        <div className="flex items-center justify-between gap-3">
          <div><h2 className="font-bold text-[#171426]">Profile completion</h2><p className="mt-1 text-sm text-[#706a80]">Complete your profile to help people get to know you.</p></div>
          <span className="text-lg font-bold text-violet-700">{loading ? '…' : `${completion}%`}</span>
        </div>
        <div className="mt-4 h-3 overflow-hidden rounded-full bg-violet-100" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={completion}>
          <div className="h-full rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-500 transition-all" style={{ width: `${completion}%` }} />
        </div>
        {loadError && <p className="mt-2 text-xs text-amber-700">{loadError}</p>}
        <Link to="/my-profile" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-violet-700 hover:underline"><UserRound className="h-4 w-4" />Complete your profile</Link>
      </section>

      <div className="grid max-w-5xl gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Link to="/browse" className="rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm transition hover:border-violet-300"><Search className="h-5 w-5 text-violet-600" /><h2 className="mt-3 font-bold">Browse people</h2><p className="mt-1 text-sm text-[#706a80]">Find someone for your next plan.</p></Link>
        <Link to="/bookings" className="rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm transition hover:border-violet-300"><CalendarDays className="h-5 w-5 text-violet-600" /><h2 className="mt-3 font-bold">My bookings</h2><p className="mt-1 text-sm text-[#706a80]">Review requests and appointments.</p></Link>
        <Link to="/messages" className="rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm transition hover:border-violet-300"><MessageCircle className="h-5 w-5 text-violet-600" /><h2 className="mt-3 font-bold">Messages</h2><p className="mt-1 text-sm text-[#706a80]">Chat with your connections.</p></Link>
      </div>
    </FeaturePage>
  );
}
