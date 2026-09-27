import { useState } from 'react';
import FeaturePage from '../components/FeaturePage';
import PersonRow from '../components/PersonRow';
import { people } from '../data/people';
export default function SearchResultsPage() { const [query, setQuery] = useState(''); const results = people.filter(person => `${person.name} ${person.location} ${person.tags.join(' ')}`.toLowerCase().includes(query.toLowerCase())); return <FeaturePage title="Search people"><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search people, city, or interest…" className="w-full max-w-2xl rounded-xl border border-[#e4dff0] bg-white px-4 py-3 text-sm outline-none ring-violet-300 focus:ring-2" /><div className="mt-5 max-w-2xl space-y-3">{results.map(person => <PersonRow key={person.id} person={person} />)}</div></FeaturePage>; }
