import React, { useState } from 'react';
import { 
  Search, 
  ShieldCheck, 
  Grid, 
  Calendar, 
  Heart, 
  ChevronDown 
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Home() {
  const [category, setCategory] = useState('');
  const [city, setCity] = useState('');

  const popularTags = [
    'Date Companion',
    'Travel Buddy',
    'Event Partner',
    'Fitness Buddy',
    'Conversation Partner',
  ];

  const features = [
    {
      icon: <ShieldCheck className="w-6 h-6 text-violet-600" />,
      title: 'Verified People',
      subtitle: 'Trusted & safe',
    },
    {
      icon: <Grid className="w-6 h-6 text-violet-600" />,
      title: 'Flexible Plans',
      subtitle: 'Hourly or daily',
    },
    {
      icon: <Calendar className="w-6 h-6 text-violet-600" />,
      title: 'Wide Categories',
      subtitle: 'For every need',
    },
    {
      icon: <Heart className="w-6 h-6 text-fuchsia-500 fill-fuchsia-500" />,
      title: 'Real Connections',
      subtitle: 'Make life more fun',
    },
  ];

  return (
    <div className="min-h-screen bg-[#f8f6ff] text-[#171426] font-sans flex flex-col justify-between selection:bg-violet-200 selection:text-violet-950">
      <nav className="w-full max-w-7xl mx-auto px-6 py-5 flex items-center justify-between z-20">
        <Link to="/" className="flex items-center space-x-2">
          <span className="flex -space-x-1"><i className="w-3.5 h-3.5 bg-pink-500 rounded-full inline-block" /><i className="w-3.5 h-3.5 bg-purple-500 rounded-full inline-block" /></span>
          <span className="text-xl font-bold tracking-tight">RentPeople</span>
        </Link>
        <div className="hidden md:flex items-center space-x-8 text-sm font-medium">
          <Link to="/" className="text-violet-700">Home</Link>
          <Link to="/browse" className="text-[#4d485d] hover:text-violet-700 transition">Browse</Link>
          <a href="#how-it-works" className="text-[#4d485d] hover:text-violet-700 transition">How It Works</a>
          <a href="#about" className="text-[#4d485d] hover:text-violet-700 transition">About</a>
        </div>
        <div className="flex items-center space-x-3">
          <Link to="/login" className="px-5 py-2 text-sm font-medium text-violet-700 bg-white border border-violet-200 rounded-lg hover:border-violet-400 transition">Login</Link>
          <Link to="/login?mode=register" className="px-5 py-2 text-sm font-semibold text-white bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-lg hover:opacity-90 transition shadow-lg shadow-violet-200">Sign Up</Link>
        </div>
      </nav>
      {/* ---------------- HERO SECTION ---------------- */}
      <main className="relative w-full max-w-7xl mx-auto px-6 pt-4 pb-16 flex-1 flex flex-col justify-center">
        {/* Background Image / Person Portrait Positioning */}
        <div className="absolute right-0 top-0 bottom-0 w-full lg:w-1/2 pointer-events-none overflow-hidden rounded-2xl opacity-80 lg:opacity-100">
          {/* Warm background bokeh blur overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#f8f6ff] via-[#f8f6ff]/70 to-transparent z-10" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#f8f6ff] via-transparent to-transparent z-10" />
          
          <img
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=1000&auto=format&fit=crop"
            alt="Hero Verified Person"
            className="w-full h-full object-cover object-top"
          />

          {/* Decorative Cursive Text overlay on right side */}
          <div className="absolute right-8 top-12 z-20 text-right hidden lg:block select-none">
            <p className="font-serif italic text-3xl tracking-wide text-gray-200 opacity-90 leading-tight">
              Good <br /> People <br /> Brighter <br /> Days
            </p>
            <div className="mt-2 flex justify-end">
              <span className="text-pink-500 text-2xl">♥</span>
            </div>
          </div>
        </div>

        {/* Hero Content Left Container */}
        <div className="relative z-20 max-w-2xl">
          {/* Subtitle Badge */}
          <p className="text-xs font-bold tracking-widest text-[#786f91] uppercase mb-3">
            Real People. Real Moments.
          </p>

          {/* Main Headline */}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight mb-4">
            Hire Verified People <br />
            for <span className="text-violet-700">Any Occasion</span>
          </h1>

          {/* Subtext */}
          <p className="text-[#5d586e] text-base md:text-lg mb-8 max-w-xl leading-relaxed">
            Companionship, events, travel, networking, fitness <br className="hidden sm:inline" />
            and more. Your moments, our people.
          </p>

          {/* Search Card Container */}
          <div className="bg-white/90 backdrop-blur-md border border-violet-100 p-3 sm:p-4 rounded-2xl shadow-xl shadow-violet-100/70 mb-6">
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_1fr_auto] gap-3">
              {/* Category Dropdown */}
              <div className="relative">
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-[#fbfaff] border border-[#e6e0f3] text-[#332d42] text-sm rounded-xl px-4 py-3.5 appearance-none focus:outline-none focus:border-violet-500 transition cursor-pointer"
                >
                  <option value="" disabled selected>
                    What are you looking for?
                  </option>
                  <option value="companion">Date Companion</option>
                  <option value="travel">Travel Buddy</option>
                  <option value="event">Event Partner</option>
                  <option value="fitness">Fitness Buddy</option>
                </select>
                <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>

              {/* City Dropdown */}
              <div className="relative">
                <select
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="w-full bg-[#fbfaff] border border-[#e6e0f3] text-[#332d42] text-sm rounded-xl px-4 py-3.5 appearance-none focus:outline-none focus:border-violet-500 transition cursor-pointer"
                >
                  <option value="" disabled selected>
                    Select City
                  </option>
                  <option value="newyork">New York</option>
                  <option value="losangeles">Los Angeles</option>
                  <option value="london">London</option>
                  <option value="mumbai">Mumbai</option>
                </select>
                <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>

              {/* Search Button */}
              <button className="w-full sm:w-auto px-8 py-3.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:opacity-90 text-white font-semibold rounded-xl text-sm transition duration-200 shadow-lg shadow-violet-200">
                Search
              </button>
            </div>
          </div>

          {/* Popular Tag Pills */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-gray-400 font-medium mr-1">Popular:</span>
            {popularTags.map((tag) => (
              <button
                key={tag}
                className="px-3.5 py-1.5 bg-[#16181e] hover:bg-[#20232c] border border-gray-800 text-gray-300 text-xs rounded-full transition"
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* ---------------- FOOTER / FEATURE STRIP ---------------- */}
      <footer className="w-full bg-white border-t border-violet-100 py-8 z-20">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {features.map((item, idx) => (
            <div key={idx} className="flex flex-col items-center justify-center space-y-1.5">
              <div className="mb-1 p-2 bg-violet-100 rounded-xl">
                {item.icon}
              </div>
              <h4 className="text-sm font-semibold text-[#272033]">{item.title}</h4>
              <p className="text-xs text-[#786f91]">{item.subtitle}</p>
            </div>
          ))}
        </div>
      </footer>

    </div>
  );
}
