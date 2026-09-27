import { Outlet } from 'react-router-dom';
import { useState } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  return <div className="min-h-screen bg-[#f8f6ff] font-sans text-[#171426]"><TopBar onMenuToggle={() => setMobileMenuOpen(true)} /><div className="flex min-h-[calc(100vh-4rem)]">{mobileMenuOpen && <button aria-label="Close menu" onClick={() => setMobileMenuOpen(false)} className="fixed inset-0 z-40 bg-[#171426]/25 lg:hidden" />}<Sidebar mobileOpen={mobileMenuOpen} onNavigate={() => setMobileMenuOpen(false)} /><main className="min-w-0 flex-1"><Outlet /></main></div></div>;
}
