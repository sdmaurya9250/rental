import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import AuthModal from './AuthModal';
import BrandLogo from './BrandLogo';

export default function HomeHeader() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [authMode, setAuthMode] = useState(null);
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const isHome = pathname === '/';
  const closeMenu = () => setMenuOpen(false);
  const sectionHref = (id) => isHome ? `#${id}` : `/#${id}`;
  const openAuth = (mode) => {
    closeMenu();
    if (isHome) setAuthMode(mode);
    else navigate(mode === 'register' ? '/login?mode=register' : '/login');
  };
  const handleLogin = (data) => {
    setAuthMode(null);
    navigate('/dashboard', { replace: true, state: { user: data?.user } });
  };

  return (
    <nav className="relative z-20 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-5">
      {/* <Link to="/" className="flex items-center space-x-2">
        <span className="flex -space-x-1"><i className="w-3.5 h-3.5 bg-pink-500 rounded-full inline-block" /><i className="w-3.5 h-3.5 bg-purple-500 rounded-full inline-block" /></span>
        <span className="text-xl font-bold tracking-tight">RentCoPartner</span>
      </Link> */}

      <BrandLogo />

      {/* <Link to="/" className="group flex items-center gap-3">

  <div className="relative flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-b from-slate-50 to-slate-100 border border-slate-200/80 shadow-inner group-hover:scale-105 transition-all duration-200">
    <div className="relative flex -space-x-2">
  
      <span className="w-5 h-5 rounded-full border-[2.5px] border-pink-500 shadow-sm shadow-pink-500/30" />
   
      <span className="w-5 h-5 rounded-full border-[2.5px] border-purple-600 mix-blend-multiply shadow-sm shadow-purple-500/30" />
    </div>
  </div>

  <div className="flex flex-col -space-y-0.5">
    <span className="text-xl font-extrabold tracking-tight text-slate-900 group-hover:text-purple-600 transition-colors">
      RentCo<span className="bg-gradient-to-r from-pink-500 to-purple-600 bg-clip-text text-transparent">Partner</span>
    </span>
    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Rental Network</span>
  </div>
</Link> */}

      <div className="hidden items-center space-x-7 text-sm font-semibold lg:flex">
        <Link to="/" className={isHome ? 'border-b-2 border-violet-600 pb-0.5 text-violet-600' : 'text-gray-600 transition hover:text-violet-600'}>Home</Link>
        <a href={sectionHref('services')} className="text-gray-600 transition hover:text-violet-600">Services</a>
        <a href={sectionHref('why-join')} className="text-gray-600 transition hover:text-violet-600">Why Join</a>
        <a href={sectionHref('how-it-works')} className="text-gray-600 transition hover:text-violet-600">How It Works</a>
      </div>

      <div className="hidden items-center space-x-4 md:flex">
        <button type="button" onClick={() => openAuth('login')} className="px-5 py-2 text-sm font-medium text-pink-600 transition hover:text-pink-700">Login</button>
        <button type="button" onClick={() => openAuth('register')} className="rounded-full bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-violet-200 transition hover:opacity-95">Sign Up</button>
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
            <button type="button" onClick={() => openAuth('login')} className="rounded-full border border-pink-200 px-4 py-2.5 text-center text-sm font-semibold text-pink-600">Login</button>
            <button type="button" onClick={() => openAuth('register')} className="rounded-full bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] px-4 py-2.5 text-center text-sm font-semibold text-white">Sign Up</button>
          </div>
        </div>
      )}

      {authMode && <AuthModal isOpen initialMode={authMode} onClose={() => setAuthMode(null)} onLogin={handleLogin} />}
    </nav>
  );
}
