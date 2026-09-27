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
  MoreHorizontal, X
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

export default function Sidebar({ mobileOpen, onNavigate }) {
  const categories = [
    { to: '/', label: 'Home', icon: LayoutGrid, end: true },
    { to: '/browse', label: 'Browse people', icon: Users },
    { to: '/search', label: 'Search people', icon: Search },
    { to: '/bookings', label: 'My bookings', icon: CalendarDays },
    { to: '/favorites', label: 'Favorites', icon: Heart },
    { to: '/messages', label: 'Messages', icon: MessageCircle },
    { to: '/my-profile', label: 'My profile', icon: UserRound },
    { to: '/date-companion', label: 'Date companion', icon: Heart },
    { to: '/travel-buddy', label: 'Travel buddy', icon: Plane },
    { to: '/event-partner', label: 'Event partner', icon: Users },
    { to: '/conversation', label: 'Conversation partner', icon: MessageSquare },
    { to: '/fitness', label: 'Fitness buddy', icon: Activity },
    { to: '/networking', label: 'Professional networking', icon: Briefcase },
    { to: '/photoshoot', label: 'Photoshoot partner', icon: Camera },
    { to: '/gaming', label: 'Gaming buddy', icon: Gamepad2 },
    { to: '/other', label: 'Other', icon: MoreHorizontal },
  ];

  return (
    <aside className={`fixed inset-y-0 left-0 z-50 w-72 overflow-y-auto bg-white border-r border-[#e7e0f5] p-5 shadow-xl transition-transform duration-200 lg:static lg:z-auto lg:w-64 lg:min-w-[256px] lg:translate-x-0 lg:shadow-none ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="mb-4 flex items-center justify-between lg:block"><h3 className="px-2 text-xs font-semibold uppercase tracking-wider text-[#8b849d]">Navigation</h3><button onClick={onNavigate} className="rounded-lg p-2 text-[#5d586e] hover:bg-violet-50 lg:hidden" aria-label="Close menu"><X className="h-5 w-5" /></button></div>

      <div className="space-y-1">
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
                  ? 'bg-gradient-to-r from-fuchsia-100 to-violet-100 text-violet-700 border border-violet-100'
                  : 'text-[#5d586e] hover:text-violet-700 hover:bg-[#f6f2ff]'
              }`}
            >
              {({ isActive }) => <><Icon className={`w-4 h-4 ${isActive ? 'text-violet-700' : 'text-[#7d778f]'}`} />
              <span className="truncate">{cat.label}</span>
              </>}
            </NavLink>
          );
        })}
      </div>
    </aside>
  );
}
