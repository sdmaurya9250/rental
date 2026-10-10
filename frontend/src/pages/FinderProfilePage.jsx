import { useEffect, useState } from 'react';
import { ArrowLeft, Languages, MapPin, UserRound, Sparkles, Image as ImageIcon, AlertCircle } from 'lucide-react';
import { Link, Navigate, useParams } from 'react-router-dom';
import FeaturePage from '../components/FeaturePage';
import { fetchPersonById } from './finderApi';
import { getStoredUser } from '../auth/auth';

function getLanguages(value) {
  if (Array.isArray(value)) return value.map((item) => typeof item === 'string' ? item : item?.name).filter(Boolean);
  if (typeof value === 'string') return value.split(',').map((language) => language.trim()).filter(Boolean);
  return [];
}

export default function FinderProfilePage() {
  const { finderId } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const currentUser = getStoredUser() || {};
  const isCompanion = String(currentUser.want_to || currentUser.wantTo || currentUser.accountIntent || '').trim().toLowerCase() === 'companion';

  useEffect(() => {
    if (!isCompanion) return undefined;
    let active = true;
    setLoading(true);
    setError('');
    fetchPersonById(finderId)
      .then((result) => { if (active) setProfile(result); })
      .catch((requestError) => { if (active) setError(requestError.message || 'Unable to load this profile.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [finderId, isCompanion]);

  if (!isCompanion) return <Navigate to="/bookings" replace />;

  if (loading) {
    return (
      <FeaturePage title="Finder Profile" subtitle="Fetching profile details.">
        <div className="mx-auto flex max-w-4xl flex-col items-center justify-center rounded-3xl border border-purple-100 bg-white/80 p-12 text-center backdrop-blur-md shadow-sm">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-purple-600 border-t-transparent" />
          <p className="mt-4 text-sm font-medium text-slate-600">Loading finder profile...</p>
        </div>
      </FeaturePage>
    );
  }

  if (error || !profile) {
    return (
      <FeaturePage title="Profile Unavailable" subtitle={error || 'This profile could not be found.'}>
        <div className="mx-auto max-w-md rounded-2xl border border-rose-100 bg-rose-50/50 p-8 text-center shadow-sm">
          <AlertCircle className="mx-auto h-10 w-10 text-rose-500" />
          <h3 className="mt-3 text-lg font-bold text-slate-900">Unable to Display Profile</h3>
          <p className="mt-1 text-sm text-slate-600">{error || 'This profile might have been removed or is temporarily unreachable.'}</p>
          <Link to="/bookings" className="mt-5 inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md transition hover:bg-fuchsia-600">
            <ArrowLeft className="h-4 w-4" /> Back to bookings
          </Link>
        </div>
      </FeaturePage>
    );
  }

  const photos = [profile.image, ...(Array.isArray(profile.images) ? profile.images : Array.isArray(profile.gallery) ? profile.gallery : [])]
    .map((photo) => typeof photo === 'string' ? photo : photo?.url || photo?.image || '')
    .filter(Boolean)
    .filter((photo, index, allPhotos) => allPhotos.indexOf(photo) === index);

  const languages = getLanguages(profile.languages);
  const rawRole = String(profile.want_to || profile.role || '').trim().toLowerCase();
  const role = rawRole === 'companion' ? 'Become a Partner' : rawRole === 'finder' ? 'Find a Partner' : rawRole || 'Finder';

  return (
    <FeaturePage title="Finder Profile" subtitle="Profile details shared with the companion for this booking.">
      <div className="mx-auto max-w-4xl space-y-6">
        
        {/* Navigation Link */}
        <Link to="/bookings" className="group inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-fuchsia-600">
          <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" /> Back to bookings
        </Link>

        {/* Main Card */}
        <div className="overflow-hidden rounded-3xl border border-purple-100 bg-white shadow-xl shadow-purple-500/5">
          
          {/* Header Banner Section */}
          <div className="relative bg-gradient-to-r from-violet-700 via-purple-600 to-fuchsia-500 p-6 sm:p-8">
            <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-end">
              <div className="relative">
                <img
                  src={profile.image || photos[0] || 'https://i.pravatar.cc/150?img=1'}
                  alt={`${profile.name || 'Finder'} profile`}
                  className="h-28 w-28 rounded-2xl border-4 border-white/20 object-cover shadow-xl backdrop-blur-md"
                />
                <span className="absolute bottom-1 right-1 h-4 w-4 rounded-full border-2 border-white bg-emerald-500" title="Active" />
              </div>
              <div className="min-w-0 text-center sm:text-left text-white">
                <h1 className="text-2xl font-black tracking-tight sm:text-3xl">
                  {profile.name || profile.fullName || profile.full_name || 'Finder'}
                </h1>
                <p className="mt-1 flex items-center justify-center gap-1.5 text-xs font-medium text-purple-100 sm:justify-start">
                  <Sparkles className="h-3.5 w-3.5 text-amber-300" /> Verified Member
                </p>
              </div>
            </div>
          </div>

          {/* Quick Info Badges */}
          <div className="border-b border-purple-100/60 bg-purple-50/50 px-6 py-4">
            <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-slate-700">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-purple-100/80 px-3 py-1.5 font-semibold text-purple-800">
                <UserRound className="h-3.5 w-3.5" />
                {role}
              </span>
              {(profile.location || profile.city) && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-slate-700 shadow-sm border border-purple-100">
                  <MapPin className="h-3.5 w-3.5 text-purple-600" />
                  {profile.location || profile.city}
                </span>
              )}
              {profile.gender && (
                <span className="inline-flex items-center rounded-full bg-white px-3 py-1.5 text-slate-700 shadow-sm border border-purple-100 capitalize">
                  {profile.gender}
                </span>
              )}
            </div>
          </div>

          {/* Bio & Languages Grid */}
          <div className="grid gap-6 p-6 sm:p-8 md:grid-cols-3">
            <div className="md:col-span-2">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">About</h2>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-600">
                {profile.bio || 'No about information added yet.'}
              </p>
            </div>

            <div className="rounded-2xl bg-slate-50 p-5 border border-slate-100">
              <h2 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-purple-500">
                <Languages className="h-4 w-4 text-purple-600" /> Languages
              </h2>
              {languages.length ? (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {languages.map((language) => (
                    <span key={language} className="rounded-lg bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 border border-purple-100 shadow-2xs">
                      {language}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-xs text-slate-400">No languages listed.</p>
              )}
            </div>
          </div>

          {/* Photo Gallery Section */}
          {photos.length > 0 && (
            <div className="border-t border-purple-100/60 p-6 sm:p-8">
              <h2 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-purple-500">
                <ImageIcon className="h-4 w-4 text-purple-600" /> Photos
              </h2>
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                {photos.map((photo, index) => (
                  <div key={`${photo}-${index}`} className="group relative overflow-hidden rounded-2xl bg-purple-50 aspect-square">
                    <img
                      src={photo}
                      alt={`${profile.name || 'Finder'} photo ${index + 1}`}
                      loading="lazy"
                      className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </FeaturePage>
  );
}
