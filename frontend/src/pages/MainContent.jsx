import React, { useState } from 'react';
import { Heart, MapPin, ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';

const PEOPLE_DATA = [
  {
    id: 1,
    name: 'Kiara',
    age: 24,
    location: 'Mumbai',
    price: '₹1,500/hr',
    isOnline: true,
    tags: ['Data Companion', 'Travel'],
    image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=600&auto=format&fit=crop',
  },
  {
    id: 2,
    name: 'Rohan',
    age: 26,
    location: 'Delhi',
    price: '₹1,200/hr',
    isOnline: true,
    tags: ['Travel', 'Event'],
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=600&auto=format&fit=crop',
  },
  {
    id: 3,
    name: 'Aanya',
    age: 23,
    location: 'Bangalore',
    price: '₹1,000/hr',
    isOnline: true,
    tags: ['Conversation', 'Movies'],
    image: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?q=80&w=600&auto=format&fit=crop',
  },
  {
    id: 4,
    name: 'Arjun',
    age: 27,
    location: 'Mumbai',
    price: '₹1,800/hr',
    isOnline: true,
    tags: ['Fitness', 'Networking'],
    image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=600&auto=format&fit=crop',
  },
  {
    id: 5,
    name: 'Meera',
    age: 25,
    location: 'Pune',
    price: '₹1,200/hr',
    isOnline: true,
    tags: ['Event', 'Travel'],
    image: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?q=80&w=600&auto=format&fit=crop',
  },
  {
    id: 6,
    name: 'Kabir',
    age: 26,
    location: 'Delhi',
    price: '₹1,500/hr',
    isOnline: true,
    tags: ['Gaming', 'Conversation'],
    image: 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?q=80&w=600&auto=format&fit=crop',
  },
  {
    id: 7,
    name: 'Isha',
    age: 24,
    location: 'Mumbai',
    price: '₹1,000/hr',
    isOnline: true,
    tags: ['Photoshoot', 'Events'],
    image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=600&auto=format&fit=crop',
  },
  {
    id: 8,
    name: 'Vikram',
    age: 29,
    location: 'Bangalore',
    price: '₹1,800/hr',
    isOnline: true,
    tags: ['Networking', 'Travel'],
    image: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=600&auto=format&fit=crop',
  },
  
];

export default function MainContent() {
  const [favorites, setFavorites] = useState({});
  const [cityFilter, setCityFilter] = useState('Mumbai');
  const [sortBy, setSortBy] = useState('Popular');

  const toggleFavorite = (id) => {
    setFavorites((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <main className="flex-1 bg-[#f8f6ff] p-6 lg:p-8 overflow-y-auto text-[#171426]">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-[#171426] tracking-tight">
            Find People for Your Moments
          </h1>
          <p className="text-sm text-[#706a80] mt-1">
            Browse verified people based on your interests.
          </p>
        </div>

        {/* Filter Dropdowns */}
        <div className="flex items-center space-x-3">
          {/* Location Select */}
          <div className="relative">
            <div className="flex items-center bg-white border border-[#e4dff0] rounded-xl px-3 py-2 text-xs text-[#40394f] shadow-sm">
              <MapPin className="w-3.5 h-3.5 text-gray-400 mr-2" />
              <select
                value={cityFilter}
                onChange={(e) => setCityFilter(e.target.value)}
                className="bg-transparent text-[#40394f] text-xs focus:outline-none appearance-none pr-5 cursor-pointer font-medium"
              >
                <option value="Mumbai" className="bg-[#16181e]">Mumbai</option>
                <option value="Delhi" className="bg-[#16181e]">Delhi</option>
                <option value="Bangalore" className="bg-[#16181e]">Bangalore</option>
                <option value="Pune" className="bg-[#16181e]">Pune</option>
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400 absolute right-2.5 pointer-events-none" />
            </div>
          </div>

          {/* Sort Select */}
          <div className="relative">
            <div className="flex items-center bg-white border border-[#e4dff0] rounded-xl px-3 py-2 text-xs text-[#40394f] shadow-sm">
              <span className="text-gray-400 mr-1.5">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-transparent text-[#40394f] text-xs focus:outline-none appearance-none pr-5 cursor-pointer font-medium"
              >
                <option value="Popular" className="bg-[#16181e]">Popular</option>
                <option value="PriceLow" className="bg-[#16181e]">Price: Low to High</option>
                <option value="PriceHigh" className="bg-[#16181e]">Price: High to Low</option>
                <option value="Rating" className="bg-[#16181e]">Highest Rated</option>
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400 absolute right-2.5 pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      {/* Profile Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
        {PEOPLE_DATA.map((person) => {
          const isFav = favorites[person.id];

          return (
            <div
              key={person.id}
              className="bg-white border border-[#e7e1f2] rounded-2xl overflow-hidden hover:border-violet-300 hover:shadow-lg hover:shadow-violet-100 transition duration-200 group flex flex-col justify-between"
            >
              {/* Image Header with Badge */}
              <div className="relative h-48 w-full overflow-hidden bg-violet-100">
                <img
                  src={person.image}
                  alt={person.name}
                  className="w-full h-full object-cover object-top group-hover:scale-105 transition duration-300"
                />
                
                {/* Online Tag */}
                {person.isOnline && (
                  <div className="absolute bottom-3 right-3 bg-white/90 backdrop-blur-md border border-emerald-200 px-2.5 py-1 rounded-full flex items-center space-x-1.5">
                    <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                    <span className="text-[10px] font-semibold text-emerald-400">Online</span>
                  </div>
                )}
              </div>

              {/* Card Body */}
              <div className="p-4 flex-1 flex flex-col justify-between">
                <div>
                  {/* Name, Age and Heart Button */}
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-base font-bold text-[#24202e]">
                      {person.name}, {person.age}
                    </h3>
                    <button
                      onClick={() => toggleFavorite(person.id)}
                      className="text-gray-400 hover:text-pink-500 transition p-1"
                    >
                      <Heart
                        className={`w-4 h-4 ${
                          isFav ? 'text-pink-500 fill-pink-500' : 'text-gray-400'
                        }`}
                      />
                    </button>
                  </div>

                  {/* Location */}
                  <p className="text-xs text-[#706a80] flex items-center mb-3">
                    <MapPin className="w-3 h-3 text-gray-500 mr-1" />
                    {person.location}
                  </p>

                  {/* Price */}
                  <p className="text-sm font-extrabold text-[#24202e] mb-3">
                    {person.price}
                  </p>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5 pt-2 border-t border-[#eeeaf5]">
                  {person.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2.5 py-1 bg-violet-50 text-violet-700 text-[11px] font-medium rounded-md border border-violet-100"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <Link to={`/people/${person.name.toLowerCase()}`} className="mt-3 block rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 px-3 py-2 text-center text-xs font-semibold text-white">View profile</Link>
              </div>
            </div>
          );
        })}
      </div>
    </main>
  );
}
