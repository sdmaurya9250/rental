import React, { useEffect, useMemo, useState } from 'react';
import { Heart, MapPin, ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { fetchPeople, formatPersonPrice, getPersonPrice } from './finderApi';

export default function MainContent() {
  const [favorites, setFavorites] = useState({});
  const [cityFilter, setCityFilter] = useState('All');
  const [sortBy, setSortBy] = useState('Popular');
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let active = true;
    fetchPeople()
      .then((results) => { if (active) setPeople(results); })
      .catch((error) => { if (active) setLoadError(error.message || 'Unable to load people.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const cities = useMemo(() => [...new Set(people.map((person) => person.location).filter(Boolean))].sort(), [people]);
  const visiblePeople = useMemo(() => {
    const results = people.filter((person) => cityFilter === 'All' || person.location === cityFilter);
    if (sortBy === 'PriceLow') results.sort((a, b) => getPersonPrice(a) - getPersonPrice(b));
    if (sortBy === 'PriceHigh') results.sort((a, b) => getPersonPrice(b) - getPersonPrice(a));
    return results;
  }, [people, cityFilter, sortBy]);

  const toggleFavorite = (id) => {
    setFavorites((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <main className="flex-1 overflow-y-auto bg-[#f5f3ff] p-4 text-[#171426] sm:p-6 xl:p-8">
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
                <option value="All">All locations</option>
                {cities.map((city) => <option key={city} value={city}>{city}</option>)}
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
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400 absolute right-2.5 pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      {/* Profile Cards Grid */}
      {loading && <p role="status" className="py-12 text-center text-sm text-[#706a80]">Loading people…</p>}
      {!loading && loadError && <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{loadError}</p>}
      {!loading && !loadError && visiblePeople.length === 0 && <p className="py-12 text-center text-sm text-[#706a80]">No people found for this location.</p>}
      {!loading && !loadError && visiblePeople.length > 0 && <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
        {visiblePeople.map((person) => {
          const isFav = favorites[person.id];

          return (
            <div
              key={person.id}
              className="bg-white border border-[#e7e1f2] rounded-2xl overflow-hidden hover:border-violet-300 hover:shadow-lg hover:shadow-violet-100 transition duration-200 group flex flex-col justify-between"
            >
              {/* Image Header with Badge */}
              <div className="relative h-48 w-full overflow-hidden bg-violet-100">
                <img
                  src={person.image || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=600&auto=format&fit=crop'}
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
                      {person.name}{person.age ? `, ${person.age}` : ''}
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
                    {person.price || `${formatPersonPrice(getPersonPrice(person))}/hr`}
                  </p>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5 pt-2 border-t border-[#eeeaf5]">
                  {(person.tags || []).map((tag) => (
                    <span
                      key={tag}
                      className="px-2.5 py-1 bg-violet-50 text-violet-700 text-[11px] font-medium rounded-md border border-violet-100"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <Link to={`/people/${person.id}`} className="mt-3 block rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 px-3 py-2 text-center text-xs font-semibold text-white">View profile</Link>
              </div>
            </div>
          );
        })}
      </div>}
    </main>
  );
}
