import { useState } from 'react';
import { BriefcaseBusiness, CalendarDays, Clock3, MapPin, ClipboardList, MessageSquareText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { verifyBookingOtp } from '../auth/auth';

function formatDate(date) {
  if (!date) return 'Date not set';
  return new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function AppointmentDetails({ booking, currentUser, onVerify }) {
  const [otp, setOtp] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const status = String(booking.booking_status || '').toLowerCase();
  const isApproved = ['approved', 'confirmed'].includes(status);
  const otpVerified = booking.otp_verified === true || booking.otpVerified === true;
  const userId = String(currentUser?.id || currentUser?.user_id || currentUser?.profile_id || '');
  const providerId = String(booking.rent_person_id || booking.provider_id || '');
  const direction = String(booking.direction || booking.booking_direction || '').toLowerCase();
  const isProvider = ['incoming', 'received', 'provider'].includes(direction) || Boolean(userId && providerId && userId === providerId);
  const accountRole = String(currentUser?.want_to || currentUser?.wantTo || currentUser?.accountIntent || '').trim().toLowerCase();
  const isCompanion = accountRole === 'companion';

  async function submitVerification(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    if (!/^\d{6}$/.test(otp)) {
      setError('Enter the 6-digit OTP from the Find user.');
      return;
    }

    setVerifying(true);
    try {
      const result = await verifyBookingOtp(booking.id, otp);
      const verifiedBooking = result?.booking || result;
      onVerify?.({
        ...(verifiedBooking && typeof verifiedBooking === 'object' ? verifiedBooking : {}),
        booking_status: 'completed',
        otp_verified: true,
        needs_otp_entry: false,
      });
      setMessage(result?.message || 'OTP verified. Booking completed.');
      setOtp('');
    } catch (requestError) {
      setError(requestError.message || 'Unable to verify the OTP. Please try again.');
    } finally {
      setVerifying(false);
    }
  }

  return <section className="mt-3 rounded-xl bg-violet-50/70 p-4 text-sm text-[#5d586e]">

      {isProvider && isCompanion && booking.customer_id && (
        <div className="mb-4 flex flex-col gap-3 rounded-xl border border-violet-100 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <h3 className="font-semibold text-[#24202e]">
              Finder profile
            </h3>
            <p className="mt-1 text-xs text-[#706a80]">
              View their photos, about section, languages, and role.
            </p>
          </div>

          <Link
            to={`/finders/${encodeURIComponent(booking.customer_id)}`}
            className="inline-flex shrink-0 items-center justify-center self-start rounded-lg bg-violet-600 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-violet-700 sm:self-center"
          >
            View Finder Profile
          </Link>
        </div>
      )}

    <div className="grid gap-3 sm:grid-cols-2">
      <p className="flex items-center gap-2"><BriefcaseBusiness aria-hidden="true" className="h-4 w-4 shrink-0 text-violet-600" /><span><strong className="text-[#24202e]">Service:</strong> {booking.service_name || booking.service?.name || 'Appointment'}</span></p>
      <p className="flex items-center gap-2"><CalendarDays aria-hidden="true" className="h-4 w-4 shrink-0 text-violet-600" /><span><strong className="text-[#24202e]">Date:</strong> {formatDate(booking.booking_date)}</span></p>
      <p className="flex items-center gap-2"><Clock3 aria-hidden="true" className="h-4 w-4 shrink-0 text-violet-600" /><span><strong className="text-[#24202e]">Time:</strong> {booking.start_time || 'TBD'}–{booking.end_time || 'TBD'} ({booking.timezone || 'Local time'})</span></p>
      <p className="flex items-center gap-2"><MapPin aria-hidden="true" className="h-4 w-4 shrink-0 text-violet-600" /><span><strong className="text-[#24202e]">Meeting:</strong> {booking.location_type === 'online' ? 'Online' : booking.location || 'Location not set'}</span></p>
      {booking.special_requirements && <p className="flex items-center gap-2"><ClipboardList aria-hidden="true" className="h-4 w-4 shrink-0 text-violet-600" /><span><strong className="text-[#24202e]">Requirements:</strong> {booking.special_requirements}</span></p>}
      {booking.customer_note && <p className="flex items-center gap-2"><MessageSquareText aria-hidden="true" className="h-4 w-4 shrink-0 text-violet-600" /><span><strong className="text-[#24202e]">Note:</strong> {booking.customer_note}</span></p>}
      {booking.rejection_message && <p className="flex items-center gap-2 text-red-700"><MessageSquareText aria-hidden="true" className="h-4 w-4 shrink-0" /><span><strong>Message:</strong> {booking.rejection_message}</span></p>}
      {booking.cancellation_message && <p className="flex items-center gap-2 text-red-700"><MessageSquareText aria-hidden="true" className="h-4 w-4 shrink-0" /><span><strong>Cancellation:</strong> {booking.cancellation_message}</span></p>}
    </div>

    {isApproved && <div className="mt-4 border-t border-violet-100 pt-4">
      <h3 className="font-semibold text-[#24202e]">Complete booking with OTP</h3>
      {isProvider ? (
        otpVerified || booking.needs_otp_entry === false ? (
          <p role="status" className="mt-2 rounded-lg bg-emerald-50 p-3 text-sm font-medium text-emerald-800">
            {otpVerified ? 'OTP verified. Booking completed.' : 'No OTP entry is required for this booking.'}
          </p>
        ) : <>
          <p className="mt-1 text-xs text-[#706a80]">At the end of the appointment, ask the Find user for the 6-digit OTP sent to their registered phone.</p>
          <form onSubmit={submitVerification} className="mt-3 flex flex-col gap-2 sm:flex-row">
            <label className="sr-only" htmlFor={`booking-otp-${booking.id}`}>6-digit booking OTP</label>
            <input
              id={`booking-otp-${booking.id}`}
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={otp}
              onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="Enter 6-digit OTP"
              className="min-w-0 flex-1 rounded-lg border border-violet-200 bg-white px-3 py-2 text-sm text-[#24202e] outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
            />
            <button type="submit" disabled={verifying || otp.length !== 6} className="rounded-lg bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] px-4 py-2 text-xs font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-50">
              {verifying ? 'Verifying…' : 'Verify & complete'}
            </button>
          </form>
        </>
      ) : (
        <>
          {otpVerified ? (
            <p role="status" className="mt-2 rounded-lg bg-emerald-50 p-3 text-sm font-medium text-emerald-800">OTP verified. Booking completed.</p>
          ) : <>
            <p className="mt-1 text-xs leading-5 text-[#706a80]">At the end of the appointment, share this one-time OTP with the RentCoPartner. The booking is completed after they verify it.</p>
            {booking.show_otp && booking.otp && (
            <div className="mt-3 inline-flex min-w-48 flex-col items-center rounded-xl border border-violet-200 bg-white px-5 py-3 shadow-sm">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#827b95]">Your booking OTP</span>
              <span className="mt-1 font-mono text-2xl font-bold tracking-[0.3em] text-violet-700">{booking.otp}</span>
            </div>
            )}
          </>}
        </>
      )}
      {error && <p role="alert" className="mt-3 text-xs text-red-700">{error}</p>}
      {message && <p role="status" className="mt-3 rounded-lg bg-emerald-50 p-3 text-xs font-medium text-emerald-800">{message}</p>}
    </div>}
  </section>;
}
