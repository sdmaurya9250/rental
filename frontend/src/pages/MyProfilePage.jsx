import { Camera, Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import FeaturePage from '../components/FeaturePage';

const defaultProfile = {
  fullName: 'Surendra Kumar', email: 'surendra@example.com', phone: '+91 98765 43210',
  city: 'Mumbai', gender: 'Man', price: '1500', bio: 'I enjoy meeting people and creating memorable experiences.',
  image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=400&auto=format&fit=crop',
};

export default function MyProfilePage() {
  const [profile, setProfile] = useState(defaultProfile);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const storedProfile = localStorage.getItem('rentpeople-profile');
    if (storedProfile) setProfile(JSON.parse(storedProfile));
  }, []);

  const updateField = (event) => setProfile({ ...profile, [event.target.name]: event.target.value });
  const uploadImage = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setProfile({ ...profile, image: String(reader.result) });
    reader.readAsDataURL(file);
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
      </aside>

      <div className="rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm">
        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="Full name" name="fullName" value={profile.fullName} onChange={updateField} />
          <Field label="Email" name="email" type="email" value={profile.email} onChange={updateField} />
          <Field label="Phone number" name="phone" type="tel" value={profile.phone} onChange={updateField} />
          <Field label="City" name="city" value={profile.city} onChange={updateField} />
          <label className="block text-sm font-semibold text-[#40394f]">Gender<select name="gender" value={profile.gender} onChange={updateField} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300"><option>Woman</option><option>Man</option><option>Non-binary</option><option>Prefer not to say</option></select></label>
          <label className="block text-sm font-semibold text-[#40394f]">Hourly pricing (₹)<input name="price" type="number" min="0" value={profile.price} onChange={updateField} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300" /></label>
        </div>
        <label className="mt-5 block text-sm font-semibold text-[#40394f]">About you<textarea name="bio" value={profile.bio} onChange={updateField} rows="4" className="mt-2 w-full resize-none rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300" /></label>
        <label className="mt-5 block text-sm font-semibold text-[#40394f]">Profile image URL<input name="image" type="url" value={profile.image} onChange={updateField} placeholder="https://..." className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300" /></label>
        <div className="mt-6 flex items-center gap-4"><button onClick={saveProfile} className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-5 py-3 text-sm font-semibold text-white"><Save className="h-4 w-4" />Save profile</button>{saved && <span className="text-sm font-medium text-emerald-600">Profile saved successfully.</span>}</div>
      </div>
    </div>
  </FeaturePage>;
}

function Field({ label, name, type = 'text', value, onChange }) {
  return <label className="block text-sm font-semibold text-[#40394f]">{label}<input name={name} type={type} value={value} onChange={onChange} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal outline-none focus:ring-2 focus:ring-violet-300" /></label>;
}
