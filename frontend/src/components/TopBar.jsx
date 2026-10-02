import { useEffect, useState } from 'react';
import { Bell, ChevronDown, LogOut, MapPin, Menu, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getMyProfile, getStoredUser, logout } from '../auth/auth';

export default function TopBar({ onMenuToggle }) {
  const navigate = useNavigate();
  const [loggingOut, setLoggingOut] = useState(false);
  const [user, setUser] = useState(() => getStoredUser() || {});
  const [query, setQuery] = useState('');

  useEffect(() => {
    let active = true;
    const refreshStoredUser = () => setUser(getStoredUser() || {});
    window.addEventListener('rp-profile-updated', refreshStoredUser);
    getMyProfile()
      .then((profile) => { if (active && profile) setUser({ ...(getStoredUser() || {}), ...(profile.profile || profile) }); })
      .catch(() => {});
    return () => {
      active = false;
      window.removeEventListener('rp-profile-updated', refreshStoredUser);
    };
  }, []);

  const displayName = user?.fullName || user?.full_name || user?.name || user?.username || user?.email || 'My account';
  const initials = displayName === 'My account' ? 'M' : displayName.charAt(0).toUpperCase();
  const profileImage = user?.image || user?.profile_image || user?.avatar_url || user?.photo || '';

  async function handleLogout() {
    setLoggingOut(true);
    try { await logout(); } catch { /* The local session is cleared even if no logout route exists. */ }
    finally {
      navigate('/login', { replace: true });
      setLoggingOut(false);
    }
  }

  function submitSearch(event) {
    event.preventDefault();
    navigate(`/search${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ''}`);
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 min-w-0 items-center gap-2 border-b border-violet-100 bg-white/95 px-3 shadow-[0_2px_12px_rgba(40,24,90,0.04)] backdrop-blur sm:gap-3 sm:px-5 lg:px-6">
      <button type="button" onClick={onMenuToggle} className="shrink-0 rounded-lg p-2 text-violet-700 hover:bg-violet-50 lg:hidden" aria-label="Open menu"><Menu className="h-5 w-5" /></button>

      <form onSubmit={submitSearch} className="hidden min-w-0 flex-1 items-center gap-2 md:flex">
        <label className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-violet-100 bg-[#fcfbff] px-3 py-2 text-[#8b849d] focus-within:border-violet-300 focus-within:ring-2 focus-within:ring-violet-100">
          <Search className="h-4 w-4 shrink-0 text-violet-500" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search people, services or activities…" className="min-w-0 flex-1 bg-transparent text-sm text-[#24202e] outline-none placeholder:text-[#a39cb4]" />
        </label>
        <button type="button" className="hidden shrink-0 items-center gap-1.5 rounded-xl border border-violet-100 bg-white px-3 py-2 text-xs font-medium text-[#5d586e] lg:flex"><MapPin className="h-4 w-4 text-violet-600" />Delhi, India<ChevronDown className="h-3.5 w-3.5" /></button>
        <button type="submit" className="shrink-0 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-500 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:opacity-90">Search</button>
      </form>
      <button type="button" onClick={() => navigate('/search')} className="ml-auto rounded-lg p-2 text-violet-700 hover:bg-violet-50 md:hidden" aria-label="Search"><Search className="h-5 w-5" /></button>

      <div className="ml-auto flex shrink-0 items-center gap-2 sm:gap-3 md:ml-1">
        <button type="button" className="relative rounded-lg p-2 text-[#706a80] hover:bg-violet-50 hover:text-violet-700" aria-label="Notifications"><Bell className="h-[18px] w-[18px]" /></button>
        <button type="button" onClick={() => navigate('/my-profile')} className="flex min-w-0 items-center gap-2 rounded-xl p-1 hover:bg-violet-50">
          <span className="grid h-9 w-9 shrink-0 place-items-center overflow-hidden rounded-full bg-gradient-to-br from-fuchsia-500 to-violet-600 text-sm font-bold text-white ring-2 ring-violet-100">{profileImage ? <img src={profileImage} alt={`${displayName} profile`} className="h-full w-full object-cover" /> : initials}</span>
          <span className="hidden max-w-32 text-left sm:block"><span className="block truncate text-xs font-bold text-[#24202e]">{displayName}</span><span className="block text-[10px] text-[#8b849d]">Member</span></span>
          <ChevronDown className="hidden h-3.5 w-3.5 text-[#8b849d] sm:block" />
        </button>
        <button type="button" onClick={handleLogout} disabled={loggingOut} className="inline-flex items-center gap-1.5 rounded-lg border border-violet-100 p-2 text-xs font-semibold text-violet-700 hover:bg-violet-50 disabled:opacity-60 sm:px-3 sm:py-2"><LogOut className="h-3.5 w-3.5" /><span className="hidden sm:inline">{loggingOut ? 'Logging out…' : 'Logout'}</span></button>
      </div>
    </header>
  );
}
