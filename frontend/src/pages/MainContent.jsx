import React, { useEffect, useMemo, useState } from 'react';
import { Heart, MapPin, ChevronDown } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchPeople, formatPersonPrice, getLocationPreference, getPersonPrice } from './finderApi';
import { getStoredUser } from '../auth/auth';

function distanceKm(from, person) {
  const rawLat = person.lat ?? person.latitude;
  const rawLng = person.lng ?? person.longitude;
  if (rawLat == null || rawLng == null || rawLat === '' || rawLng === '') return null;
  const lat = Number(rawLat);
  const lng = Number(rawLng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  const radians = (degrees) => degrees * Math.PI / 180;
  const latDelta = radians(lat - from.lat);
  const lngDelta = radians(lng - from.lng);
  const a = Math.sin(latDelta / 2) ** 2
    + Math.cos(radians(from.lat)) * Math.cos(radians(lat)) * Math.sin(lngDelta / 2) ** 2;
  return 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

async function fetchNearbyDirectory(coordinates, city, userId) {
  const nearbyPeople = await fetchPeople({ ...coordinates, radius_km: 500, city, user_id: userId });
  return nearbyPeople
    .map((person) => {
      const distance = distanceKm(coordinates, person);
      return person.distance_km != null || distance == null
        ? person
        : { ...person, distance_km: distance };
    })
    .sort((a, b) => Number(a.distance_km ?? Infinity) - Number(b.distance_km ?? Infinity));
}

export default function MainContent() {
  const [searchParams] = useSearchParams();
  const [favorites, setFavorites] = useState({});
  const [sortBy, setSortBy] = useState('Popular');
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [nearMe, setNearMe] = useState(false);

  useEffect(() => {
    let active = true;
    const savedLocation = getLocationPreference();
    const mode = searchParams.get('mode') || savedLocation?.mode;
    const city = searchParams.get('city') || savedLocation?.city;
    const user = getStoredUser() || {};
    const latValue = searchParams.has('lat') ? searchParams.get('lat') : savedLocation?.lat;
    const lngValue = searchParams.has('lng') ? searchParams.get('lng') : savedLocation?.lng;
    const lat = Number(latValue);
    const lng = Number(lngValue);
    const hasCoordinates = latValue != null && lngValue != null && Number.isFinite(lat) && Number.isFinite(lng);
    setLoading(true);
    setLoadError('');
    const userCity = user.city || user.location;
    const userId = user.id || user.user_id || user.userId;
    const load = mode === 'near' && hasCoordinates
      ? fetchNearbyDirectory({ lat, lng }, city || userCity, userId)
      : city ? fetchPeople({ city }) : fetchPeople();
    load
      .then((results) => { if (active) { setPeople(results); setNearMe(mode === 'near' && hasCoordinates); } })
      .catch((error) => { if (active) setLoadError(error.message || 'Unable to load people.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [searchParams]);

  const visiblePeople = useMemo(() => {
    const results = [...people];
    if (nearMe && sortBy === 'Popular') results.sort((a, b) => Number(a.distance_km ?? Infinity) - Number(b.distance_km ?? Infinity));
    if (sortBy === 'PriceLow') results.sort((a, b) => getPersonPrice(a) - getPersonPrice(b));
    if (sortBy === 'PriceHigh') results.sort((a, b) => getPersonPrice(b) - getPersonPrice(a));
    return results;
  }, [people, sortBy, nearMe]);

  const toggleFavorite = (id) => {
    setFavorites((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <main className="flex-1 overflow-y-auto bg-[#f5f3ff] p-4 text-[#171426] sm:p-6 xl:p-8">
      {/* Header Bar */}
      {/* <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-[#171426] tracking-tight">
            Find People for Your Moments
          </h1>
          <p className="text-sm text-[#706a80] mt-1">
            Browse verified people based on your interests.
          </p>
        </div>
      </div> */}
      {/* Profile Cards Grid */}
      {loading && <p role="status" className="py-12 text-center text-sm text-[#706a80]">Loading people…</p>}
      {!loading && loadError && <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{loadError}</p>}
      {!loading && !loadError && visiblePeople.length === 0 && <p className="py-12 text-center text-sm text-[#706a80]">No people found for this location.</p>}
      {!loading && !loadError && visiblePeople.length > 0 && <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-4 2xl:grid-cols-4">
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
      <h3 className="text-base font-bold text-[#24202e] truncate pr-2">
        {person.name}
        {person.age ? `, ${person.age}` : ''}
      </h3>

      <button
        onClick={() => toggleFavorite(person.id)}
        className="text-gray-400 hover:text-pink-500 transition p-1 flex-shrink-0"
      >
        <Heart
          className={`w-4 h-4 ${
            isFav ? 'text-pink-500 fill-pink-500' : 'text-gray-400'
          }`}
        />
      </button>
    </div>

    {/* Location & Price - Same Line */}
    <div className="flex items-center justify-between gap-2 mb-3 min-w-0">
      {/* Location */}
      <p className="text-xs text-[#706a80] flex items-center min-w-0 flex-1">
        <MapPin className="w-3 h-3 text-gray-500 mr-1 flex-shrink-0" />

        <span className="truncate">
          {person.location || person.city}

          {person.distance_km != null && (
            <span className="ml-1 font-medium text-violet-700">
              · {Number(person.distance_km).toFixed(1)} km
            </span>
          )}
        </span>
      </p>

      {/* Price */}
      <p className="text-sm font-extrabold text-[#24202e] whitespace-nowrap flex-shrink-0">
        {person.price || `${formatPersonPrice(getPersonPrice(person))}/hr`}
      </p>
    </div>
  </div>

  {/* Tags - Maximum 2 */}
  <div className="flex flex-wrap gap-1.5 pt-2 border-t border-[#eeeaf5]">
    {(person.tags || []).slice(0, 2).map((tag) => (
      <span
        key={tag}
        className="px-1 py-0.5 bg-violet-50 text-violet-700 text-[10px] font-medium rounded-md border border-violet-100"
      >
        {tag}
      </span>
    ))}
  </div>

  {/* View Profile */}
  <Link
    to={`/people/${person.id}`}
    className="mt-3 block rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 px-3 py-2 text-center text-xs font-semibold text-white"
  >
    View profile
  </Link>
</div>
            </div>
          );
        })}
      </div>}
    </main>
  );
}
