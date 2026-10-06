import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getStoredUser, isAuthenticated } from '../auth/auth';
import { formatPrice } from '../data/people';
import AppointmentDetails from '../components/AppointmentDetails';
import { approveBookingRecord, fetchBookingRecords, rejectBookingRecord } from './finderApi';

const tabs = ['All Bookings', 'Upcoming', 'Completed', 'Cancelled'];

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

function bookingStatus(booking) {
  if (booking.otp_verified === true || booking.otpVerified === true) return 'completed';
  return String(booking.booking_status || 'pending').toLowerCase();
}

function statusBadgeStyle(status) {
  const normalized = String(status || 'pending').toLowerCase();
  if (['approved', 'confirmed', 'upcoming'].includes(normalized)) return 'bg-blue-50 text-blue-600 border-blue-100';
  if (['completed'].includes(normalized)) return 'bg-emerald-50 text-emerald-600 border-emerald-100';
  if (['rejected', 'cancelled'].includes(normalized)) return 'bg-rose-50 text-rose-600 border-rose-100';
  return 'bg-amber-50 text-amber-600 border-amber-100';
}

export default function BookingsList() {
  const user = getStoredUser();
  const role = getRole(user);
  const [activeTab, setActiveTab] = useState('All Bookings');
  const [searchQuery, setSearchQuery] = useState('');
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

  const metrics = useMemo(() => {
    let upcoming = 0;
    let completed = 0;
    let cancelled = 0;
    let totalSpent = 0;

    roleBookings.forEach((b) => {
      const st = bookingStatus(b);
      const amount = Number(b.total_amount) || 0;

      if (st === 'completed') completed += 1;
      else if (['cancelled', 'rejected'].includes(st)) cancelled += 1;
      else upcoming += 1;

      totalSpent += amount;
    });

    return { upcoming, completed, cancelled, totalSpent };
  }, [roleBookings]);

  const visibleBookings = useMemo(() => roleBookings.filter((booking) => {
    const status = bookingStatus(booking);
    const personName = (booking.person_name || booking.customer_name || booking.rent_person?.name || '').toLowerCase();
    
    if (searchQuery && !personName.includes(searchQuery.toLowerCase())) {
      return false;
    }

    if (activeTab === 'Completed') return status === 'completed';
    if (activeTab === 'Cancelled') return ['cancelled', 'rejected'].includes(status);
    if (activeTab === 'Upcoming') return !['completed', 'cancelled', 'rejected'].includes(status);
    return true;
  }), [activeTab, roleBookings, searchQuery]);

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
    <main className="min-h-screen bg-[#f8f9fe] p-4 text-[#1a1c23] sm:p-6 lg:p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#111827]">My Bookings</h1>
          <p className="mt-0.5 text-sm text-[#6b7280]">Track and manage all your appointments and booking requests.</p>
        </div>

        {/* Top Summary Metrics */}
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-2 sm:gap-4 lg:grid-cols-4">
          <div className="flex min-w-0 items-center gap-2 rounded-2xl border border-gray-100 bg-white p-2.5 shadow-sm sm:gap-4 sm:p-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-purple-50 text-purple-600 sm:h-12 sm:w-12 sm:rounded-xl">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
            </div>
            <div>
              <p className="text-xl font-bold leading-none text-gray-900 sm:text-xl">{metrics.upcoming}</p>
              <p className="mt-1 text-[10px] font-medium leading-tight text-gray-500 sm:text-xs">Upcoming</p>
            </div>
          </div>

          <div className="flex min-w-0 items-center gap-2 rounded-2xl border border-gray-100 bg-white p-2.5 shadow-sm sm:gap-4 sm:p-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 sm:h-12 sm:w-12 sm:rounded-xl">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            </div>
            <div>
              <p className="text-xl font-bold leading-none text-gray-900">{metrics.completed}</p>
              <p className="mt-1 text-[10px] font-medium leading-tight text-gray-500 sm:text-xs">Completed</p>
            </div>
          </div>

          <div className="flex min-w-0 items-center gap-2 rounded-2xl border border-gray-100 bg-white p-2.5 shadow-sm sm:gap-4 sm:p-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-rose-50 text-rose-600 sm:h-12 sm:w-12 sm:rounded-xl">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            </div>
            <div>
              <p className="text-xl font-bold leading-none text-gray-900">{metrics.cancelled}</p>
              <p className="mt-1 text-[10px] font-medium leading-tight text-gray-500 sm:text-xs">Cancelled</p>
            </div>
          </div>

          <div className="hidden items-center gap-4 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm sm:flex">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500">Total Spent</p>
              <p className="text-xl font-bold text-gray-900">{formatPrice(metrics.totalSpent)}</p>
              <p className="text-xs text-gray-400">Across all bookings</p>
            </div>
          </div>
        </div>

        {/* Filter Navigation & Search Bar */}
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="order-2 flex w-full items-center gap-1.5 overflow-x-auto rounded-2xl border border-gray-100 bg-white p-1.5 shadow-sm lg:order-1 lg:w-auto">
            {tabs.map((tab) => {
              const isActive = activeTab === tab;
              return (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveTab(tab)}
                  className={`flex shrink-0 items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition-all sm:px-4 ${
                    isActive
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow'
                      : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  {tab === 'All Bookings' && (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>
                  )}
                  {tab === 'Upcoming' && (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  )}
                  {tab === 'Completed' && (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/></svg>
                  )}
                  {tab === 'Cancelled' && (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
                  )}
                  {tab === 'All Bookings' ? 'All' : tab}
                </button>
              );
            })}
          </div>

          <div className="order-1 flex w-full items-center gap-2.5 lg:order-2 lg:w-auto">
            <div className="relative min-w-0 flex-1 lg:w-64 lg:flex-none">
              <svg className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
              <input
                type="text"
                placeholder="Search bookings..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-full border border-gray-200 bg-white py-3 pl-10 pr-4 text-sm font-medium placeholder-gray-400 shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
            </div>
            <button type="button" className="flex shrink-0 items-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-purple-700 shadow-sm hover:bg-gray-50">
              <svg className="h-4 w-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/></svg>
              Filter
            </button>
          </div>
        </div>

        {actionError && <p role="alert" className="text-xs font-medium text-rose-600">{actionError}</p>}

        {/* Content Section */}
        {loading ? (
          <div className="rounded-2xl border border-gray-100 bg-white p-8 text-center text-xs font-medium text-gray-500">
            Loading bookings…
          </div>
        ) : error ? (
          <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
            {error} {!signedIn && <Link className="font-semibold underline" to="/login">Sign in</Link>}
          </div>
        ) : visibleBookings.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-gray-200 bg-white p-12 text-center">
            <p className="text-sm font-semibold text-gray-700">No {activeTab.toLowerCase()} appointments found.</p>
            <Link className="mt-3 inline-block text-xs font-semibold text-purple-600 hover:underline" to="/browse">
              Browse people
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {visibleBookings.map((booking) => {
              const direction = getDirection(booking, user);
              const isIncoming = direction === 'incoming';
              const status = bookingStatus(booking);
              const canRespond = isIncoming && status === 'pending';
              const chatPartnerId = getChatPartnerId(booking, user);
              const canChat = ['approved', 'confirmed'].includes(status) && chatPartnerId;
              const isExpanded = expandedBooking === booking.id;
              const personName = booking.person_name || booking.customer_name || booking.rent_person?.name || 'Unknown person';
              const personImage = booking.person_image || booking.customer_image || booking.rent_person?.image || 'https://i.pravatar.cc/150?img=1';

              const tags = booking.tags || booking.services || ['Companion', 'Chat', 'Dinner', 'Events'];

              return (
                <article key={booking.id} className="overflow-hidden rounded-2xl border border-gray-100 bg-white p-5 shadow-sm transition hover:shadow-md">
                  <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
                    
                    {/* Left Details */}
                    <div className="flex flex-1 items-start gap-4">
                      <div className="relative h-28 w-28 shrink-0 overflow-hidden rounded-2xl bg-gray-100">
                        <img src={personImage} alt={personName} className="h-full w-full object-cover" />
                        {booking.is_online && (
                          <span className="absolute bottom-2 left-2 flex items-center gap-1 rounded-full bg-black/60 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur-sm">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span> Online
                          </span>
                        )}
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <h2 className="text-base font-bold text-gray-900">{personName}</h2>
                          <svg className="h-4 w-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/></svg>
                          <div className="flex items-center text-xs font-semibold text-gray-700">
                            <span className="text-amber-400">★</span>
                            <span className="ml-1">{booking.rating || '4.8'}</span>
                            <span className="ml-0.5 text-gray-400">({booking.reviews_count || '120'} reviews)</span>
                          </div>
                        </div>

                        {/* Service Tags */}
                        <div className="flex flex-wrap gap-1.5">
                          {tags.slice(0, 4).map((tag, i) => (
                            <span key={i} className="rounded-md bg-purple-50/60 px-2.5 py-0.5 text-[11px] font-medium text-purple-700">
                              {tag}
                            </span>
                          ))}
                        </div>

                        {/* Metadata */}
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-gray-500">
                          <div className="flex items-center gap-1.5">
                            <svg className="h-3.5 w-3.5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                            <span>{formatDate(booking.booking_date)}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <svg className="h-3.5 w-3.5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            <span>{booking.start_time || '18:00'} - {booking.end_time || '20:00'}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <svg className="h-3.5 w-3.5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            <span>{booking.duration_minutes || 120} min</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <svg className="h-3.5 w-3.5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                            <span>{booking.location_type === 'online' ? 'Online' : booking.location || booking.rent_person?.location || 'Location not set'}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Right Actions & Price */}
                    <div className="flex flex-col items-start justify-between gap-3 lg:items-end">
                      <div className="flex items-center gap-2">
                        <span className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${statusBadgeStyle(status)}`}>
                          {status === 'completed' && <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>}
                          {status === 'cancelled' && <span className="h-1.5 w-1.5 rounded-full bg-rose-500"></span>}
                          {['approved', 'confirmed', 'pending'].includes(status) && <span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span>}
                          {statusLabel(status)}
                        </span>
                      </div>

                      <div className="text-xl font-extrabold text-gray-900">
                        {formatPrice(Number(booking.total_amount) || 0)}
                      </div>

                      <div className="flex flex-wrap items-center gap-2">
                        {canChat && (
                          <Link className="flex items-center gap-1.5 rounded-xl border border-purple-200 bg-white px-3.5 py-2 text-xs font-semibold text-purple-700 hover:bg-purple-50" to={`/messages?userId=${encodeURIComponent(chatPartnerId)}`}>
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
                            Message
                          </Link>
                        )}

                        {canRespond && (
                          <>
                            <button
                              type="button"
                              onClick={() => approveBookingRequest(booking)}
                              disabled={approvingBooking === booking.id}
                              className="rounded-xl bg-emerald-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                            >
                              {approvingBooking === booking.id ? 'Approving…' : 'Approve'}
                            </button>
                            <button
                              type="button"
                              onClick={() => { setRejectingBooking(booking.id); setRejectionMessage(''); }}
                              className="rounded-xl border border-rose-200 px-3.5 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-50"
                            >
                              Reject
                            </button>
                          </>
                        )}

                        {status === 'completed' && (
                          <button
                            type="button"
                            className="flex items-center gap-1.5 rounded-xl bg-purple-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-purple-700"
                          >
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                            Book Again
                          </button>
                        )}

                        {!canRespond && status !== 'completed' && (
                          <button
                            type="button"
                            onClick={() => { setRejectingBooking(booking.id); setRejectionMessage(''); }}
                            className="rounded-xl border border-rose-200 px-3.5 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50"
                          >
                            Cancel
                          </button>
                        )}

                        <button
                          type="button"
                          aria-expanded={isExpanded}
                          onClick={() => setExpandedBooking(isExpanded ? null : booking.id)}
                          className="rounded-xl border border-gray-200 bg-white px-3.5 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                        >
                          View Details
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Informational Status Banner */}
                  <div className="mt-4">
                    {status === 'completed' && (
                      <div className="flex items-center gap-2 rounded-xl bg-emerald-50/60 p-3 text-xs text-emerald-800">
                        <svg className="h-4 w-4 shrink-0 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        <div>
                          <span className="font-bold">Appointment completed</span>
                          <span className="ml-1 text-emerald-700">— Hope you had a great time! You can book again or leave a review.</span>
                        </div>
                      </div>
                    )}

                    {status === 'cancelled' && (
                      <div className="flex items-center gap-2 rounded-xl bg-rose-50/60 p-3 text-xs text-rose-800">
                        <svg className="h-4 w-4 shrink-0 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        <div>
                          <span className="font-bold">Booking cancelled</span>
                          <span className="ml-1 text-rose-700">— {booking.rejection_message ? `Reason: ${booking.rejection_message}` : 'This booking was cancelled.'}</span>
                        </div>
                      </div>
                    )}

                    {!['completed', 'cancelled', 'rejected'].includes(status) && (
                      <div className="flex items-center gap-2 rounded-xl bg-blue-50/60 p-3 text-xs text-blue-800">
                        <svg className="h-4 w-4 shrink-0 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        <div>
                          <span className="font-bold">Upcoming appointment</span>
                          <span className="ml-1 text-blue-700">— Get ready for your appointment. You can chat with your provider now.</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Rejection Modal/Form */}
                  {canRespond && rejectingBooking === booking.id && (
                    <div className="mt-4 rounded-xl border border-rose-100 bg-rose-50/60 p-4">
                      <label className="block text-xs font-semibold text-gray-700">
                        Message to the requester <span className="font-normal text-gray-400">(optional)</span>
                        <textarea
                          rows="2"
                          value={rejectionMessage}
                          onChange={(e) => setRejectionMessage(e.target.value)}
                          placeholder="Add a reason or suggest another time"
                          className="mt-2 w-full rounded-lg border border-gray-200 bg-white p-2.5 text-xs text-gray-800 placeholder-gray-400 focus:outline-none"
                        />
                      </label>
                      <div className="mt-3 flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setRejectingBooking(null)}
                          className="rounded-lg px-3 py-1.5 text-xs font-semibold text-gray-500 hover:text-gray-700"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={() => rejectBookingRequest(booking)}
                          disabled={submittingRejection === booking.id}
                          className="rounded-lg bg-rose-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
                        >
                          {submittingRejection === booking.id ? 'Rejecting…' : 'Confirm rejection'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Expanded Appointment Details */}
                  {isExpanded && (
                    <div className="mt-4 border-t border-gray-100 pt-4">
                      <AppointmentDetails
                        booking={booking}
                        currentUser={user}
                        onVerify={(changes) => updateBooking(booking.id, changes)}
                      />
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
