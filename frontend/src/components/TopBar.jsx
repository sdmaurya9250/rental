import { useState } from 'react';
import { LogOut, Menu, Search } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import { getStoredUser, logout } from '../auth/auth';

export default function TopBar({ onMenuToggle }) {
  const navigate = useNavigate();
  const [loggingOut, setLoggingOut] = useState(false);
  const user = getStoredUser();
  const displayName = user?.fullName || user?.name || user?.username || user?.email?.split('@')[0] || 'My account';
  const initials = displayName === 'My account' ? 'M' : displayName.charAt(0).toUpperCase();

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
    } catch {
      // The local session is cleared even when the server has no logout route.
    } finally {
      navigate('/login', { replace: true });
      setLoggingOut(false);
    }
  }

  return <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[#e7e0f5] bg-white/95 px-6 backdrop-blur">
    <NavLink to="/" className="flex items-center space-x-2 text-[#171426]"><span className="flex -space-x-1"><i className="h-3.5 w-3.5 rounded-full bg-fuchsia-500" /><i className="h-3.5 w-3.5 rounded-full bg-violet-600" /></span><span className="text-xl font-bold">RentPeople</span></NavLink>
    <div className="flex items-center gap-2 sm:gap-3"><button className="hidden p-2 text-[#5d586e] hover:text-violet-700 sm:block" aria-label="Search"><Search className="h-5 w-5" /></button><div className="hidden text-right sm:block"><p className="max-w-40 truncate text-sm font-medium text-[#171426]">{displayName}</p><p className="text-xs text-[#7d778f]">Member</p></div><span className="hidden h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-fuchsia-500 to-violet-600 text-sm font-bold text-white sm:grid">{initials}</span><button type="button" onClick={handleLogout} disabled={loggingOut} className="inline-flex items-center gap-2 rounded-lg border border-violet-200 px-3 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-50 disabled:opacity-60"><LogOut className="h-4 w-4" /><span className="hidden sm:inline">{loggingOut ? 'Logging out…' : 'Logout'}</span></button><button onClick={onMenuToggle} className="rounded-lg p-2 text-[#5d586e] hover:bg-violet-50 lg:hidden" aria-label="Open menu"><Menu className="h-5 w-5" /></button></div>
  </header>;
}
