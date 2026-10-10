import { useEffect, useState } from 'react';
import { Heart } from 'lucide-react';
import FeaturePage from '../components/FeaturePage';
import PersonRow from '../components/PersonRow';
import { fetchFavoritePeople, removeFavoriteRecord } from './finderApi';

export default function FavoritesPage() {
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    fetchFavoritePeople()
      .then((result) => {
        if (active) setPeople(Array.isArray(result?.people) ? result.people : Array.isArray(result?.favorites) ? result.favorites : []);
      })
      .catch((requestError) => { if (active) setError(requestError.message || 'Unable to load favorites.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  async function removeFavorite(person) {
    setRemovingId(person.id);
    setError('');
    try {
      await removeFavoriteRecord(person.id);
      setPeople((current) => current.filter((favorite) => favorite.id !== person.id));
    } catch (requestError) {
      setError(requestError.message || 'Unable to remove this favorite.');
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <FeaturePage title="My favorites" subtitle="Quick booking from your saved people.">
      <div className="w-full space-y-3">
        {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        {loading ? (
          <p className="rounded-xl border border-violet-100 bg-white p-5 text-sm text-gray-500">Loading favorites…</p>
        ) : people.length ? people.map((person) => (
          <div key={person.id} className="flex items-center gap-2">
            <div className="min-w-0 flex-1"><PersonRow person={person} action="View profile" /></div>
            <button type="button" onClick={() => removeFavorite(person)} disabled={removingId === person.id} aria-label={`Remove ${person.name || 'person'} from favorites`} className="shrink-0 rounded-lg border border-rose-200 p-2 text-rose-600 hover:bg-rose-50 disabled:opacity-50">
              {removingId === person.id ? <span className="px-1 text-xs">…</span> : <Heart className="h-4 w-4 fill-current" />}
            </button>
          </div>
        )) : !error && (
          <div className="rounded-xl border border-dashed border-violet-200 bg-white p-8 text-center">
            <Heart className="mx-auto h-8 w-8 text-violet-300" />
            <p className="mt-3 text-sm font-semibold text-gray-700">No favorites yet</p>
            <p className="mt-1 text-xs text-gray-500">Save a profile with the heart button and it will appear here.</p>
          </div>
        )}
      </div>
    </FeaturePage>
  );
}
