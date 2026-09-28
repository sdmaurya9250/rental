import { Camera, ChevronDown, Plus, Save, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import FeaturePage from '../components/FeaturePage';

// ---- Config -----------------------------------------------------------
// Point this at wherever the server in /server is running.
const API_BASE = import.meta?.env?.VITE_API_BASE || 'http://localhost:4000';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function formatHour(h) {
  const period = h < 12 ? 'AM' : 'PM';
  const hour12 = h % 12 === 0 ? 12 : h % 12;
  return `${hour12}:00 ${period}`;
}
const HOURS = Array.from({ length: 24 }, (_, h) => formatHour(h));

const SUGGESTED_LANGUAGES = ['English', 'Hindi', 'Marathi', 'Tamil', 'Telugu', 'Bengali', 'Gujarati', 'Kannada', 'Punjabi', 'Urdu'];
const SUGGESTED_SERVICES = ['Coffee Partner', 'Café & Food Partner', 'Event Partner', 'Travel Buddy', 'Movie Buddy', 'Shopping Buddy', 'Gym Partner', 'Music Jam'];

const MAX_GALLERY_IMAGES = 6;

const defaultProfile = {
  id: '',
  fullName: 'Surendra Kumar',
  email: 'surendra@example.com',
  phone: '+91 98765 43210',
  city: 'Mumbai',
  gender: 'Man',
  bio: 'I enjoy meeting people and creating memorable experiences.',
  image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=400&auto=format&fit=crop',
  isAvailable: true,
  languages: ['English', 'Hindi'],
  availableDays: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
  timeSlots: [{ id: 'slot-1', start: '6:00 PM', end: '10:00 PM' }],
  services: [{ id: 'svc-1', name: 'Coffee Partner', price: 1500 }],
  gallery: [],
};

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
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
  const [profile, setProfile] = useState(defaultProfile);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [languageDraft, setLanguageDraft] = useState('');
  const [serviceDraft, setServiceDraft] = useState({ name: '', price: '' });

  // Load an existing profile from the API (falling back to a local cache).
  useEffect(() => {
    let userId = localStorage.getItem('rentpeople-user-id');
    if (!userId) {
      userId = uid('user');
      localStorage.setItem('rentpeople-user-id', userId);
    }
    setProfile((p) => ({ ...p, id: userId }));

    fetch(`${API_BASE}/api/profile/${userId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setProfile((p) => ({ ...defaultProfile, ...data, id: userId }));
      })
      .catch(() => {
        const cached = localStorage.getItem('rentpeople-profile');
        if (cached) setProfile((p) => ({ ...defaultProfile, ...JSON.parse(cached), id: userId }));
      });
  }, []);

  const updateField = (event) => setProfile({ ...profile, [event.target.name]: event.target.value });

  const uploadImage = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setProfile({ ...profile, image: String(reader.result) });
    reader.readAsDataURL(file);
  };

  const uploadGalleryImages = async (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;
    const room = MAX_GALLERY_IMAGES - profile.gallery.length;
    const dataUrls = await Promise.all(files.slice(0, room).map(readFileAsDataUrl));
    setProfile({ ...profile, gallery: [...profile.gallery, ...dataUrls] });
    event.target.value = '';
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
      const res = await fetch(`${API_BASE}/api/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || 'Server error while saving');
      }
      const savedProfile = await res.json();
      setProfile((p) => ({ ...p, ...savedProfile }));
      localStorage.setItem('rentpeople-profile', JSON.stringify(savedProfile));
      setSaved(true);
      window.setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      // Backend unreachable or rejected the request — keep the user's work locally.
      localStorage.setItem('rentpeople-profile', JSON.stringify(profile));
      setErrorMsg(err.message === 'Failed to fetch' ? "Couldn't reach the server, so this was saved on this device only." : err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <FeaturePage title="My profile" subtitle="Keep your details, profile image, and pricing up to date.">
      <div className="grid max-w-5xl gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="h-fit rounded-2xl border border-[#e7e1f2] bg-white p-5 text-center shadow-sm">
          <img src={profile.image} alt="Your profile" className="mx-auto h-36 w-36 rounded-full object-cover ring-4 ring-violet-100" />
          <label className="mt-5 inline-flex cursor-pointer items-center gap-2 rounded-lg border border-violet-200 px-4 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-50">
            <Camera className="h-4 w-4" />
            Upload image
            <input type="file" accept="image/*" onChange={uploadImage} className="hidden" />
          </label>
          <p className="mt-3 text-xs text-[#706a80]">Use a clear profile image.</p>

          <label className="mt-5 flex items-center justify-between rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-semibold text-[#40394f]">
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
          </label>
        </aside>

        <div className="space-y-5 rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm">
          {/* Personal info (collapsible) */}
          <CollapsibleSection title="Personal info" subtitle="Your name and contact details.">
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Full name" name="fullName" value={profile.fullName} onChange={updateField} />
              <Field label="Email" name="email" type="email" value={profile.email} onChange={updateField} />
              <Field label="Phone number" name="phone" type="tel" value={profile.phone} onChange={updateField} />
              <Field label="City" name="city" value={profile.city} onChange={updateField} />
              <label className="block text-sm font-semibold text-[#40394f]">
                Gender
                <select
                  name="gender"
                  value={profile.gender}
                  onChange={updateField}
                  className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"
                >
                  <option>Woman</option>
                  <option>Man</option>
                  <option>Non-binary</option>
                  <option>Prefer not to say</option>
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
          <CollapsibleSection title="Available time" subtitle="Choose your days, then add one or more hourly time slots.">
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
          </CollapsibleSection>

          {/* Interests / services with per-item pricing */}
          <CollapsibleSection title="Interests & services" subtitle="Add what you offer and set your own price for each.">
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
          </CollapsibleSection>

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
                  <span className="text-xs font-medium">Add photos</span>
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
    </FeaturePage>
  );
}