import { Camera, ChevronDown, MapPin, Plus, Save, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FeaturePage from '../components/FeaturePage';
import { getMyProfile, getStoredUser, isAuthenticated, updateMyProfile, uploadProfilePhoto } from '../auth/auth';
import { fetchPeople, getCurrentLocation, reverseGeocode } from './finderApi';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function formatHour(h) {
  const period = h < 12 ? 'AM' : 'PM';
  const hour12 = h % 12 === 0 ? 12 : h % 12;
  return `${hour12}:00 ${period}`;
}
const HOURS = Array.from({ length: 24 }, (_, h) => formatHour(h));

const SUGGESTED_LANGUAGES = ['English', 'Hindi', 'Marathi', 'Tamil', 'Telugu', 'Bengali', 'Gujarati', 'Kannada', 'Punjabi', 'Urdu'];
const SUGGESTED_CITIES = ['Ahmedabad', 'Bengaluru', 'Bhopal', 'Chandigarh', 'Chennai', 'Delhi', 'Goa', 'Hyderabad', 'Indore', 'Jaipur', 'Kanpur', 'Kochi', 'Kolkata', 'Lucknow', 'Mumbai', 'Nagpur', 'Noida', 'Prayagraj', 'Pune', 'Surat', 'Varanasi'];

const SUGGESTED_SERVICES = [
  'Coffee Partner',
  'Café & Food Partner',
  'Event Partner',
  'Travel Partner',
  'Movie Partner',
  'Shopping Buddy',
  'Gym Partner',
  'Music Jam',
  'In-Person Meeting',
  'Elder Care',
  'Hangingout',
  'Clubbing',
  'Medical Support',
  'Domestic Help',
  'City Tour Partner',
  'Gaming Partner (Physical)',
  'Concert Partner',
  'Professional Networking Partner',
];
const MAX_GALLERY_IMAGES = 6;

const defaultProfile = {
  id: '',
  fullName: '',
  email: '',
  phone: '',
  city: '',
  lat: null,
  lng: null,
  gender: 'Other',
  bio: '',
  image: '',
  isAvailable: true,
  languages: [],
  availableDays: [],
  timeSlots: [],
  services: [],
  gallery: [],
};

function parseList(value) {
  if (Array.isArray(value)) return value;
  if (typeof value !== 'string' || !value.trim()) return [];
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) return parsed;
  } catch {
    // Older records may store comma-separated values.
  }
  return value.split(',').map((item) => item.trim()).filter(Boolean);
}

function mapApiProfile(data, user = {}) {
  let availability = {};
  try {
    availability = data.availableTime ? JSON.parse(data.availableTime) : {};
  } catch {
    availability = {};
  }
  const services = parseList(data.services).map((service, index) => (
    typeof service === 'string'
      ? { id: `service-${index}`, name: service, price: Number(data.price) || 0 }
      : { id: service.id || `service-${index}`, name: service.name || '', price: Number(service.price) || 0 }
  ));
  const gender = String(data.gender || user.gender || 'Other').toLowerCase();

  return {
    ...defaultProfile,
    id: data.id || user.id || '',
    fullName: data.fullName || user.fullName || user.name || '',
    email: data.email || user.email || '',
    phone: data.phone || user.mobile || '',
    city: data.city || user.city || '',
    lat: data.lat != null && Number.isFinite(Number(data.lat)) ? Number(data.lat) : null,
    lng: data.lng != null && Number.isFinite(Number(data.lng)) ? Number(data.lng) : null,
    gender: gender === 'male' ? 'Male' : gender === 'female' ? 'Female' : 'Other',
    price: Number(data.price) || 0,
    bio: data.bio || '',
    image: data.image || data.profile_image || data.avatar_url || data.photo || '',
    isAvailable: data.isAvailable ?? true,
    languages: parseList(data.languages),
    availableDays: availability.days || [],
    timeSlots: (availability.timeSlots || []).map((slot, index) => ({ ...slot, id: slot.id || `slot-${index}` })),
    services,
    gallery: parseList(data.gallery),
  };
}

