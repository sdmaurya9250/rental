import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getStoredUser, isAuthenticated } from '../auth/auth';
import { formatPrice } from '../data/people';
import AppointmentDetails from '../components/AppointmentDetails';
import { approveBookingRecord, fetchBookingRecords, rejectBookingRecord } from './finderApi';

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

function getChatPartnerId(booking, user) {
  const userId = String(user?.id || user?.user_id || user?.profile_id || '');
  const providerId = String(booking.rent_person_id || booking.provider_id || booking.rent_person?.id || '');
  const customerId = String(booking.customer_id || booking.customer_user_id || booking.finder_id || booking.finder_user_id || booking.requester_id || booking.booked_by_id || booking.user_id || booking.customer?.id || '');
  if (userId && userId === providerId) return customerId;
  return providerId || customerId;
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
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedBooking, setExpandedBooking] = useState(null);
  const [rejectingBooking, setRejectingBooking] = useState(null);
  const [rejectionMessage, setRejectionMessage] = useState('');
  const [approvingBooking, setApprovingBooking] = useState(null);
  const [submittingRejection, setSubmittingRejection] = useState(null);
  const [actionError, setActionError] = useState('');

  const signedIn = isAuthenticated();

  useEffect(() => {
    let active = true;
    if (!isAuthenticated()) {
      setError('Sign in to see your bookings.');
      setLoading(false);
      return () => { active = false; };
    }
    fetchBookingRecords()
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

  async function approveBookingRequest(booking) {
    setApprovingBooking(booking.id);
    setActionError('');
    try {
      const result = await approveBookingRecord(booking.id);
      const approvedBooking = result?.booking || result;
      updateBooking(booking.id, {
        ...(approvedBooking && typeof approvedBooking === 'object' ? approvedBooking : {}),
        booking_status: approvedBooking?.booking_status || approvedBooking?.status || 'approved',
      });
    } catch (requestError) {
      setActionError(requestError.message || 'Unable to approve this booking.');
    } finally {
      setApprovingBooking(null);
    }
  }

  async function rejectBookingRequest(booking) {
    setSubmittingRejection(booking.id);
    setActionError('');
    try {
      const result = await rejectBookingRecord(booking.id, rejectionMessage.trim());
      const rejectedBooking = result?.booking || result;
      updateBooking(booking.id, {
        ...(rejectedBooking && typeof rejectedBooking === 'object' ? rejectedBooking : {}),
        booking_status: rejectedBooking?.booking_status || rejectedBooking?.status || 'rejected',
        rejection_message: rejectedBooking?.rejection_message ?? rejectionMessage.trim(),
      });
    } catch (requestError) {
      setActionError(requestError.message || 'Unable to reject this booking.');
    } finally {
      setSubmittingRejection(null);
    }
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

      {actionError && <p role="alert" className="text-sm text-red-600">{actionError}</p>}

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
            const chatPartnerId = getChatPartnerId(booking, user);
            const canChat = ['approved', 'confirmed'].includes(status) && chatPartnerId;
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
                    {canChat && <Link to={`/messages?userId=${encodeURIComponent(chatPartnerId)}`} className="rounded-lg border border-violet-200 px-3 py-2 text-xs font-semibold text-violet-700 hover:bg-violet-50">Chat</Link>}
                    {canRespond && <>
                      <button type="button" onClick={() => approveBookingRequest(booking)} disabled={approvingBooking === booking.id} className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">{approvingBooking === booking.id ? 'Approving…' : 'Approve'}</button>
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
                    <button type="button" onClick={() => rejectBookingRequest(booking)} disabled={submittingRejection === booking.id} className="rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-50">{submittingRejection === booking.id ? 'Rejecting…' : 'Confirm rejection'}</button>
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
