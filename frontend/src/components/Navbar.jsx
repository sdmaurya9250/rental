import { Search } from 'lucide-react';
import BrandLogo from './BrandLogo';

export default function Navbar({ activeTab = 'Browse', onTabChange }) {
  const navItems = ['Home', 'Browse', 'How It Works', 'About'];

  return (
    <nav className="w-full bg-[#0b0c10] border-b border-gray-800/80 px-6 py-4 flex items-center justify-between sticky top-0 z-30">
      <BrandLogo dark />

      {/* Navigation Links */}
      <div className="hidden md:flex items-center space-x-8 text-sm font-medium">
        {navItems.map((item) => (
          <button
            key={item}
            onClick={() => onTabChange && onTabChange(item)}
            className={`relative py-1 transition ${
              activeTab === item
                ? 'text-pink-500 after:content-[""] after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-pink-500 font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      {/* Right Action Items */}
      <div className="flex items-center space-x-3">
        <button className="text-gray-400 hover:text-white p-2 rounded-full transition">
          <Search className="w-5 h-5" />
        </button>
        <button className="px-5 py-2 text-sm font-medium text-gray-200 bg-[#16181e] border border-gray-700/60 rounded-lg hover:border-gray-500 transition">
          Login
        </button>
        <button className="px-5 py-2 text-sm font-semibold text-white bg-gradient-to-r from-pink-500 to-rose-500 rounded-lg hover:opacity-90 transition shadow-lg shadow-pink-500/20">
          Sign Up
        </button>
      </div>
    </nav>
  );
}
