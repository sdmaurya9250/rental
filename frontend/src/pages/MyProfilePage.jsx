import { Camera, Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import FeaturePage from '../components/FeaturePage';

const SERVICE_CATEGORIES = [
  { id: 'coffee', label: 'Coffee Partner', price: 1500, hours: 1 },
  { id: 'cafe-food', label: 'Café & Food Partner', price: 2250, hours: 2 },
  { id: 'event', label: 'Event Partner', price: 3750, hours: 3 },
  { id: 'travel', label: 'Travel Buddy', price: 5000, hours: 4 },
];

const defaultProfile = {
  fullName: 'Surendra Kumar', email: 'surendra@example.com', phone: '+91 98765 43210',
  city: 'Mumbai', gender: 'Man', price: '1500', bio: 'I enjoy meeting people and creating memorable experiences.',
  image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=400&auto=format&fit=crop',
  isAvailable: true, availableTime: 'Mon-Fri, 6 PM - 10 PM',
  languages: 'English, Hindi', interests: 'Coffee, Travel, Music',
  services: ['coffee'], gallery: [],
};

const MAX_GALLERY_IMAGES = 6;

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export default function MyProfilePage() {
  const [profile, setProfile] = useState(defaultProfile);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const storedProfile = localStorage.getItem('rentpeople-profile');
    if (storedProfile) setProfile({ ...defaultProfile, ...JSON.parse(storedProfile) });
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
  const toggleService = (id) => {
    const services = profile.services.includes(id)
      ? profile.services.filter((serviceId) => serviceId !== id)
      : [...profile.services, id];
    setProfile({ ...profile, services });
  };
  const saveProfile = () => {
    localStorage.setItem('rentpeople-profile', JSON.stringify(profile));
    setSaved(true);
    window.setTimeout(() => setSaved(false), 3000);
  };

  return <FeaturePage title="My profile" subtitle="Keep your details, profile image, and pricing up to date.">
    <div className="grid max-w-5xl gap-6 lg:grid-cols-[260px_1fr]">
      <aside className="h-fit rounded-2xl border border-[#e7e1f2] bg-white p-5 text-center shadow-sm">
        <img src={profile.image} alt="Your profile" className="mx-auto h-36 w-36 rounded-full object-cover ring-4 ring-violet-100" />
        <label className="mt-5 inline-flex cursor-pointer items-center gap-2 rounded-lg border border-violet-200 px-4 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-50"><Camera className="h-4 w-4" />Upload image<input type="file" accept="image/*" onChange={uploadImage} className="hidden" /></label>
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

      <div className="rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm">
        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="Full name" name="fullName" value={profile.fullName} onChange={updateField} />
          <Field label="Email" name="email" type="email" value={profile.email} onChange={updateField} />
          <Field label="Phone number" name="phone" type="tel" value={profile.phone} onChange={updateField} />
          <Field label="City" name="city" value={profile.city} onChange={updateField} />
          <label className="block text-sm font-semibold text-[#40394f]">Gender<select name="gender" value={profile.gender} onChange={updateField} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"><option>Woman</option><option>Man</option><option>Non-binary</option><option>Prefer not to say</option></select></label>
          <Field label="Available time" name="availableTime" value={profile.availableTime} onChange={updateField} placeholder="e.g. Mon-Fri, 6 PM - 10 PM" />
          <Field label="Languages" name="languages" value={profile.languages} onChange={updateField} placeholder="e.g. English, Hindi" />
          <Field label="Interests" name="interests" value={profile.interests} onChange={updateField} placeholder="e.g. Coffee, Travel, Music" />
        </div>

        <label className="mt-5 block text-sm font-semibold text-[#40394f]">About you<textarea name="bio" value={profile.bio} onChange={updateField} rows="4" className="mt-2 w-full resize-none rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300" /></label>
        <div className="mt-5">
          <p className="text-sm font-semibold text-[#40394f]">Photos</p>
          <p className="mt-1 text-xs text-[#706a80]">Add a few more photos so people get a feel for you. Up to {MAX_GALLERY_IMAGES}.</p>
          <div className="mt-3 grid grid-cols-3 gap-3 sm:grid-cols-4">
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
        </div>

        <div className="mt-6">
          <p className="text-sm font-semibold text-[#40394f]">Services & pricing</p>
          <p className="mt-1 text-xs text-[#706a80]">Select the service categories you offer.</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {SERVICE_CATEGORIES.map((service) => {
              const selected = profile.services.includes(service.id);
              return (
                <button
                  key={service.id}
                  type="button"
                  onClick={() => toggleService(service.id)}
                  className={`flex items-center justify-between rounded-xl border px-4 py-3 text-left text-sm transition ${
                    selected ? 'border-violet-500 bg-violet-50 ring-1 ring-violet-300' : 'border-[#e4dff0] bg-white hover:border-violet-300'
                  }`}
                >
                  <span className="font-semibold text-[#40394f]">{service.label}</span>
                  <span className="text-xs font-medium text-[#706a80]">₹{service.price.toLocaleString('en-IN')} · {service.hours} hr{service.hours > 1 ? 's' : ''}</span>
                </button>
              );
            })}
          </div>
          <label className="mt-4 block text-sm font-semibold text-[#40394f]">Base hourly pricing (₹)<input name="price" type="number" min="0" value={profile.price} onChange={updateField} className="mt-2 w-full max-w-xs rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300" /></label>
        </div>

        <div className="mt-6 flex items-center gap-4"><button onClick={saveProfile} className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-5 py-3 text-sm font-semibold text-white"><Save className="h-4 w-4" />Save profile</button>{saved && <span className="text-sm font-medium text-emerald-600">Profile saved successfully.</span>}</div>
      </div>
    </div>
  </FeaturePage>;
}

function Field({ label, name, type = 'text', value, onChange, placeholder }) {
  return <label className="block text-sm font-semibold text-[#40394f]">{label}<input name={name} type={type} value={value} onChange={onChange} placeholder={placeholder} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300" /></label>;
}