import { useState } from 'react';
import { Heart, Menu, X } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export default function HomeHeader() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { pathname } = useLocation();
  const isHome = pathname === '/';
  const closeMenu = () => setMenuOpen(false);
  const sectionHref = (id) => isHome ? `#${id}` : `/#${id}`;

  return (
    <nav className="relative z-20 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-5">
      <Link to="/" onClick={closeMenu} className="flex shrink-0 items-center space-x-2">
        <Heart className="h-7 w-7 fill-pink-500 text-pink-500" />
        <span className="text-2xl font-black tracking-tight text-[#16132a]">Rent<span className="text-[#8a1cf7]">People</span></span>
      </Link>

      <div className="hidden items-center space-x-7 text-sm font-semibold lg:flex">
        <Link to="/" className={isHome ? 'border-b-2 border-violet-600 pb-0.5 text-violet-600' : 'text-gray-600 transition hover:text-violet-600'}>Home</Link>
        <a href={sectionHref('services')} className="text-gray-600 transition hover:text-violet-600">Services</a>
        <a href={sectionHref('why-join')} className="text-gray-600 transition hover:text-violet-600">Why Join</a>
        <a href={sectionHref('how-it-works')} className="text-gray-600 transition hover:text-violet-600">How It Works</a>
      </div>

      <div className="hidden items-center space-x-4 md:flex">
        <Link to="/login" className="px-5 py-2 text-sm font-medium text-pink-600 transition hover:text-pink-700">Login</Link>
        <Link to="/login?mode=register" className="rounded-full bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-violet-200 transition hover:opacity-95">Sign Up</Link>
      </div>

      <button type="button" onClick={() => setMenuOpen((open) => !open)} aria-label="Toggle menu" aria-expanded={menuOpen} className="rounded-full border border-violet-100 bg-white p-2.5 text-violet-600 shadow-sm lg:hidden">
        {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {menuOpen && (
        <div className="absolute left-4 right-4 top-full z-50 mt-1 rounded-2xl border border-violet-100 bg-white p-3 shadow-xl sm:left-6 sm:right-6 lg:hidden">
          <div className="flex flex-col text-sm font-semibold">
            <Link to="/" onClick={closeMenu} className={`rounded-xl px-4 py-3 ${isHome ? 'bg-violet-50 text-violet-600' : 'text-gray-700 hover:bg-violet-50 hover:text-violet-600'}`}>Home</Link>
            <a href={sectionHref('services')} onClick={closeMenu} className="rounded-xl px-4 py-3 text-gray-700 hover:bg-violet-50 hover:text-violet-600">Services</a>
            <Link to="/browse" onClick={closeMenu} className="rounded-xl px-4 py-3 text-gray-700 hover:bg-violet-50 hover:text-violet-600">Browse</Link>
            <a href={sectionHref('why-join')} onClick={closeMenu} className="rounded-xl px-4 py-3 text-gray-700 hover:bg-violet-50 hover:text-violet-600">Why Join</a>
            <a href={sectionHref('how-it-works')} onClick={closeMenu} className="rounded-xl px-4 py-3 text-gray-700 hover:bg-violet-50 hover:text-violet-600">How It Works</a>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 border-t border-gray-100 pt-3 md:hidden">
            <Link to="/login" onClick={closeMenu} className="rounded-full border border-pink-200 px-4 py-2.5 text-center text-sm font-semibold text-pink-600">Login</Link>
            <Link to="/login?mode=register" onClick={closeMenu} className="rounded-full bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] px-4 py-2.5 text-center text-sm font-semibold text-white">Sign Up</Link>
          </div>
        </div>
      )}
    </nav>
  );
}
