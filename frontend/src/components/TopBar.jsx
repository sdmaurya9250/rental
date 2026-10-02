import { useEffect, useRef, useState } from 'react';
import { Bell, ChevronDown, Crosshair, MapPin, Menu, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getMyProfile, getStoredUser } from '../auth/auth';
import { geocodeCity, getCurrentLocation, reverseGeocode } from '../pages/finderApi';

export default function TopBar({ onMenuToggle }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(() => getStoredUser() || {});
  const [query, setQuery] = useState('');
  const [locationOpen, setLocationOpen] = useState(false);
  const [cityQuery, setCityQuery] = useState('');
  const [cityResults, setCityResults] = useState([]);
  const [citySearchLoading, setCitySearchLoading] = useState(false);
  const [locationBusy, setLocationBusy] = useState(false);
  const [locationError, setLocationError] = useState('');
  const [locationLabel, setLocationLabel] = useState('India');
  const locationRef = useRef(null);

  useEffect(() => {
    const closeOnOutsideClick = (event) => {
      if (!locationRef.current?.contains(event.target)) setLocationOpen(false);
    };
    document.addEventListener('mousedown', closeOnOutsideClick);
    return () => document.removeEventListener('mousedown', closeOnOutsideClick);
  }, []);

  useEffect(() => {
    if (cityQuery.trim().length < 2) { setCityResults([]); setCitySearchLoading(false); return undefined; }
    let active = true;
    setCitySearchLoading(true);
    const timer = window.setTimeout(() => {
      geocodeCity(cityQuery.trim())
        .then((results) => { if (active) setCityResults(results); })
        .catch((error) => { if (active) setLocationError(error.message || 'Unable to search cities.'); })
        .finally(() => { if (active) setCitySearchLoading(false); });
    }, 300);
    return () => { active = false; window.clearTimeout(timer); };
  }, [cityQuery]);

  useEffect(() => {
    let active = true;
    const refreshStoredUser = () => setUser(getStoredUser() || {});
    window.addEventListener('rp-profile-updated', refreshStoredUser);
    getMyProfile()
      .then((profile) => { if (active && profile) setUser({ ...(getStoredUser() || {}), ...(profile.profile || profile) }); })
      .catch(() => {});
    return () => {
      active = false;
      window.removeEventListener('rp-profile-updated', refreshStoredUser);
    };
  }, []);

  const displayName = user?.fullName || user?.full_name || user?.name || user?.username || user?.email || 'My account';
  const initials = displayName === 'My account' ? 'M' : displayName.charAt(0).toUpperCase();
  const profileImage = user?.image || user?.profile_image || user?.avatar_url || user?.photo || '';

  function submitSearch(event) {
    event.preventDefault();
    navigate(`/search${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ''}`);
  }

  async function chooseCurrentLocation() {
    setLocationBusy(true);
    setLocationError('');
    try {
      const coordinates = await getCurrentLocation();
      const place = await reverseGeocode(coordinates).catch(() => ({}));
      const label = place.city || 'Near me';
      setLocationLabel(label);
      const params = new URLSearchParams({ ...coordinates, ...(place.city ? { city: place.city } : {}) });
      params.set('mode', 'near');
      navigate(`/browse?${params}`);
      setLocationOpen(false);
    } catch (error) {
      setLocationError(error.message || 'Unable to detect your location.');
    } finally {
      setLocationBusy(false);
    }
  }

  function chooseCity(city) {
    setLocationLabel(city.city || city.name);
    const params = new URLSearchParams({ city: city.city || city.name });
    if (city.lat != null) params.set('lat', city.lat);
    if (city.lng != null) params.set('lng', city.lng);
    params.set('mode', 'city');
    navigate(`/browse?${params}`);
    setLocationOpen(false);
    setCityQuery('');
    setLocationError('');
  }

  async function choosePopularLocation(location) {
    setLocationError('');
    setLocationBusy(true);
    try {
      const results = await geocodeCity(location);
      const match = results[0];
      chooseCity(match ? { ...match, city: match.city || location } : { city: location, name: location });
    } catch (error) {
      setLocationError(error.message || 'Unable to load this location.');
    } finally {
      setLocationBusy(false);
    }
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 min-w-0 items-center gap-2 border-b border-violet-100 bg-white/95 px-3 shadow-[0_2px_12px_rgba(40,24,90,0.04)] backdrop-blur sm:gap-3 sm:px-5 lg:px-6">
      <button type="button" onClick={onMenuToggle} className="shrink-0 rounded-lg p-2 text-violet-700 hover:bg-violet-50 lg:hidden" aria-label="Open menu"><Menu className="h-5 w-5" /></button>

      <form onSubmit={submitSearch} className="contents md:flex md:min-w-0 md:flex-1 md:items-center md:gap-2">
        <label className="hidden min-w-0 flex-1 items-center gap-2 rounded-xl border border-violet-100 bg-[#fcfbff] px-3 py-2 text-[#8b849d] focus-within:border-violet-300 focus-within:ring-2 focus-within:ring-violet-100 md:flex">
          <Search className="h-4 w-4 shrink-0 text-violet-500" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search people, services or activities…" className="min-w-0 flex-1 bg-transparent text-sm text-[#24202e] outline-none placeholder:text-[#a39cb4]" />
        </label>
        <div ref={locationRef} className="relative shrink-0 md:ml-auto lg:ml-0">
          <button type="button" onClick={() => { setLocationOpen((open) => !open); setLocationError(''); }} aria-expanded={locationOpen} className="flex max-w-32 items-center gap-1.5 rounded-full border border-blue-600 bg-white px-3 py-2 text-xs font-medium text-[#30343b] sm:max-w-48 lg:max-w-56"><MapPin className="h-4 w-4 shrink-0 text-blue-600" /><span className="truncate">{locationLabel}</span><ChevronDown className="h-3.5 w-3.5 shrink-0 text-[#9aa0a6]" /></button>
          {locationOpen && <div className="absolute right-0 top-12 z-50 w-[min(16rem,calc(100vw-1.5rem))] overflow-hidden rounded-2xl border border-[#d8d8d8] bg-white shadow-xl lg:left-0 lg:right-auto">
            <button type="button" onClick={chooseCurrentLocation} disabled={locationBusy} className="flex w-full items-center gap-3 bg-[#eaf3ff] px-4 py-3 text-left hover:bg-[#dcecff] disabled:opacity-60">
              <Crosshair className="h-5 w-5 shrink-0 text-blue-600" />
              <span className="min-w-0"><span className="block text-sm font-bold text-blue-700">{locationBusy ? 'Detecting location…' : 'Use current location'}</span><span className="block text-xs leading-4 text-blue-600">{locationError || 'Find nearby people around you'}</span></span>
            </button>
            <div className="border-t border-[#e5e5e5] px-4 pb-1 pt-3">
              <p className="text-[10px] font-medium uppercase tracking-wide text-[#858585]">Popular locations</p>
            </div>
            <div className="max-h-56 overflow-y-auto px-1 pb-1">
              {['Kerala', 'Tamil Nadu', 'Punjab', 'Maharashtra'].map((location) => <button key={location} type="button" onClick={() => choosePopularLocation(location)} disabled={locationBusy} className="flex w-full items-center gap-3 rounded-lg px-3 py-3 text-left text-sm text-[#24202e] hover:bg-[#f5f7fa] disabled:opacity-60"><MapPin className="h-5 w-5 shrink-0 text-[#8a8f98]" /><span>{location}</span></button>)}
            </div>
            <div className="border-t border-[#e5e5e5] p-3">
              <label className="block text-xs font-semibold text-[#706a80]">Search a city
                <input value={cityQuery} onChange={(event) => { setCityQuery(event.target.value); setLocationError(''); }} placeholder="Type a city name…" className="mt-1.5 w-full rounded-lg border border-violet-100 px-3 py-2 text-sm font-normal text-[#24202e] outline-none focus:ring-2 focus:ring-violet-200" />
              </label>
              {cityResults.length > 0 && <div className="mt-2 max-h-36 overflow-y-auto">{cityResults.map((city, index) => <button key={`${city.name}-${index}`} type="button" onClick={() => chooseCity(city)} className="block w-full rounded-lg px-2 py-2 text-left hover:bg-violet-50"><span className="block text-sm font-semibold text-[#24202e]">{city.city || city.name}</span><span className="block truncate text-xs text-[#827b95]">{city.name}</span></button>)}</div>}
              {citySearchLoading && <p className="mt-2 text-xs text-[#827b95]">Searching cities…</p>}
              {!citySearchLoading && cityQuery.trim().length >= 2 && !cityResults.length && !locationError && <p className="mt-2 text-xs text-[#827b95]">No cities found.</p>}
              {locationError && <p role="alert" className="mt-2 text-xs text-rose-700">{locationError}</p>}
            </div>
          </div>}
        </div>
        <button type="submit" className="hidden shrink-0 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-500 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:opacity-90 md:block">Search</button>
      </form>
      <button type="button" onClick={() => navigate('/search')} className="rounded-lg p-2 text-violet-700 hover:bg-violet-50 md:hidden" aria-label="Search"><Search className="h-5 w-5" /></button>

      <div className="ml-auto flex shrink-0 items-center gap-2 sm:gap-3 md:ml-1">
        <button type="button" className="relative rounded-lg p-2 text-[#706a80] hover:bg-violet-50 hover:text-violet-700" aria-label="Notifications"><Bell className="h-[18px] w-[18px]" /></button>
        <button type="button" onClick={() => navigate('/my-profile')} className="flex min-w-0 items-center gap-2 rounded-xl p-1 hover:bg-violet-50">
          <span className="grid h-9 w-9 shrink-0 place-items-center overflow-hidden rounded-full bg-gradient-to-br from-fuchsia-500 to-violet-600 text-sm font-bold text-white ring-2 ring-violet-100">{profileImage ? <img src={profileImage} alt={`${displayName} profile`} className="h-full w-full object-cover" /> : initials}</span>
          <span className="hidden max-w-32 text-left sm:block"><span className="block truncate text-xs font-bold text-[#24202e]">{displayName}</span><span className="block text-[10px] text-[#8b849d]">Member</span></span>
          <ChevronDown className="hidden h-3.5 w-3.5 text-[#8b849d] sm:block" />
        </button>
      </div>
    </header>
  );
}
