import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyBookings, isAuthenticated } from '../auth/auth';
import { findPerson, formatPrice } from '../data/people';

const tabs = ['Upcoming', 'Completed', 'Cancelled'];

function formatDate(date) {
  if (!date) return 'Date not set';
  return new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function BookingsList() {
  const [activeTab, setActiveTab] = useState('Upcoming');
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    if (!isAuthenticated()) {
      setError('Sign in to see your bookings.');
      setLoading(false);
      return () => { active = false; };
    }
    getMyBookings()
      .then((data) => { if (active) setBookings(Array.isArray(data) ? data : []); })
      .catch((requestError) => { if (active) setError(requestError.message || 'Unable to load bookings.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const visibleBookings = useMemo(() => bookings.filter((booking) => {
    const status = String(booking.booking_status || '').toLowerCase();
    if (activeTab === 'Completed') return status === 'completed';
    if (activeTab === 'Cancelled') return status === 'cancelled';
    return status !== 'completed' && status !== 'cancelled';
  }), [activeTab, bookings]);

  return (
    <main className="min-h-full space-y-6 bg-[#f8f6ff] p-6 text-[#171426] lg:p-8">
      <div>
        <h1 className="text-2xl font-bold">My bookings</h1>
        <p className="mt-1 text-sm text-[#706a80]">Your booking requests and their current status.</p>
      </div>

      <div className="flex w-fit items-center gap-1 rounded-xl border border-[#e7e1f2] bg-white p-1.5 shadow-sm">
        {tabs.map((tab) => <button key={tab} onClick={() => setActiveTab(tab)} className={`rounded-lg px-5 py-2 text-sm font-medium transition ${activeTab === tab ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow' : 'text-[#706a80] hover:text-violet-700'}`}>{tab}</button>)}
      </div>

      {loading ? <p className="text-sm text-[#706a80]">Loading bookings…</p> : error ? <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{error} {!isAuthenticated() && <Link to="/login" className="font-semibold underline">Sign in</Link>}</div> : visibleBookings.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#d9d0eb] bg-white p-10 text-center">
          <p className="font-semibold">No {activeTab.toLowerCase()} bookings yet.</p>
          <Link to="/browse" className="mt-3 inline-block text-sm font-semibold text-violet-700 hover:underline">Browse people</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {visibleBookings.map((booking) => {
            const person = findPerson(booking.rent_person_id);
            const status = String(booking.booking_status || 'pending');
            return (
              <article key={booking.id} className="flex flex-col justify-between gap-4 rounded-2xl border border-[#e7e1f2] bg-white p-4 shadow-sm sm:flex-row sm:items-center">
                <div className="flex min-w-0 items-center gap-4">
                  <img src={person.image} alt={person.name} className="h-16 w-16 rounded-xl object-cover" />
                  <div className="min-w-0">
                    <h2 className="font-bold">{person.name}</h2>
                    <p className="mt-1 text-xs text-[#706a80]">{formatDate(booking.booking_date)} · {booking.start_time}–{booking.end_time} · {booking.duration_minutes} min</p>
                    <p className="mt-1 text-xs text-[#706a80]">{booking.location_type === 'online' ? 'Online' : booking.location || person.location} · {booking.timezone}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between gap-4 sm:justify-end">
                  <span className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize ${status === 'confirmed' ? 'bg-emerald-50 text-emerald-700' : status === 'cancelled' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'}`}>{status}</span>
                  <span className="text-sm font-bold">{formatPrice(Number(booking.total_amount) || 0)}</span>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}
