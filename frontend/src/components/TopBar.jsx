import { useEffect, useState } from 'react';
import { LogOut, Menu, Search } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import { getMyProfile, getStoredUser, logout } from '../auth/auth';

export default function TopBar({ onMenuToggle }) {
  const navigate = useNavigate();

  const [loggingOut, setLoggingOut] = useState(false);

  const [user, setUser] = useState(() => getStoredUser() || {});

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

  const displayName =
    user?.fullName ||
    user?.full_name ||
    user?.name ||
    user?.username ||
    user?.email?.split('@')[0] ||
    'My account';

  const initials =
    displayName === 'My account'
      ? 'M'
      : displayName.charAt(0).toUpperCase();
  const profileImage = user?.image || user?.profile_image || user?.avatar_url || user?.photo || '';

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

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-white/10 bg-[#100d2b]/95 px-6 text-white shadow-sm backdrop-blur">
      {/* Logo */}
      <NavLink
        to="/"
        className="flex items-center space-x-2 text-white"
      >
        <span className="flex -space-x-1">
          <i className="h-3.5 w-3.5 rounded-full bg-fuchsia-500" />
          <i className="h-3.5 w-3.5 rounded-full bg-violet-600" />
        </span>

        <span className="text-xl font-bold">RentPeople</span>
      </NavLink>

      {/* Right Actions */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Search */}
        {/* <button
          type="button"
          className="hidden p-2 text-violet-100/70 hover:text-fuchsia-300 sm:block"
          aria-label="Search"
        >
          <Search className="h-5 w-5" />
        </button> */}

        {/* User Info */}
        <div className="hidden text-right sm:block">
          <p className="max-w-40 truncate text-sm font-medium text-white">
            {displayName}
          </p>

          {/* <p className="text-xs text-violet-200/60">Member</p> */}
        </div>

        {/* Avatar */}
        <span className="grid h-9 w-9 place-items-center overflow-hidden rounded-full bg-gradient-to-br from-fuchsia-500 to-violet-600 text-sm font-bold text-white">
          {profileImage ? <img src={profileImage} alt={`${displayName} profile`} className="h-full w-full object-cover" /> : initials}
        </span>

        {/* Logout */}
        <button
          type="button"
          onClick={handleLogout}
          disabled={loggingOut}
          className="inline-flex items-center gap-2 rounded-lg border border-violet-300/30 bg-white/5 px-3 py-2 text-sm font-semibold text-violet-100 hover:border-fuchsia-300/50 hover:bg-white/10 hover:text-white disabled:opacity-60"
        >
          <LogOut className="h-4 w-4" />

          <span className="hidden sm:inline">
            {loggingOut ? 'Logging out…' : 'Logout'}
          </span>
        </button>

        {/* Mobile Menu */}
        <button
          type="button"
          onClick={onMenuToggle}
          className="rounded-lg p-2 text-violet-100/80 hover:bg-white/10 hover:text-white lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}
