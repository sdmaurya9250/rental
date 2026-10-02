import React from 'react';
import {
  LayoutGrid, CalendarDays, Search, MessageCircle, UserRound,
  Heart,
  Plane,
  Users,
  MessageSquare,
  Activity,
  Briefcase,
  Camera,
  Gamepad2,
  MoreHorizontal, X, UserPlus
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { getStoredUser } from '../auth/auth';

export default function Sidebar({ mobileOpen, onNavigate }) {
  const allCategories = [
    { to: '/dashboard', label: 'Home', icon: LayoutGrid, end: true },
    { to: '/browse', label: 'Browse people', icon: Users },
    // { to: '/search', label: 'Search people', icon: Search },
    { to: '/bookings', label: 'My bookings', icon: CalendarDays },
    { to: '/favorites', label: 'Favorites', icon: Heart },
    { to: '/messages', label: 'Messages', icon: MessageCircle },
    { to: '/my-profile', label: 'My profile', icon: UserRound },
    // { to: '/date-companion', label: 'Date companion', icon: Heart },
    // { to: '/travel-buddy', label: 'Travel buddy', icon: Plane },
    // { to: '/event-partner', label: 'Event partner', icon: Users },
    // { to: '/conversation', label: 'Conversation partner', icon: MessageSquare },
    // { to: '/fitness', label: 'Fitness buddy', icon: Activity },
    // { to: '/networking', label: 'Professional networking', icon: Briefcase },
    // { to: '/photoshoot', label: 'Photoshoot partner', icon: Camera },
    // { to: '/gaming', label: 'Gaming buddy', icon: Gamepad2 },
    // { to: '/other', label: 'Other', icon: MoreHorizontal },
  ];
  const user = getStoredUser();
  const role = String(user?.want_to || user?.wantTo || user?.accountIntent || '').trim().toLowerCase();
  const isBecomeRole = role === 'become a rentpeople' || role === 'become';
  const isFindRole = role === 'find a rentpeople' || role === 'find';
  const isBothRole = role === 'both';
  const roleCategories = [
    { to: '/my-profile', label: 'Become', icon: UserPlus },
    { to: '/bookings', label: 'My bookings', icon: CalendarDays },
    { to: '/messages', label: 'Messages', icon: MessageCircle },
    { to: '/my-profile', label: 'My profile', icon: UserRound },
  ];
  const categories = isBecomeRole
    ? roleCategories
    : isFindRole
      ? allCategories
      : isBothRole
        ? [...allCategories, roleCategories[0]]
        : allCategories;

  return (
    <aside className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col overflow-y-auto border-r border-violet-950 bg-[#100d2b] p-4 text-white shadow-xl transition-transform duration-200 lg:sticky lg:top-0 lg:z-auto lg:h-screen lg:w-60 lg:min-w-[240px] lg:shrink-0 lg:translate-x-0 lg:shadow-none xl:w-64 xl:min-w-[256px] ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="mb-5 flex items-center justify-between border-b border-white/10 px-1 pb-4">
        <NavLink to="/" onClick={onNavigate} className="flex items-center gap-2.5">
          <span className="relative flex h-8 w-8 items-center justify-center text-xl font-black text-fuchsia-400">♥<span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-violet-400" /></span>
          <span><span className="block text-sm font-extrabold tracking-wide text-white">RentPeople</span><span className="block text-[9px] tracking-wide text-violet-200/60">Meet · Connect · Rent</span></span>
        </NavLink>
        <button onClick={onNavigate} className="rounded-lg p-2 text-violet-100/70 hover:bg-white/10 lg:hidden" aria-label="Close menu"><X className="h-5 w-5" /></button>
      </div>

      <div className="space-y-1.5">
        {categories.map((cat) => {
          const Icon = cat.icon;
          return (
            <NavLink
              key={cat.to}
              to={cat.to}
              end={cat.end}
              onClick={onNavigate}
              className={({ isActive }) => `w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition duration-150 ${
                isActive
                  ? 'bg-gradient-to-r from-violet-700 via-purple-600 to-fuchsia-500 text-white shadow-lg shadow-fuchsia-950/30'
                  : 'text-violet-100/75 hover:bg-white/10 hover:text-white'
              }`}
            >
              {({ isActive }) => <><Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-violet-200/70'}`} />
              <span className="truncate">{cat.label}</span>
              </>}
            </NavLink>
          );
        })}
      </div>

      <div className="mt-auto pt-6">
        <div className="rounded-2xl border border-amber-300/25 bg-gradient-to-br from-amber-500/15 via-fuchsia-500/10 to-violet-500/20 p-3.5 shadow-lg shadow-black/10">
          <p className="flex items-center gap-2 text-xs font-bold text-amber-200"><span aria-hidden="true">♛</span> Upgrade to Pro</p>
          <p className="mt-1 text-[10px] leading-relaxed text-violet-100/70">Get more visibility and premium features.</p>
          <span className="mt-3 block rounded-lg bg-gradient-to-r from-orange-400 via-pink-500 to-violet-500 px-3 py-2 text-center text-xs font-bold text-white shadow-md shadow-fuchsia-950/30">Upgrade Now</span>
        </div>
      </div>
    </aside>
  );
}
