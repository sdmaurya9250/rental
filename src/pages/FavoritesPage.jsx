import FeaturePage from '../components/FeaturePage';
import PersonRow from '../components/PersonRow';
import { people } from '../data/people';
export default function FavoritesPage() { return <FeaturePage title="My favorites" subtitle="Quick booking from your saved people."><div className="max-w-2xl space-y-3">{people.map(person => <PersonRow key={person.id} person={person} action="Book now" />)}</div></FeaturePage>; }
