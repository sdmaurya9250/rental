import { Outlet } from 'react-router-dom';
import { useState } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  return (
    <div className="flex min-h-screen bg-[#f5f3ff] font-sans text-[#171426]">
      {mobileMenuOpen && <button aria-label="Close menu" onClick={() => setMobileMenuOpen(false)} className="fixed inset-0 z-40 bg-[#100d2b]/55 backdrop-blur-[1px] lg:hidden" />}
      <Sidebar mobileOpen={mobileMenuOpen} onNavigate={() => setMobileMenuOpen(false)} />
      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <TopBar onMenuToggle={() => setMobileMenuOpen(true)} />
        <main className="min-w-0 flex-1"><Outlet /></main>
      </div>
    </div>
  );
}