function uid(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

// ---- Small reusable pieces ---------------------------------------------

function CollapsibleSection({ title, subtitle, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl border border-[#e4dff0]">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <div>
          <p className="text-sm font-semibold text-[#40394f]">{title}</p>
          {subtitle && <p className="mt-0.5 text-xs text-[#706a80]">{subtitle}</p>}
        </div>
        <ChevronDown className={`h-4 w-4 text-[#706a80] transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="border-t border-[#e4dff0] px-4 py-4">{children}</div>}
    </div>
  );
}

function Field({ label, name, type = 'text', value, onChange, placeholder }) {
  return (
    <label className="block text-sm font-semibold text-[#40394f]">
      {label}
      <input
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"
      />
    </label>
  );
}

function Chip({ children, onRemove }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700 ring-1 ring-violet-200">
      {children}
      <button type="button" onClick={onRemove} aria-label="Remove" className="text-violet-400 hover:text-violet-700">
        <X className="h-3 w-3" />
      </button>
    </span>
  );
}

// ---- Main component ------------------------------------------------------

export default function MyProfilePage() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const user = getStoredUser() || {};
  const role = String(user.want_to || user.wantTo || user.accountIntent || '').trim().toLowerCase();
  const isFinderRole = role === 'find' || role.includes('find a rentpeople');
  const [profile, setProfile] = useState(defaultProfile);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [uploadingGallery, setUploadingGallery] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [languageDraft, setLanguageDraft] = useState('');
  const [serviceDraft, setServiceDraft] = useState({ name: '', price: '' });
  const [cityOptions, setCityOptions] = useState(SUGGESTED_CITIES);
  const [customCityMode, setCustomCityMode] = useState(false);
  const [locating, setLocating] = useState(false);

  useEffect(() => {
    let active = true;
    fetchPeople()
      .then((people) => {
        if (!active) return;
        const directoryCities = people.map((person) => person.location || person.city).filter(Boolean);
        setCityOptions([...new Set([...SUGGESTED_CITIES, ...directoryCities])].sort((a, b) => a.localeCompare(b)));
      })
      .catch(() => {});
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!cameraOpen) return undefined;
    let active = true;
    let stream;
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError('Camera access is not available in this browser. You can upload a photo instead.');
      return () => {};
    }
    setCameraError('');
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
      .then((cameraStream) => {
        if (!active) {
          cameraStream.getTracks().forEach((track) => track.stop());
          return;
        }
        stream = cameraStream;
        if (videoRef.current) videoRef.current.srcObject = cameraStream;
      })
      .catch(() => { if (active) setCameraError('Could not open your camera. Check camera permission or upload a photo instead.'); });
    return () => {
      active = false;
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, [cameraOpen]);

  // The profile endpoint identifies the account from the saved bearer token.
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login', { replace: true });
      return;
    }
    let active = true;
    getMyProfile()
      .then((data) => {
        if (active) setProfile(mapApiProfile(data || {}, getStoredUser() || {}));
      })
      .catch((error) => {
        if (active) setErrorMsg(error.message || 'Unable to load your profile.');
      })
      .finally(() => {
        if (active) setLoadingProfile(false);
      });
    return () => { active = false; };
  }, [navigate]);

  const updateField = (event) => setProfile({ ...profile, [event.target.name]: event.target.value });

  const useCurrentLocation = async () => {
    setLocating(true);
    setErrorMsg('');
    try {
      const coordinates = await getCurrentLocation();
      let city = profile.city;
      try {
        const place = await reverseGeocode(coordinates);
        city = place.city || city;
      } catch {
        // Coordinates can still be saved when the optional reverse lookup is unavailable.
      }
      setProfile((current) => ({ ...current, ...coordinates, city }));
      if (city) setCustomCityMode(true);
    } catch (error) {
      setErrorMsg(error.message || 'Unable to get your location.');
    } finally {
      setLocating(false);
    }
  };

  const uploadImage = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    event.target.value = '';
    setUploadingAvatar(true);
    setErrorMsg('');
    try {
      const result = await uploadProfilePhoto(file, 'avatar');
      const image = result.image || (await getMyProfile())?.image;
      if (!image) throw new Error('The avatar was uploaded, but the API did not return its image URL.');
      setProfile((current) => ({ ...current, image }));
    } catch (error) {
      setErrorMsg(error.message || 'Unable to upload your profile image.');
    } finally {
      setUploadingAvatar(false);
    }
  };

  const capturePhoto = () => {
    const video = videoRef.current;
    if (!video?.videoWidth || !video?.videoHeight) {
      setCameraError('The camera is not ready yet.');
      return;
    }
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height);
    setCameraOpen(false);
    canvas.toBlob(async (fileBlob) => {
      if (!fileBlob) {
        setErrorMsg('Could not prepare the captured photo for upload.');
        return;
      }
      setUploadingAvatar(true);
      setErrorMsg('');
      try {
        const result = await uploadProfilePhoto(new File([fileBlob], 'avatar.jpg', { type: 'image/jpeg' }), 'avatar');
        const image = result.image || (await getMyProfile())?.image;
        if (!image) throw new Error('The avatar was uploaded, but the API did not return its image URL.');
        setProfile((current) => ({ ...current, image }));
      } catch (error) {
        setErrorMsg(error.message || 'Unable to upload your profile image.');
      } finally {
        setUploadingAvatar(false);
      }
    }, 'image/jpeg', 0.9);
  };

  const uploadGalleryImages = async (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;
    event.target.value = '';
    const room = MAX_GALLERY_IMAGES - profile.gallery.length;
    if (room <= 0) return;
    setUploadingGallery(true);
    setErrorMsg('');
    try {
      let uploadedGallery = profile.gallery;
      for (const file of files.slice(0, room)) {
        const result = await uploadProfilePhoto(file, 'gallery');
        if (Array.isArray(result.gallery)) {
          uploadedGallery = result.gallery;
        } else if (result.url) {
          uploadedGallery = [...uploadedGallery, result.url];
        } else {
          throw new Error('The photo uploaded, but the API did not return its URL.');
        }
      }
      setProfile((current) => ({ ...current, gallery: uploadedGallery }));
    } catch (error) {
      setErrorMsg(error.message || 'Unable to upload gallery photos.');
    } finally {
      setUploadingGallery(false);
    }
  };

  const removeGalleryImage = (index) => {
    setProfile({ ...profile, gallery: profile.gallery.filter((_, i) => i !== index) });
  };

  // Languages ------------------------------------------------------------
  const addLanguage = (lang) => {
    const value = lang.trim();
    if (!value || profile.languages.includes(value)) return;
    setProfile({ ...profile, languages: [...profile.languages, value] });
    setLanguageDraft('');
  };
  const removeLanguage = (lang) => setProfile({ ...profile, languages: profile.languages.filter((l) => l !== lang) });

  // Availability -----------------------------------------------------------
  const toggleDay = (day) => {
    const availableDays = profile.availableDays.includes(day)
      ? profile.availableDays.filter((d) => d !== day)
      : [...profile.availableDays, day];
    setProfile({ ...profile, availableDays });
  };
  const addTimeSlot = () => {
    setProfile({
      ...profile,
      timeSlots: [...profile.timeSlots, { id: uid('slot'), start: '9:00 AM', end: '10:00 AM' }],
    });
  };
  const updateTimeSlot = (id, field, value) => {
    setProfile({
      ...profile,
      timeSlots: profile.timeSlots.map((slot) => (slot.id === id ? { ...slot, [field]: value } : slot)),
    });
  };
  const removeTimeSlot = (id) => setProfile({ ...profile, timeSlots: profile.timeSlots.filter((slot) => slot.id !== id) });

  // Services / interests with pricing --------------------------------------
  const addService = (name, price) => {
    const trimmed = name.trim();
    if (!trimmed) return;
    if (profile.services.some((s) => s.name.toLowerCase() === trimmed.toLowerCase())) return;
    setProfile({
      ...profile,
      services: [...profile.services, { id: uid('svc'), name: trimmed, price: Number(price) || 0 }],
    });
    setServiceDraft({ name: '', price: '' });
  };
  const updateServicePrice = (id, price) => {
    setProfile({
      ...profile,
      services: profile.services.map((s) => (s.id === id ? { ...s, price: Number(price) || 0 } : s)),
    });
  };
  const removeService = (id) => setProfile({ ...profile, services: profile.services.filter((s) => s.id !== id) });

  // Save --------------------------------------------------------------------
  const saveProfile = async () => {
    setSaving(true);
    setErrorMsg('');
    try {
      await updateMyProfile({
        fullName: profile.fullName,
        phone: profile.phone,
        city: profile.city,
        lat: profile.lat,
        lng: profile.lng,
        gender: profile.gender,
        price: profile.price,
        bio: profile.bio,
        image: profile.image,
        isAvailable: profile.isAvailable,
        availableTime: JSON.stringify({ days: profile.availableDays, timeSlots: profile.timeSlots }),
        languages: JSON.stringify(profile.languages),
        interests: JSON.stringify(profile.services.map((service) => service.name)),
        services: profile.services,
        gallery: profile.gallery,
      });
      setSaved(true);
      window.setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setErrorMsg(err.message || 'Unable to save your profile.');
    } finally {
      setSaving(false);
    }
  };

  const completionItems = [profile.fullName, profile.city, profile.bio, profile.image, profile.languages.length > 0];
  if (!isFinderRole) completionItems.push(profile.services.length > 0, profile.availableDays.length > 0 || profile.timeSlots.length > 0);
  const completion = Math.round((completionItems.filter(Boolean).length / completionItems.length) * 100);
  const availableCityOptions = [...new Set([...cityOptions, profile.city].filter(Boolean))].sort((a, b) => a.localeCompare(b));

  return (
    <FeaturePage title="My profile" subtitle="Keep your details, profile image, and pricing up to date.">
      <section className="mb-6 max-w-5xl rounded-2xl border border-violet-100 bg-white p-5 shadow-sm" aria-label="Profile completion">
        <div className="flex items-center justify-between gap-3"><div><h2 className="font-bold text-[#171426]">Profile completion</h2><p className="mt-1 text-sm text-[#706a80]">A complete profile helps people get to know you.</p></div><span className="text-lg font-bold text-violet-700">{loadingProfile ? '…' : `${completion}%`}</span></div>
        <div className="mt-4 h-3 overflow-hidden rounded-full bg-violet-100" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={completion}><div className="h-full rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-500 transition-all" style={{ width: `${completion}%` }} /></div>
      </section>
      {loadingProfile ? <p className="text-sm text-[#706a80]">Loading your profile…</p> : errorMsg && !profile.id ? <p role="alert" className="text-sm text-red-600">{errorMsg}</p> : (
      <div className="grid max-w-5xl gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="h-fit rounded-2xl border border-[#e7e1f2] bg-white p-5 text-center shadow-sm">
          {errorMsg && <p role="alert" className="mb-3 text-xs text-red-600">{errorMsg}</p>}
          {profile.image ? <img src={profile.image} alt="Your profile" className="mx-auto h-36 w-36 rounded-full object-cover ring-4 ring-violet-100" /> : <div className="mx-auto grid h-36 w-36 place-items-center rounded-full bg-violet-100 text-3xl font-bold text-violet-500">{profile.fullName?.charAt(0)?.toUpperCase() || '?'}</div>}
          <label className="mt-5 inline-flex cursor-pointer items-center gap-2 rounded-lg border border-violet-200 px-4 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-50">
            <Camera className="h-4 w-4" />
            {uploadingAvatar ? 'Uploading…' : 'Upload image'}
            <input type="file" accept="image/*" onChange={uploadImage} className="hidden" />
          </label>
          <button type="button" onClick={() => { setCameraError(''); setCameraOpen(true); }} className="mt-2 inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700"><Camera className="h-4 w-4" />Open camera</button>
          {cameraOpen && <div className="mt-4 space-y-2">
            <video ref={videoRef} autoPlay playsInline muted className="aspect-video w-full rounded-lg bg-black object-cover" />
            {cameraError && <p role="alert" className="text-xs text-red-600">{cameraError}</p>}
            <div className="flex justify-center gap-2"><button type="button" onClick={capturePhoto} className="rounded-lg bg-fuchsia-600 px-3 py-2 text-xs font-semibold text-white">Take picture</button><button type="button" onClick={() => setCameraOpen(false)} className="rounded-lg border px-3 py-2 text-xs font-semibold">Close</button></div>
          </div>}
          {cameraError && !cameraOpen && <p role="alert" className="mt-2 text-xs text-red-600">{cameraError}</p>}
          <p className="mt-3 text-xs text-[#706a80]">Use a clear profile image.</p>

          {!isFinderRole && <label className="mt-5 flex items-center justify-between rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-semibold text-[#40394f]">
            Available
            <button
              type="button"
              role="switch"
              aria-checked={profile.isAvailable}
              onClick={() => setProfile({ ...profile, isAvailable: !profile.isAvailable })}
              className={`relative h-6 w-11 shrink-0 rounded-full transition ${profile.isAvailable ? 'bg-violet-600' : 'bg-gray-300'}`}
            >
              <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${profile.isAvailable ? 'translate-x-5' : 'translate-x-0.5'}`} />
            </button>
          </label>}
        </aside>

        <div className="space-y-5 rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm">
          {/* Personal info (collapsible) */}
          <CollapsibleSection title="Personal info" subtitle="Your name and contact details.">
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Full name" name="fullName" value={profile.fullName} onChange={updateField} />
              <Field label="Email" name="email" type="email" value={profile.email} onChange={updateField} />
              <Field label="Phone number" name="phone" type="tel" value={profile.phone} onChange={updateField} />
              <label className="block text-sm font-semibold text-[#40394f]">
                City / location
                <select
                  value={customCityMode ? 'Other' : profile.city}
                  onChange={(event) => {
                    const value = event.target.value;
                    setCustomCityMode(value === 'Other');
                    setProfile((current) => ({ ...current, city: value === 'Other' ? '' : value }));
                  }}
                  className="mt-2 w-full rounded-lg border border-[#e4dff0] bg-white px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"
                >
                  <option value="">Select your city</option>
                  {availableCityOptions.map((city) => <option key={city} value={city}>{city}</option>)}
                  <option value="Other">Other / add a city</option>
                </select>
                {customCityMode && <input name="city" value={profile.city} onChange={updateField} placeholder="Enter your city or area" className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300" />}
                <span className="mt-1 block text-xs font-normal text-[#827b95]">Suggestions include cities where RentCoPartner are available.</span>
                <div className="mt-3">
                  <button type="button" onClick={useCurrentLocation} disabled={locating} className="inline-flex items-center gap-2 rounded-lg border border-violet-200 px-3 py-2 text-xs font-semibold text-violet-700 hover:bg-violet-50 disabled:opacity-60"><MapPin className="h-3.5 w-3.5" />{locating ? 'Finding location…' : profile.lat != null && profile.lng != null ? 'Update current location' : 'Use my current location'}</button>
                  {profile.lat != null && profile.lng != null && <span className="ml-2 text-xs font-normal text-[#827b95]">Coordinates ready to save</span>}
                  <span className="mt-1 block text-xs font-normal text-[#827b95]">Your location helps Find a RentCoPartner users discover nearby providers. Browser permission is required.</span>
                </div>
              </label>
              <label className="block text-sm font-semibold text-[#40394f]">
                Gender
                <select
                  name="gender"
                  value={profile.gender}
                  onChange={updateField}
                  className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"
                >
                  <option>Male</option>
                  <option>Female</option>
                  <option>Other</option>
                </select>
              </label>
            </div>
          </CollapsibleSection>

          {/* Languages */}
          <CollapsibleSection title="Languages" subtitle="Pick from the list or add your own.">
            <div className="flex flex-wrap gap-2">
              {profile.languages.map((lang) => (
                <Chip key={lang} onRemove={() => removeLanguage(lang)}>{lang}</Chip>
              ))}
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <select
                value=""
                onChange={(e) => addLanguage(e.target.value)}
                className="rounded-lg border border-[#e4dff0] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-300"
              >
                <option value="" disabled>Add a language…</option>
                {SUGGESTED_LANGUAGES.filter((l) => !profile.languages.includes(l)).map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
              <input
                value={languageDraft}
                onChange={(e) => setLanguageDraft(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addLanguage(languageDraft))}
                placeholder="Or type another language"
                className="rounded-lg border border-[#e4dff0] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-300"
              />
              <button
                type="button"
                onClick={() => addLanguage(languageDraft)}
                className="inline-flex items-center gap-1 rounded-lg border border-violet-200 px-3 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-50"
              >
                <Plus className="h-3.5 w-3.5" />Add
              </button>
            </div>
          </CollapsibleSection>

          {/* Availability: days + hourly time slots */}
          {!isFinderRole && <CollapsibleSection title="Available time" subtitle="Choose your days, then add one or more hourly time slots.">
            <p className="text-xs font-semibold text-[#706a80]">Days available</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {DAYS.map((day) => {
                const selected = profile.availableDays.includes(day);
                return (
                  <button
                    key={day}
                    type="button"
                    onClick={() => toggleDay(day)}
                    className={`rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${
                      selected ? 'border-violet-500 bg-violet-50 text-violet-700 ring-1 ring-violet-300' : 'border-[#e4dff0] text-[#706a80] hover:border-violet-300'
                    }`}
                  >
                    {day}
                  </button>
                );
              })}
            </div>

            <p className="mt-4 text-xs font-semibold text-[#706a80]">Time slots</p>
            <div className="mt-2 space-y-2">
              {profile.timeSlots.map((slot) => (
                <div key={slot.id} className="flex flex-wrap items-center gap-2">
                  <select
                    value={slot.start}
                    onChange={(e) => updateTimeSlot(slot.id, 'start', e.target.value)}
                    className="rounded-lg border border-[#e4dff0] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-300"
                  >
                    {HOURS.map((h) => <option key={h} value={h}>{h}</option>)}
                  </select>
                  <span className="text-xs text-[#706a80]">to</span>
                  <select
                    value={slot.end}
                    onChange={(e) => updateTimeSlot(slot.id, 'end', e.target.value)}
                    className="rounded-lg border border-[#e4dff0] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-300"
                  >
                    {HOURS.map((h) => <option key={h} value={h}>{h}</option>)}
                  </select>
                  <button
                    type="button"
                    onClick={() => removeTimeSlot(slot.id)}
                    aria-label="Remove time slot"
                    className="text-[#706a80] hover:text-red-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={addTimeSlot}
                className="inline-flex items-center gap-1 rounded-lg border border-violet-200 px-3 py-1.5 text-xs font-semibold text-violet-700 hover:bg-violet-50"
              >
                <Plus className="h-3.5 w-3.5" />Add another time slot
              </button>
            </div>
          </CollapsibleSection>}

          {/* Interests / services with per-item pricing */}
          {!isFinderRole && <CollapsibleSection title="Interests & services" subtitle="Add what you offer and set your own price for each.">
            <div className="flex flex-wrap items-end gap-2">
              <label className="text-sm font-semibold text-[#40394f]">
                Choose from list
                <select
                  value=""
                  onChange={(e) => addService(e.target.value, 0)}
                  className="mt-2 block rounded-lg border border-[#e4dff0] px-3 py-2 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"
                >
                  <option value="" disabled>Add a service…</option>
                  {SUGGESTED_SERVICES.filter((s) => !profile.services.some((x) => x.name === s)).map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </label>
              <label className="text-sm font-semibold text-[#40394f]">
                Or add your own
                <input
                  value={serviceDraft.name}
                  onChange={(e) => setServiceDraft({ ...serviceDraft, name: e.target.value })}
                  placeholder="e.g. City tour guide"
                  className="mt-2 block rounded-lg border border-[#e4dff0] px-3 py-2 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"
                />
              </label>
              <label className="text-sm font-semibold text-[#40394f]">
                Price (₹/hr)
                <input
                  type="number"
                  min="0"
                  value={serviceDraft.price}
                  onChange={(e) => setServiceDraft({ ...serviceDraft, price: e.target.value })}
                  placeholder="0"
                  className="mt-2 block w-28 rounded-lg border border-[#e4dff0] px-3 py-2 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"
                />
              </label>
              <button
                type="button"
                onClick={() => addService(serviceDraft.name, serviceDraft.price)}
                className="inline-flex items-center gap-1 rounded-lg border border-violet-200 px-3 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-50"
              >
                <Plus className="h-3.5 w-3.5" />Add
              </button>
            </div>

            <div className="mt-4 space-y-2">
              {profile.services.length === 0 && <p className="text-xs text-[#706a80]">No services added yet.</p>}
              {profile.services.map((service) => (
                <div key={service.id} className="flex items-center justify-between gap-3 rounded-xl border border-[#e4dff0] px-4 py-2.5">
                  <span className="text-sm font-semibold text-[#40394f]">{service.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[#706a80]">₹</span>
                    <input
                      type="number"
                      min="0"
                      value={service.price}
                      onChange={(e) => updateServicePrice(service.id, e.target.value)}
                      className="w-24 rounded-lg border border-[#e4dff0] px-2 py-1.5 text-sm outline-none focus:ring-2 focus:ring-violet-300"
                    />
                    <span className="text-xs text-[#706a80]">/hr</span>
                    <button type="button" onClick={() => removeService(service.id)} aria-label={`Remove ${service.name}`} className="text-[#706a80] hover:text-red-600">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </CollapsibleSection>}

          {/* Photos */}
          <CollapsibleSection title="Photos" subtitle={`Add a few more photos so people get a feel for you. Up to ${MAX_GALLERY_IMAGES}.`}>
            <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
              {profile.gallery.map((src, index) => (
                <div key={index} className="group relative aspect-square overflow-hidden rounded-lg border border-[#e4dff0]">
                  <img src={src} alt={`Photo ${index + 1}`} className="h-full w-full object-cover" />
                  <button
                    type="button"
                    onClick={() => removeGalleryImage(index)}
                    className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-xs font-bold text-white opacity-0 transition group-hover:opacity-100"
                    aria-label={`Remove photo ${index + 1}`}
                  >
                    ×
                  </button>
                </div>
              ))}
              {profile.gallery.length < MAX_GALLERY_IMAGES && (
                <label className="flex aspect-square cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-[#e4dff0] text-[#706a80] hover:border-violet-300 hover:text-violet-600">
                  <Camera className="h-5 w-5" />
                  <span className="text-xs font-medium">{uploadingGallery ? 'Uploading…' : 'Add photos'}</span>
                  <input type="file" accept="image/*" multiple onChange={uploadGalleryImages} className="hidden" />
                </label>
              )}
            </div>
          </CollapsibleSection>

          {/* Bio */}
          <label className="block text-sm font-semibold text-[#40394f]">
            About you
            <textarea
              name="bio"
              value={profile.bio}
              onChange={updateField}
              rows="4"
              className="mt-2 w-full resize-none rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"
            />
          </label>

          <div className="flex items-center gap-4">
            <button
              onClick={saveProfile}
              disabled={saving}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
            >
              <Save className="h-4 w-4" />
              {saving ? 'Saving…' : 'Save profile'}
            </button>
            {saved && <span className="text-sm font-medium text-emerald-600">Profile saved successfully.</span>}
            {errorMsg && <span className="text-sm font-medium text-amber-600">{errorMsg}</span>}
          </div>
        </div>
      </div>
      )}
    </FeaturePage>
  );
}
