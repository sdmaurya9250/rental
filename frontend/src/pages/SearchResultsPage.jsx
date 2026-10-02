import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import FeaturePage from '../components/FeaturePage';
import PersonRow from '../components/PersonRow';
import { fetchPeople } from './finderApi';

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    fetchPeople().then((results) => { if (active) setPeople(results); }).catch((requestError) => { if (active) setError(requestError.message || 'Unable to search people.'); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => { setQuery(searchParams.get('q') || ''); }, [searchParams]);

  const results = people.filter((person) => {
    const tags = Array.isArray(person.tags) ? person.tags : Array.isArray(person.interests) ? person.interests : String(person.interests || '').split(',');
    return `${person.name || person.fullName || ''} ${person.location || person.city || ''} ${tags.join(' ')}`.toLowerCase().includes(query.toLowerCase());
  });
  return <FeaturePage title="Search people" subtitle="Search by name, city, or activity."><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search people, city, or interest…" className="w-full max-w-2xl rounded-xl border border-[#e4dff0] bg-white px-4 py-3 text-sm outline-none ring-violet-300 focus:ring-2" />{loading && <p className="mt-5 text-sm text-[#706a80]">Loading people…</p>}{error && <p role="alert" className="mt-5 text-sm text-rose-700">{error}</p>}<div className="mt-5 w-full max-w-3xl space-y-3">{!loading && !error && results.map((person) => <PersonRow key={person.id} person={person} />)}{!loading && !error && results.length === 0 && <p className="rounded-xl bg-white p-5 text-sm text-[#706a80]">No people match this search.</p>}</div></FeaturePage>;
}
