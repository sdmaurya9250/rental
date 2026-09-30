import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyBookings, getStoredUser, isAuthenticated } from '../auth/auth';
import { formatPrice } from '../data/people';
import AppointmentDetails from '../components/AppointmentDetails';

// Keep sample appointments enabled while the booking approval API is not available.
const USE_DUMMY_DATA = true;

const DUMMY_BOOKINGS = [
  {
    id: 'bk_out_1001', direction: 'outgoing', person_name: 'Aarav Sharma', person_image: 'https://i.pravatar.cc/150?img=12',
    booking_status: 'pending', booking_date: '2026-10-05', start_time: '10:00', end_time: '11:00', duration_minutes: 60,
    location_type: 'online', location: '', timezone: 'Asia/Kolkata', service_name: 'Coffee Partner', total_amount: 1500,
    special_requirements: 'Please suggest a quiet cafe or a video call.', customer_note: 'Looking forward to meeting!',
  },
  {
    id: 'bk_out_1002', direction: 'outgoing', person_name: 'Priya Singh', person_image: 'https://i.pravatar.cc/150?img=47',
    booking_status: 'approved', booking_date: '2026-10-12', start_time: '15:30', end_time: '17:00', duration_minutes: 90,
    location_type: 'in_person', location: 'Civil Lines, Prayagraj', timezone: 'Asia/Kolkata', service_name: 'Event Partner', total_amount: 2250,
    special_requirements: '', customer_note: 'I will message when I arrive.',
  },
  {
    id: 'bk_in_1003', direction: 'incoming', person_name: 'Rohan Verma', person_image: 'https://i.pravatar.cc/150?img=33',
    booking_status: 'pending', booking_date: '2026-10-18', start_time: '18:00', end_time: '19:00', duration_minutes: 60,
    location_type: 'online', location: '', timezone: 'Asia/Kolkata', service_name: 'Conversation Partner', total_amount: 1200,
    special_requirements: 'Would like to discuss local travel options.', customer_note: 'Please let me know if this time works.',
  },
  {
    id: 'bk_in_1004', direction: 'incoming', person_name: 'Neha Gupta', person_image: 'https://i.pravatar.cc/150?img=45',
    booking_status: 'approved', booking_date: '2026-10-22', start_time: '11:00', end_time: '12:30', duration_minutes: 90,
    location_type: 'in_person', location: 'Katra, Prayagraj', timezone: 'Asia/Kolkata', service_name: 'Coffee Partner', total_amount: 1800,
    special_requirements: '', customer_note: 'A cafe near the university would be great.',
  },
  {
    id: 'bk_out_1005', direction: 'outgoing', person_name: 'Kabir Mehta', person_image: 'https://i.pravatar.cc/150?img=15',
    booking_status: 'completed', booking_date: '2026-09-18', start_time: '09:00', end_time: '10:00', duration_minutes: 60,
    location_type: 'online', location: '', timezone: 'Asia/Kolkata', service_name: 'Travel Buddy', total_amount: 1000,
    special_requirements: '', customer_note: 'Thanks for the great recommendations!',
  },
  {
    id: 'bk_in_1006', direction: 'incoming', person_name: 'Isha Patel', person_image: 'https://i.pravatar.cc/150?img=49',
    booking_status: 'completed', booking_date: '2026-09-12', start_time: '16:00', end_time: '17:30', duration_minutes: 90,
    location_type: 'in_person', location: 'Civil Lines, Prayagraj', timezone: 'Asia/Kolkata', service_name: 'Event Partner', total_amount: 1800,
    special_requirements: 'Help with event planning ideas.', customer_note: 'Thank you for your time.',
  },
  {
    id: 'bk_out_1007', direction: 'outgoing', person_name: 'Vikram Rao', person_image: 'https://i.pravatar.cc/150?img=60',
    booking_status: 'cancelled', booking_date: '2026-09-24', start_time: '13:00', end_time: '14:00', duration_minutes: 60,
    location_type: 'in_person', location: 'Bandra, Mumbai', timezone: 'Asia/Kolkata', service_name: 'Coffee Partner', total_amount: 1200,
    cancellation_message: 'Plans changed; appointment cancelled by requester.',
  },
  {
    id: 'bk_in_1008', direction: 'incoming', person_name: 'Meera Shah', person_image: 'https://i.pravatar.cc/150?img=44',
    booking_status: 'rejected', booking_date: '2026-09-20', start_time: '14:00', end_time: '15:00', duration_minutes: 60,
    location_type: 'online', location: '', timezone: 'Asia/Kolkata', service_name: 'Conversation Partner', total_amount: 900,
    rejection_message: 'Sorry, I am unavailable at that time. Please choose another slot.',
  },
];

