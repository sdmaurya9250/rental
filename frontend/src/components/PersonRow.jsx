import { MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatPrice } from '../data/people';

export default function PersonRow({ person, action = 'View profile' }) {
  return <div className="flex items-center gap-3 rounded-xl border border-[#e7e1f2] bg-white p-3 shadow-sm"><img src={person.image} alt={person.name} className="h-14 w-14 rounded-lg object-cover" /><div className="min-w-0 flex-1"><p className="font-bold text-[#24202e]">{person.name}, {person.age}</p><p className="flex items-center gap-1 text-xs text-[#706a80]"><MapPin className="h-3 w-3" />{person.location}</p><p className="mt-1 text-sm font-bold text-[#24202e]">{formatPrice(person.rate)}/hr</p></div><Link to={`/people/${person.id}`} className="rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 px-3 py-2 text-xs font-semibold text-white">{action}</Link></div>;
}
