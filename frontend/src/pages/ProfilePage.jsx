import { useEffect, useMemo, useState } from 'react';
import { 
  CheckCircle2, 
  Heart, 
  MapPin, 
  Star, 
  Calendar, 
  MessageSquare, 
  Clock, 
  User, 
  Briefcase, 
  Globe, 
  ShieldCheck, 
  ChevronLeft, 
  ChevronRight,
  Plus,
  LoaderCircle,
  Wallet,
  X
} from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import FeaturePage from '../components/FeaturePage';
import { getStoredUser, isAuthenticated } from '../auth/auth';
import { addFavoriteRecord, checkFavoriteRecord, createBookingRecord, fetchPersonRatings, formatPersonPrice as formatPrice, fetchPersonById, geocodeCity, getCurrentLocation, getPersonPrice, removeFavoriteRecord } from './finderApi';

function localDate() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

function slug(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function durationHours(service) {
  if (/full day/i.test(service.duration || '')) return 6;
  return Number(service.duration?.match(/\d+/)?.[0]) || 1;
}

function formatTime(totalMinutes) {
  const minutes = totalMinutes % (24 * 60);
  return `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`;
}

function formatAvailability(value) {
  if (!value) return 'Wed, Thu, Fri, Sat, Sun';
  try {
    const parsed = typeof value === 'string' ? JSON.parse(value) : value;
    if (Array.isArray(parsed.days) && parsed.days.length) return parsed.days.join(', ');
  } catch {
    return value;
  }
  return typeof value === 'string' ? value : 'Wed, Thu, Fri, Sat, Sun';
}

export default function ProfilePage() {
  const { personId } = useParams();
  const [person, setPerson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadError('');
    fetchPersonById(personId)
      .then((result) => { if (active) setPerson({ ...result, rate: getPersonPrice(result), tags: result.tags || [] }); })
      .catch((error) => { if (active) setLoadError(error.message || 'Unable to load this profile.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [personId]);

  if (loading) return <FeaturePage title="Loading profile…" subtitle="Fetching profile details." />;
  if (loadError || !person) return <FeaturePage title="Profile unavailable" subtitle={loadError || 'This profile could not be found.'}><Link to="/browse" className="text-sm font-medium text-purple-700 hover:underline">← Back to browse</Link></FeaturePage>;

  return <ProfileDetails person={person} />;
}

function ProfileDetails({ person }) {
  const signedInUser = getStoredUser() || {};
  const signedInRole = String(signedInUser.want_to || signedInUser.wantTo || signedInUser.accountIntent || '').trim().toLowerCase();
  const isBecomeOnly = ['companion', 'become a rentcopartner', 'become'].includes(signedInRole);
  const services = useMemo(() => (person.services || [
    { 
      title: 'Movie Partner', 
      price: person.rate || 1000, 
      duration: '1 hr',
      image: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=300&auto=format&fit=crop',
      description: 'Watch together, share laughs and enjoy your favorite movies.'
    },
    { 
      title: 'Café & Food Partner', 
      price: (person.rate || 1000) * 1.5, 
      duration: '1 hr', 
      isPopular: true,
      image: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=300&auto=format&fit=crop',
      description: 'Enjoy food, coffee and great conversations at cafés and restaurants.'
    },
    { 
      title: 'Domestic Help', 
      price: (person.rate || 1000), 
      duration: '1 hr',
      image: 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=300&auto=format&fit=crop',
      description: 'Assistance with household tasks and daily activities.'
    },
  ]).map((service, index) => ({
    ...service,
    id: String(service.id || slug(service.title || service.name || `service-${index + 1}`)),
    title: service.title || service.name || 'Service',
    price: Number(service.price) || Number(person.rate) || 1000,
  })), [person]);

  const galleryImages = person.images || [
    person.image || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=800&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&q=80&w=800',
    'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&q=80&w=800',
  ];

  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const activeImage = galleryImages[activeImageIndex] || galleryImages[0];
  const [selectedServiceId, setSelectedServiceId] = useState(services[0]?.id || '');
  const [bookingDate, setBookingDate] = useState(localDate);
  const [durationHoursSelected, setDurationHoursSelected] = useState(1);
  const [location, setLocation] = useState(person.location || '');
  const [addressSuggestions, setAddressSuggestions] = useState([]);
  const [addressSearchLoading, setAddressSearchLoading] = useState(false);
  const [showAddressSuggestions, setShowAddressSuggestions] = useState(false);
  const [addressSearchError, setAddressSearchError] = useState('');
  const [addressProximity, setAddressProximity] = useState(() => {
    const lat = signedInUser.lat == null ? NaN : Number(signedInUser.lat);
    const lng = signedInUser.lng == null ? NaN : Number(signedInUser.lng);
    return Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lng } : null;
  });
  const [requestedAddressLocation, setRequestedAddressLocation] = useState(false);
  const [addressLocationLoading, setAddressLocationLoading] = useState(false);
  const [specialRequirements, setSpecialRequirements] = useState('');
  const [customerNote, setCustomerNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [insufficientBalance, setInsufficientBalance] = useState(null);
  const [createdBooking, setCreatedBooking] = useState(null);
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [ratingSummary, setRatingSummary] = useState(null);
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);
  const [favoriteError, setFavoriteError] = useState('');
  const viewerId = signedInUser.id || signedInUser.user_id || signedInUser.userId;
  const canFavorite = isAuthenticated() && !isBecomeOnly && String(viewerId || '') !== String(person.id);

  useEffect(() => {
    const query = location.trim();
    if (!showAddressSuggestions || query.length < 2) {
      setAddressSuggestions([]);
      setAddressSearchLoading(false);
      return undefined;
    }
    if (!addressProximity && addressLocationLoading) {
      setAddressSearchLoading(true);
      return undefined;
    }

    let active = true;
    setAddressSearchLoading(true);
    setAddressSearchError('');
    const timer = window.setTimeout(() => {
      geocodeCity(query, addressProximity)
        .then((results) => { if (active) setAddressSuggestions(results); })
        .catch((error) => { if (active) setAddressSearchError(error.message || 'Unable to load address suggestions.'); })
        .finally(() => { if (active) setAddressSearchLoading(false); });
    }, 300);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [location, showAddressSuggestions, addressProximity, addressLocationLoading]);

  function openAddressSuggestions() {
    setShowAddressSuggestions(true);
    if (addressProximity || requestedAddressLocation) return;
    setRequestedAddressLocation(true);
    setAddressLocationLoading(true);
    getCurrentLocation()
      .then(setAddressProximity)
      .catch(() => {})
      .finally(() => setAddressLocationLoading(false));
  }

  useEffect(() => {
    let active = true;
    setRatingSummary(null);
    fetchPersonRatings(person.id)
      .then((result) => { if (active) setRatingSummary(result); })
      .catch(() => { if (active) setRatingSummary({ rating_count: person.rating_count || person.ratingCount || person.reviewsCount || 0, rating_avg: person.rating_avg || person.rating || 0 }); });
    return () => { active = false; };
  }, [person.id, person.rating_count, person.ratingCount, person.reviewsCount, person.rating_avg, person.rating]);

  const reviewCount = Number(ratingSummary?.rating_count ?? person.rating_count ?? person.ratingCount ?? person.reviewsCount ?? 0);
  const averageRating = Number(ratingSummary?.rating_avg ?? person.rating_avg ?? person.rating ?? 0);

  useEffect(() => {
    setIsFavorite(false);
    if (!canFavorite || !person.id) return undefined;
    let active = true;
    setFavoriteLoading(true);
    checkFavoriteRecord(person.id)
      .then((result) => { if (active) setIsFavorite(Boolean(result?.is_favorite)); })
      .catch(() => {})
      .finally(() => { if (active) setFavoriteLoading(false); });
    return () => { active = false; };
  }, [canFavorite, person.id]);

  const selectedService = services.find((service) => service.id === selectedServiceId) || services[0];
  const durationMinutes = durationHoursSelected * 60;
  const startTime = '12:00';
  const endTime = formatTime(12 * 60 + durationMinutes);
  const price = selectedService && durationMinutes > 0
    ? Math.round(selectedService.price * durationHoursSelected / durationHours(selectedService))
    : 0;
  const platformFee = Math.round(price * 0.125);
  const totalAmount = price + platformFee;

  const interests = person.tags?.length ? person.tags : ['Movie Partner', 'Café & Food Partner', 'Domestic Help', 'Travel Buddy', 'Event Partner'];

  const handlePrevImage = () => {
    setActiveImageIndex((prev) => (prev === 0 ? galleryImages.length - 1 : prev - 1));
  };

  const handleNextImage = () => {
    setActiveImageIndex((prev) => (prev === galleryImages.length - 1 ? 0 : prev + 1));
  };

  async function toggleFavorite() {
    if (!canFavorite || favoriteLoading) return;
    setFavoriteLoading(true);
    setFavoriteError('');
    try {
      if (isFavorite) {
        await removeFavoriteRecord(person.id);
        setIsFavorite(false);
      } else {
        await addFavoriteRecord(person.id);
        setIsFavorite(true);
      }
    } catch (error) {
      setFavoriteError(error.message || 'Unable to update favorites.');
    } finally {
      setFavoriteLoading(false);
    }
  }

  async function submitBooking(event) {
    event.preventDefault();
    setBookingError('');
    setCreatedBooking(null);
    if (!isAuthenticated()) {
      setBookingError('Please sign in before submitting a booking.');
      return;
    }
    if (!selectedService || durationMinutes <= 0) {
      setBookingError('Choose a valid booking duration.');
      return;
    }
    if (!bookingDate || !location.trim()) {
      setBookingError('Please complete the date and location.');
      return;
    }

    setSubmitting(true);
    try {
      const booking = await createBookingRecord({
        booking_date: bookingDate,
        start_time: startTime,
        end_time: endTime,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata',
        duration_minutes: durationMinutes,
        location_type: 'in_person',
        location: location.trim(),
        service_id: selectedService.id,
        service_name: selectedService.title,
        rent_person_id: person.id,
        special_requirements: specialRequirements.trim() || null,
        customer_note: customerNote.trim() || null,
        price,
        platform_fee: platformFee,
        total_amount: totalAmount,
      });
      setCreatedBooking(booking);
    } catch (error) {
      if (error.code === 'INSUFFICIENT_BALANCE' || error.data?.code === 'INSUFFICIENT_BALANCE') {
        setInsufficientBalance(error.data || error);
      } else {
        setBookingError(error.message || 'Unable to submit this booking. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f8f7fc] p-4 md:p-6 font-sans text-gray-800">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Top Header Link */}
        <div>
          <Link to="/browse" className="inline-flex items-center text-sm font-medium text-purple-700 hover:text-purple-900 transition">
            ← Back to browse
          </Link>
        </div>

        {/* Profile Main Section */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column - Gallery & Actions */}
          <div className="lg:col-span-3 space-y-4">
            {/* Image Carousel Card */}
            <div className="relative rounded-2xl overflow-hidden bg-black aspect-square group shadow-sm">
              <img src={activeImage} alt={`${person.name} profile photo`} width="600" height="600" loading="lazy" className="w-full h-full object-cover" />
              
              {person.isOnline !== false && (
                <span className="absolute top-3 left-3 bg-emerald-500/90 text-white text-xs px-2.5 py-1 rounded-full font-medium flex items-center gap-1 backdrop-blur-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span> Online
                </span>
              )}

              {canFavorite && <button type="button" onClick={toggleFavorite} disabled={favoriteLoading} aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'} aria-pressed={isFavorite} className="absolute top-3 right-3 p-2 rounded-full bg-white/80 text-gray-700 hover:text-rose-500 hover:bg-white transition shadow-sm disabled:opacity-60">
                <Heart className={`w-4 h-4 ${isFavorite ? 'fill-rose-500 text-rose-500' : ''}`} />
              </button>}

              <button onClick={handlePrevImage} className="absolute left-2 top-1/2 -translate-y-1/2 p-1.5 rounded-full bg-black/40 text-white opacity-0 group-hover:opacity-100 hover:bg-black/60 transition">
                <ChevronLeft className="w-5 h-5" />
              </button>
              
              <button onClick={handleNextImage} className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-full bg-black/40 text-white opacity-0 group-hover:opacity-100 hover:bg-black/60 transition">
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            {/* Thumbnail Navigation */}
            <div className="grid grid-cols-5 gap-2">
              {galleryImages.slice(0, 5).map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveImageIndex(idx)}
                  className={`relative rounded-xl overflow-hidden aspect-square border-2 transition ${
                    activeImageIndex === idx ? 'border-purple-600' : 'border-transparent opacity-70 hover:opacity-100'
                  }`}
                >
                  <img src={img} alt={`${person.name} photo ${idx + 1}`} width="120" height="120" loading="lazy" className="w-full h-full object-cover" />
                  {idx === 4 && galleryImages.length > 5 && (
                    <div className="absolute inset-0 bg-black/60 text-white text-xs font-bold flex items-center justify-center">
                      +{galleryImages.length - 4}
                    </div>
                  )}
                </button>
              ))}
            </div>

            {/* Stats Card */}
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-purple-50 grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="flex items-center justify-center gap-1 text-amber-500 font-bold text-sm">
                  <Star className="w-4 h-4 fill-amber-400" /> {reviewCount ? averageRating.toFixed(1) : 'New'}
                </div>
                <p className="text-[10px] text-gray-500 mt-0.5">{reviewCount ? `(${reviewCount} reviews)` : 'No reviews yet'}</p>
              </div>
              <div className="border-x border-gray-100">
                <div className="flex items-center justify-center gap-1 text-purple-600 font-bold text-sm">
                  <Calendar className="w-3.5 h-3.5" /> {person.bookingsCount || '320+'}
                </div>
                <p className="text-[10px] text-gray-500 mt-0.5">Bookings</p>
              </div>
              <div>
                <div className="flex items-center justify-center gap-1 text-pink-500 font-bold text-sm">
                  <Heart className="w-3.5 h-3.5" /> {person.responseRate || '96%'}
                </div>
                <p className="text-[10px] text-gray-500 mt-0.5">Response rate</p>
              </div>
            </div>

            {/* CTAs */}
            <div className="space-y-2">
              {/* <button className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-medium text-sm rounded-xl shadow-md shadow-purple-200 transition flex items-center justify-center gap-2">
                <MessageSquare className="w-4 h-4" /> Send Message
              </button> */}
              {canFavorite && <button type="button" onClick={toggleFavorite} disabled={favoriteLoading} aria-pressed={isFavorite} className="w-full py-2.5 border border-purple-200 text-purple-700 hover:bg-purple-50 font-medium text-sm rounded-xl transition flex items-center justify-center gap-2 disabled:opacity-60">
                <Heart className={`w-4 h-4 ${isFavorite ? 'fill-rose-500 text-rose-500' : ''}`} /> {favoriteLoading ? 'Updating…' : isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
              </button>}
              {favoriteError && <p role="alert" className="text-xs text-rose-600">{favoriteError}</p>}
            </div>
          </div>

          {/* Center Column - Profile Info */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-6 shadow-sm border border-purple-50 space-y-6">
            {/* Title & Location */}
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900">{person.name}</h1>
                <CheckCircle2 className="w-5 h-5 text-blue-500 fill-blue-500 stroke-white" />
              </div>
              <p className="flex items-center gap-1 text-xs text-gray-500 mt-1">
                <MapPin className="w-3.5 h-3.5 text-gray-400" /> {person.location || 'Mumbai, Maharashtra'}
              </p>

              {/* Status Badges */}
              <div className="flex flex-wrap gap-2 mt-3">
                <span className="bg-emerald-50 text-emerald-600 text-xs font-semibold px-2.5 py-1 rounded-md border border-emerald-100 flex items-center gap-1">
                  ● Online now
                </span>
                <span className="bg-purple-50 text-purple-600 text-xs font-semibold px-2.5 py-1 rounded-md border border-purple-100 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> ID Verified
                </span>
                <span className="bg-amber-50 text-amber-600 text-xs font-semibold px-2.5 py-1 rounded-md border border-amber-100 flex items-center gap-1">
                  ★ Top Rated
                </span>
              </div>
            </div>

            {/* About Me */}
            <div>
              <h2 className="text-sm font-bold text-gray-900 mb-2">About me</h2>
              <p className="text-xs leading-relaxed text-gray-600">
                {person.bio || "Lorem ipsum is a standard placeholder or dummy text widely used in graphic design, publishing, and web development to preview layouts and typography. Lorem ipsum is a standard placeholder or dummy text widely used in graphic design, publishing, and web development to preview layouts and typography."}
              </p>
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-purple-50/40 rounded-xl p-3 border border-purple-100/50">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-white text-purple-600 shadow-xs"><User className="w-4 h-4" /></div>
                <div>
                  <p className="text-[10px] text-gray-400 font-medium">Gender</p>
                  <p className="text-xs font-semibold text-gray-700">{person.gender || 'Male'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-white text-purple-600 shadow-xs"><Briefcase className="w-4 h-4" /></div>
                <div>
                  <p className="text-[10px] text-gray-400 font-medium">Role</p>
                  <p className="text-xs font-semibold text-gray-700">{String(person.want_to || '').toLowerCase() === 'companion' ? 'Become a Partner' : 'Find a Partner'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-white text-purple-600 shadow-xs"><Globe className="w-4 h-4" /></div>
                <div>
                  <p className="text-[10px] text-gray-400 font-medium">Languages</p>
                  <p className="text-xs font-semibold text-gray-700">{person.languages?.join(', ') || 'English, Marathi, Hindi'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-white text-purple-600 shadow-xs"><Clock className="w-4 h-4" /></div>
                <div>
                  <p className="text-[10px] text-gray-400 font-medium">Response time</p>
                  <p className="text-xs font-semibold text-gray-700">Within 1 hour</p>
                </div>
              </div>
            </div>

            {/* Interests / Tags */}
            <div>
              <h2 className="text-sm font-bold text-gray-900 mb-2">Interests</h2>
              <div className="flex flex-wrap gap-2">
                {interests.map((tag, idx) => {
                  const colors = [
                    'bg-purple-50 text-purple-600 border-purple-100',
                    'bg-pink-50 text-pink-600 border-pink-100',
                    'bg-sky-50 text-sky-600 border-sky-100',
                    'bg-emerald-50 text-emerald-600 border-emerald-100',
                    'bg-amber-50 text-amber-600 border-amber-100',
                  ];
                  const colorStyle = colors[idx % colors.length];
                  return (
                    <span key={idx} className={`text-xs font-medium px-3 py-1.5 rounded-lg border ${colorStyle}`}>
                      {tag}
                    </span>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column - Availability & Rating Breakdown */}
          <div className="lg:col-span-3 space-y-4">
            {/* Available This Week Card */}
            <div className="bg-purple-50/60 rounded-2xl p-4 border border-purple-100 flex items-start gap-3">
              <div className="p-2 bg-purple-100 rounded-xl text-purple-600">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-gray-900">Available This Week</h3>
                <p className="text-[11px] text-purple-700 mt-1 font-medium flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> 
                  {formatAvailability(person.availability || person.availableTime)}
                </p>
              </div>
            </div>

            {/* Reviews Breakdown Card */}
            {reviewCount > 0 && <div className="bg-white rounded-2xl p-4 shadow-sm border border-purple-50 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-900">Reviews ({reviewCount})</h3>
                <Link to="#reviews" className="text-xs text-purple-600 font-semibold hover:underline">View all →</Link>
              </div>

              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-gray-900">{averageRating.toFixed(1)}</span>
                <span className="text-xs text-gray-400">/5</span>
                <div className="flex text-amber-400 text-xs ml-1">
                  {'★'.repeat(5)}
                </div>
              </div>

              {/* Rating Bars */}
              <div className="space-y-1.5 text-[11px] text-gray-500">
                {[
                  { star: '5 star', percent: 85 },
                  { star: '4 star', percent: 10 },
                  { star: '3 star', percent: 4 },
                  { star: '2 star', percent: 1 },
                  { star: '1 star', percent: 0 },
                ].map((item) => (
                  <div key={item.star} className="flex items-center gap-2">
                    <span className="w-10 text-gray-400 text-right">{item.star}</span>
                    <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-600 rounded-full" style={{ width: `${item.percent}%` }}></div>
                    </div>
                    <span className="w-6 text-gray-400">{item.percent}%</span>
                  </div>
                ))}
              </div>
            </div>}
          </div>
        </div>

        {/* Services & Prices Section */}
<div className="bg-white rounded-2xl p-6 shadow-sm border border-purple-50 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-purple-100 rounded-lg text-purple-600">
                  <Briefcase className="w-4 h-4" />
                </div>
                <h2 className="text-base font-bold text-gray-900">Services & prices</h2>
              </div>
              <p className="text-xs text-gray-500 mt-1">{isBecomeOnly ? `Available services and prices from ${person.name}.` : `Choose from ${person.name}'s available services and book an appointment.`}</p>
            </div>
            
            {!isBecomeOnly && (
            <button 
              type="button" 
              onClick={() => setShowBookingForm(!showBookingForm)} 
              className="bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold px-4 py-2.5 rounded-xl transition shadow-sm flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4" /> Add Book Appointment
            </button>
            )}
          </div>

          {/* Service Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {services.map((service) => {
              const isSelected = selectedServiceId === service.id;
              return (
                <div 
                  key={service.id} 
                  className={`relative rounded-2xl border transition-all p-4 flex flex-col justify-between ${
                    isSelected ? 'border-purple-600 bg-purple-50/20 ring-2 ring-purple-600/20' : 'border-gray-100 hover:border-purple-200'
                  }`}
                >
                  {service.isPopular && (
                    <span className="absolute -top-2.5 right-4 bg-purple-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-md shadow-xs">
                      Most Popular
                    </span>
                  )}

                  {/* Card Content */}
                  <div className="space-y-1">
                    <h3 className="text-xs font-bold text-gray-900">{service.title}</h3>
                    <p className="text-xs font-semibold text-purple-700">
                      {formatPrice(service.price)} <span className="text-[10px] text-gray-400 font-normal">/ {service.duration || '1 hr'}</span>
                    </p>
                    <p className="text-[10px] text-gray-500 line-clamp-2">
                      {service.description || 'Quality partner service provided with full attention.'}
                    </p>
                  </div>

                  {!isBecomeOnly && <button
                    type="button"
                    onClick={() => {
                      setSelectedServiceId(service.id);
                      setCreatedBooking(null);
                      setShowBookingForm(true);
                    }}
                    className={`mt-3 text-[11px] font-semibold py-1.5 px-3 rounded-lg border transition text-center w-fit ${
                      isSelected 
                        ? 'bg-purple-600 text-white border-purple-600' 
                        : 'bg-purple-50 text-purple-700 border-purple-100 hover:bg-purple-100'
                    }`}
                  >
                    Book Now →
                  </button>}
                </div>
              );
            })}
          </div>
        </div>

        {/* Booking Form (Toggled or inline) */}
        {!isBecomeOnly && showBookingForm && (
          <form onSubmit={submitBooking} className="grid gap-6 lg:grid-cols-[1fr_320px] bg-white p-6 rounded-2xl border border-purple-100 shadow-sm">
            <div className="space-y-5">
              <section>
                <h2 className="text-base font-bold text-gray-900">Book {person.name}</h2>
                <p className="mt-0.5 text-xs text-gray-500">Select the service, booking date, duration, and address.</p>
                
                <div className="mt-3 grid gap-2 sm:grid-cols-3">
                  {services.map((service) => (
                    <button 
                      key={service.id} 
                      type="button" 
                      onClick={() => { setSelectedServiceId(service.id); setCreatedBooking(null); }} 
                      className={`rounded-xl border p-2.5 text-left transition ${selectedServiceId === service.id ? 'border-purple-600 bg-purple-50 ring-1 ring-purple-400' : 'border-gray-200 hover:border-purple-200'}`}
                    >
                      <span className="block text-xs font-semibold text-gray-800">{service.title}</span>
                      <span className="mt-0.5 block text-[11px] text-purple-700">{formatPrice(service.price)} · {service.duration || 'hourly'}</span>
                    </button>
                  ))}
                </div>
              </section>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="text-xs font-semibold text-gray-700">Booking date
                  <input required type="date" min={localDate()} value={bookingDate} onChange={(event) => setBookingDate(event.target.value)} className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-xs font-normal focus:ring-2 focus:ring-purple-500 outline-none" />
                </label>
                <label className="text-xs font-semibold text-gray-700">Duration
                  <select value={durationHoursSelected} onChange={(event) => setDurationHoursSelected(Number(event.target.value))} className="mt-1 w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-normal focus:ring-2 focus:ring-purple-500 outline-none">
                    {Array.from({ length: 12 }, (_, index) => index + 1).map((hours) => <option key={hours} value={hours}>{hours} {hours === 1 ? 'hour' : 'hours'}</option>)}
                  </select>
                </label>
              </div>

              <div className="relative">
                <label htmlFor="booking-address" className="block text-xs font-semibold text-gray-700">Address</label>
                <input
                  id="booking-address"
                  required
                  autoComplete="street-address"
                  value={location}
                  onFocus={openAddressSuggestions}
                  onChange={(event) => { setLocation(event.target.value); setShowAddressSuggestions(true); }}
                  placeholder="Search for an address or venue"
                  className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-xs font-normal outline-none focus:ring-2 focus:ring-purple-500"
                />
                {showAddressSuggestions && location.trim().length >= 2 && (
                  <div className="absolute inset-x-0 top-full z-20 mt-1 overflow-hidden rounded-xl border border-purple-100 bg-white shadow-lg" role="listbox" aria-label="Address suggestions">
                    {addressSearchLoading ? (
                      <p className="flex items-center gap-2 px-3 py-3 text-xs text-gray-500"><LoaderCircle className="h-3.5 w-3.5 animate-spin" />{addressLocationLoading ? 'Finding nearby places…' : 'Searching nearby places…'}</p>
                    ) : addressSearchError ? (
                      <p role="status" className="px-3 py-3 text-xs text-gray-500">Suggestions are unavailable. You can enter the address manually.</p>
                    ) : addressSuggestions.length ? addressSuggestions.map((suggestion, index) => (
                      <button
                        key={`${suggestion.name || suggestion.city}-${index}`}
                        type="button"
                        role="option"
                        aria-selected="false"
                        onClick={() => { setLocation(suggestion.name || suggestion.city || ''); setShowAddressSuggestions(false); setAddressSuggestions([]); }}
                        className="flex w-full items-start gap-2.5 border-b border-gray-100 px-3 py-2.5 text-left last:border-0 hover:bg-purple-50"
                      >
                        <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-purple-600" />
                        <span className="text-xs font-medium text-gray-700">{suggestion.name || suggestion.city}</span>
                      </button>
                    )) : (
                      <p className="px-3 py-3 text-xs text-gray-500">No matching places. You can enter the address manually.</p>
                    )}
                  </div>
                )}
              </div>

              <label className="block text-xs font-semibold text-gray-700">Special requirements
                <textarea rows="2" value={specialRequirements} onChange={(event) => setSpecialRequirements(event.target.value)} className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-xs font-normal focus:ring-2 focus:ring-purple-500 outline-none" placeholder="Anything the RentCoPartner should know before meeting?" />
              </label>
              <label className="block text-xs font-semibold text-gray-700">Note to the RentCoPartner
                <textarea rows="2" value={customerNote} onChange={(event) => setCustomerNote(event.target.value)} className="mt-1 w-full rounded-xl border border-gray-200 px-3 py-2 text-xs font-normal focus:ring-2 focus:ring-purple-500 outline-none" placeholder="Optional note" />
              </label>
            </div>

            <aside className="h-fit rounded-xl border border-purple-100 bg-purple-50/30 p-4 space-y-3">
              <h3 className="font-bold text-xs text-gray-900">Booking total</h3>
              <div className="space-y-2 text-xs text-gray-600">
                <p className="flex justify-between"><span>Duration</span> <span className="font-medium text-gray-800">{durationHoursSelected} {durationHoursSelected === 1 ? 'hour' : 'hours'} ({durationMinutes} min)</span></p>
                <p className="flex justify-between"><span>Service price</span> <span className="font-medium text-gray-800">{formatPrice(price)}</span></p>
                <p className="flex justify-between"><span>Platform fee</span> <span className="font-medium text-gray-800">{formatPrice(platformFee)}</span></p>
                <div className="border-t border-purple-100 pt-2 flex justify-between text-sm font-bold text-gray-900">
                  <span>Total</span>
                  <span className="text-purple-700">{formatPrice(totalAmount)}</span>
                </div>
                <p className="text-[10px] text-gray-400">Payment remains pending; this form does not charge a payment method.</p>
              </div>

              {!isAuthenticated() && <p className="text-xs text-amber-700">Please <Link className="font-semibold underline" to="/?auth=login">sign in</Link> to submit a booking.</p>}
              {bookingError && <p role="alert" className="text-xs text-red-600">{bookingError}</p>}
              {createdBooking && <div role="status" className="rounded-xl bg-emerald-50 p-2.5 text-xs text-emerald-800">Booking request saved. Reference: <strong>{createdBooking.id}</strong><Link to="/bookings" className="mt-1 block font-semibold underline">View my bookings</Link></div>}
              
              <button type="submit" disabled={submitting || durationMinutes <= 0 || !selectedService} className="w-full rounded-xl bg-purple-600 hover:bg-purple-700 py-2.5 text-xs font-semibold text-white transition disabled:opacity-50">
                {submitting ? 'Submitting…' : 'Submit booking request'}
              </button>
            </aside>
          </form>
        )}

      </div>

      {insufficientBalance && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm" onMouseDown={(event) => { if (event.target === event.currentTarget) setInsufficientBalance(null); }}>
          <section role="alertdialog" aria-modal="true" aria-labelledby="insufficient-balance-title" className="w-full max-w-md overflow-hidden rounded-3xl bg-white shadow-2xl">
            <div className="flex items-start justify-between gap-4 border-b border-violet-100 p-5">
              <div className="flex items-center gap-3">
                <span className="grid h-11 w-11 place-items-center rounded-2xl bg-rose-50 text-rose-600"><Wallet className="h-5 w-5" /></span>
                <div>
                  <h2 id="insufficient-balance-title" className="text-lg font-bold text-slate-900">Insufficient wallet balance</h2>
                  <p className="mt-1 text-xs text-slate-500">Add funds to your wallet to complete this booking.</p>
                </div>
              </div>
              <button type="button" aria-label="Close" onClick={() => setInsufficientBalance(null)} className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"><X className="h-4 w-4" /></button>
            </div>
            <div className="space-y-3 p-5">
              <div className="flex justify-between text-sm"><span className="text-slate-500">Booking amount</span><strong className="text-slate-900">{formatPrice(Number(insufficientBalance.booking_amount) || totalAmount)}</strong></div>
              <div className="flex justify-between text-sm"><span className="text-slate-500">Available balance</span><strong className="text-slate-900">{formatPrice(Number(insufficientBalance.available_balance) || 0)}</strong></div>
              <div className="flex justify-between rounded-xl bg-rose-50 px-3 py-2.5 text-sm"><span className="font-semibold text-rose-700">Amount to add</span><strong className="text-rose-700">{formatPrice(Number(insufficientBalance.amount_needed) || Math.max(totalAmount - Number(insufficientBalance.available_balance || 0), 0))}</strong></div>
              <div className="flex gap-2 pt-2">
                <button type="button" onClick={() => setInsufficientBalance(null)} className="flex-1 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50">Close</button>
                <Link to="/wallet" onClick={() => setInsufficientBalance(null)} className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-500 px-4 py-2.5 text-sm font-semibold text-white hover:from-violet-700 hover:to-fuchsia-600"><Wallet className="h-4 w-4" /> Add funds</Link>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