const tabs = ['Upcoming', 'Completed', 'Cancelled'];

function formatDate(date) {
  if (!date) return 'Date not set';
  return new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

function getRole(user) {
  const role = String(user?.want_to || user?.wantTo || user?.accountIntent || '').trim().toLowerCase();
  if (role === 'both') return 'both';
  if (role.includes('become')) return 'become';
  if (role.includes('find')) return 'find';
  return 'find';
}

function getDirection(booking, user) {
  const value = String(booking.direction || booking.booking_direction || '').toLowerCase();
  if (['incoming', 'received', 'provider'].includes(value)) return 'incoming';
  if (['outgoing', 'sent', 'customer'].includes(value)) return 'outgoing';
  if (booking.is_incoming === true || booking.is_provider === true) return 'incoming';
  if (booking.is_incoming === false || booking.is_provider === false) return 'outgoing';

  const userId = String(user?.id || user?.user_id || user?.profile_id || '');
  const providerId = String(booking.rent_person_id || booking.provider_id || booking.rent_person?.id || '');
  if (userId && providerId && userId === providerId) return 'incoming';
  return 'outgoing';
}

function statusLabel(status) {
  const normalized = String(status || 'pending').toLowerCase();
  return normalized === 'confirmed' ? 'Approved' : normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function statusStyle(status) {
  const normalized = String(status || 'pending').toLowerCase();
  if (['approved', 'confirmed'].includes(normalized)) return 'bg-emerald-50 text-emerald-700';
  if (['rejected', 'cancelled'].includes(normalized)) return 'bg-red-50 text-red-700';
  return 'bg-amber-50 text-amber-700';
}

export default function BookingsList() {
  const user = getStoredUser();
  const role = getRole(user);
  const [activeTab, setActiveTab] = useState('Upcoming');
  const [bookings, setBookings] = useState(USE_DUMMY_DATA ? DUMMY_BOOKINGS : []);
  const [loading, setLoading] = useState(!USE_DUMMY_DATA);
  const [error, setError] = useState('');
  const [expandedBooking, setExpandedBooking] = useState(null);
  const [rejectingBooking, setRejectingBooking] = useState(null);
  const [rejectionMessage, setRejectionMessage] = useState('');

  const signedIn = USE_DUMMY_DATA || isAuthenticated();

  useEffect(() => {
    if (USE_DUMMY_DATA) return undefined;
    let active = true;
    if (!isAuthenticated()) {
      setError('Sign in to see your bookings.');
      setLoading(false);
      return () => { active = false; };
    }
    getMyBookings()
      .then((data) => { if (active) setBookings(Array.isArray(data) ? data : data?.bookings || []); })
      .catch((requestError) => { if (active) setError(requestError.message || 'Unable to load bookings.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const roleBookings = useMemo(() => bookings.filter((booking) => {
    const direction = getDirection(booking, user);
    return role === 'both' || (role === 'become' ? direction === 'incoming' : direction === 'outgoing');
  }), [bookings, role, user]);

  const visibleBookings = useMemo(() => roleBookings.filter((booking) => {
    const status = String(booking.booking_status || 'pending').toLowerCase();
    if (activeTab === 'Completed') return status === 'completed';
    if (activeTab === 'Cancelled') return ['cancelled', 'rejected'].includes(status);
    return !['completed', 'cancelled', 'rejected'].includes(status);
  }), [activeTab, roleBookings]);

  function updateBooking(bookingId, changes) {
    setBookings((current) => current.map((booking) => booking.id === bookingId ? { ...booking, ...changes } : booking));
    setRejectingBooking(null);
    setRejectionMessage('');
  }

  function rejectBooking(booking) {
    updateBooking(booking.id, { booking_status: 'rejected', rejection_message: rejectionMessage.trim() });
  }

  return (
    <main className="min-h-full space-y-6 bg-[#f8f6ff] p-6 text-[#171426] lg:p-8">
      <div>
        <h1 className="text-2xl font-bold">My bookings</h1>
        <p className="mt-1 text-sm text-[#706a80]">Track appointments you requested and manage requests you receive.</p>
      </div>

      <div className="flex w-fit items-center gap-1 rounded-xl border border-[#e7e1f2] bg-white p-1.5 shadow-sm">
        {tabs.map((tab) => <button key={tab} type="button" onClick={() => setActiveTab(tab)} className={`rounded-lg px-5 py-2 text-sm font-medium transition ${activeTab === tab ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow' : 'text-[#706a80] hover:text-violet-700'}`}>{tab}</button>)}
      </div>

      {loading ? <p className="text-sm text-[#706a80]">Loading bookings…</p> : error ? <div role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{error} {!signedIn && <Link to="/login" className="font-semibold underline">Sign in</Link>}</div> : visibleBookings.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#d9d0eb] bg-white p-10 text-center">
          <p className="font-semibold">No {activeTab.toLowerCase()} appointments yet.</p>
          <Link to="/browse" className="mt-3 inline-block text-sm font-semibold text-violet-700 hover:underline">Browse people</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {visibleBookings.map((booking) => {
            const direction = getDirection(booking, user);
            const isIncoming = direction === 'incoming';
            const status = String(booking.booking_status || 'pending').toLowerCase();
            const canRespond = isIncoming && status === 'pending';
            const isExpanded = expandedBooking === booking.id;
            const personName = booking.person_name || booking.customer_name || booking.rent_person?.name || 'Unknown person';
            const personImage = booking.person_image || booking.customer_image || booking.rent_person?.image || 'https://i.pravatar.cc/150?img=1';

            return (
              <article key={booking.id} className="rounded-2xl border border-[#e7e1f2] bg-white p-4 shadow-sm">
                <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                  <div className="flex min-w-0 items-center gap-4">
                    <img src={personImage} alt={personName} className="h-16 w-16 rounded-xl object-cover" />
                    <div className="min-w-0">
                      <h2 className="font-bold">{personName}</h2>
                      <p className="mt-1 text-xs text-[#706a80]">{isIncoming ? 'Appointment request from' : 'Appointment with'} · {formatDate(booking.booking_date)} · {booking.start_time || 'Time TBD'}–{booking.end_time || 'TBD'}</p>
                      <p className="mt-1 text-xs text-[#706a80]">{booking.location_type === 'online' ? 'Online' : booking.location || booking.rent_person?.location || 'Location not set'} · {booking.duration_minutes || 0} min</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-3 sm:justify-end">
                    <span className={`rounded-full px-3 py-1.5 text-xs font-semibold ${statusStyle(status)}`}>{statusLabel(status)}</span>
                    <span className="text-sm font-bold">{formatPrice(Number(booking.total_amount) || 0)}</span>
                    {canRespond && <>
                      <button type="button" onClick={() => updateBooking(booking.id, { booking_status: 'approved', response_message: '' })} className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700">Approve</button>
                      <button type="button" onClick={() => { setRejectingBooking(booking.id); setRejectionMessage(''); }} className="rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-50">Reject</button>
                    </>}
                  </div>
                </div>

                {canRespond && rejectingBooking === booking.id && <div className="mt-4 rounded-xl border border-red-100 bg-red-50/60 p-4">
                  <label className="block text-sm font-semibold text-[#40394f]">Message to the requester <span className="font-normal text-[#8b849d]">(optional)</span>
                    <textarea rows="2" value={rejectionMessage} onChange={(event) => setRejectionMessage(event.target.value)} placeholder="Add a reason or suggest another time" className="mt-2 w-full rounded-lg border border-[#e4dff0] bg-white px-3 py-2.5 text-sm font-normal" />
                  </label>
                  <div className="mt-3 flex justify-end gap-2">
                    <button type="button" onClick={() => setRejectingBooking(null)} className="rounded-lg px-3 py-2 text-xs font-semibold text-[#706a80]">Cancel</button>
                    <button type="button" onClick={() => rejectBooking(booking)} className="rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-700">Confirm rejection</button>
                  </div>
                </div>}

                <button type="button" aria-expanded={isExpanded} onClick={() => setExpandedBooking(isExpanded ? null : booking.id)} className="mt-3 text-sm font-semibold text-violet-700 hover:underline">{isExpanded ? 'Hide appointment details' : 'View appointment details'}</button>
                {isExpanded && <AppointmentDetails
                  booking={booking}
                  currentUser={user}
                  onVerify={(changes) => updateBooking(booking.id, changes)}
                />}
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}
