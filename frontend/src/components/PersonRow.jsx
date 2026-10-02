import { MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatPersonPrice, getPersonPrice } from '../pages/finderApi';

export default function PersonRow({ person, action = 'View profile' }) {
  const name = person.name || person.fullName || person.full_name || 'RentPeople member';
  const location = person.location || person.city || 'India';
  const price = getPersonPrice(person);
  return <div className="flex min-w-0 items-center gap-3 rounded-xl border border-violet-100 bg-white p-3 shadow-sm"><img src={person.image || person.profile_image || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop'} alt={name} className="h-14 w-14 shrink-0 rounded-lg object-cover" /><div className="min-w-0 flex-1"><p className="truncate font-bold text-[#24202e]">{name}{person.age ? `, ${person.age}` : ''}</p><p className="flex items-center gap-1 truncate text-xs text-[#706a80]"><MapPin className="h-3 w-3 shrink-0" />{location}</p><p className="mt-1 text-sm font-bold text-[#24202e]">{formatPersonPrice(price)}/hr</p></div><Link to={`/people/${person.id}`} className="shrink-0 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-500 px-2.5 py-2 text-center text-[11px] font-semibold text-white sm:px-3 sm:text-xs">{action}</Link></div>;
}
