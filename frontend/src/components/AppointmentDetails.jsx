import { useEffect, useId, useRef, useState } from 'react';
import QRCode from 'qrcode';

function formatDate(date) {
  if (!date) return 'Date not set';
  return new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

function CheckInScanner({ scannerId, onScan, onClose, onError }) {
  const onScanRef = useRef(onScan);
  const onErrorRef = useRef(onError);
  onScanRef.current = onScan;
  onErrorRef.current = onError;

  useEffect(() => {
    let scanner;
    let mounted = true;
    import('html5-qrcode').then(({ Html5QrcodeScanner }) => {
      if (!mounted) return;
      scanner = new Html5QrcodeScanner(scannerId, { fps: 10, qrbox: { width: 220, height: 220 } }, false);
      scanner.render((decodedText) => {
        if (!mounted) return;
        onScanRef.current(decodedText);
        scanner.clear().catch(() => {});
      }, () => {});
    }).catch(() => {
      if (mounted) onErrorRef.current('Unable to start the camera. Allow camera access and try again.');
    });
    return () => {
      mounted = false;
      scanner?.clear().catch(() => {});
    };
  }, [scannerId]);

  return <div className="mt-4 rounded-xl border border-violet-100 bg-white p-3">
    <div className="mb-2 flex items-center justify-between gap-3">
      <p className="text-sm font-semibold text-[#24202e]">Scan the other participant’s appointment QR</p>
      <button type="button" onClick={onClose} className="text-xs font-semibold text-violet-700 hover:underline">Close scanner</button>
    </div>
    <div id={scannerId} />
  </div>;
}

export default function AppointmentDetails({ booking, currentUser, onVerify }) {
  const generatedId = useId().replace(/:/g, '');
  const scannerId = `appointment-qr-scanner-${generatedId}`;
  const userId = String(currentUser?.id || currentUser?.user_id || currentUser?.profile_id || 'demo-user');
  const [qrDataUrl, setQrDataUrl] = useState('');
  const [showQr, setShowQr] = useState(false);
  const [showScanner, setShowScanner] = useState(false);
  const [message, setMessage] = useState('');
  const [scannerError, setScannerError] = useState('');

  useEffect(() => {
    if (!showQr) return undefined;
    let active = true;
    const payload = JSON.stringify({
      type: 'rental-meetup-check-in',
      bookingId: String(booking.id),
      userId,
    });
    QRCode.toDataURL(payload, { width: 240, margin: 2, color: { dark: '#171426', light: '#ffffff' } })
      .then((url) => { if (active) setQrDataUrl(url); })
      .catch(() => { if (active) setMessage('Could not generate this appointment QR.'); });
    return () => { active = false; };
  }, [booking.id, showQr, userId]);

  function handleScan(decodedText) {
    setShowScanner(false);
    setScannerError('');
    let payload;
    try {
      payload = JSON.parse(decodedText);
    } catch {
      setMessage('That QR code is not a RentCoPartner appointment code.');
      return;
    }
    if (payload.type !== 'rental-meetup-check-in' || String(payload.bookingId) !== String(booking.id)) {
      setMessage('This QR code does not match this appointment.');
      return;
    }
    if (!payload.userId || String(payload.userId) === userId) {
      setMessage('Scan the other participant’s QR code to confirm the meetup.');
      return;
    }
    onVerify({ meetup_verified: true, meetup_verified_at: new Date().toISOString(), meetup_verified_by: userId });
    setMessage('Meetup confirmed for this appointment.');
  }

  return <section className="mt-3 rounded-xl bg-violet-50/70 p-4 text-sm text-[#5d586e]">
    <div className="grid gap-3 sm:grid-cols-2">
      <p><strong className="text-[#24202e]">Service:</strong> {booking.service_name || booking.service?.name || 'Appointment'}</p>
      <p><strong className="text-[#24202e]">Date:</strong> {formatDate(booking.booking_date)}</p>
      <p><strong className="text-[#24202e]">Time:</strong> {booking.start_time || 'TBD'}–{booking.end_time || 'TBD'} ({booking.timezone || 'Local time'})</p>
      <p><strong className="text-[#24202e]">Meeting:</strong> {booking.location_type === 'online' ? 'Online' : booking.location || 'Location not set'}</p>
      {booking.special_requirements && <p><strong className="text-[#24202e]">Requirements:</strong> {booking.special_requirements}</p>}
      {booking.customer_note && <p><strong className="text-[#24202e]">Note:</strong> {booking.customer_note}</p>}
      {booking.rejection_message && <p className="text-red-700"><strong>Message:</strong> {booking.rejection_message}</p>}
      {booking.cancellation_message && <p className="text-red-700"><strong>Cancellation:</strong> {booking.cancellation_message}</p>}
    </div>

    {['approved', 'confirmed'].includes(String(booking.booking_status).toLowerCase()) && <div className="mt-4 border-t border-violet-100 pt-4">
      <h3 className="font-semibold text-[#24202e]">Meetup check-in</h3>
      {booking.meetup_verified ? <p role="status" className="mt-2 rounded-lg bg-emerald-50 p-3 text-sm font-medium text-emerald-800">Meetup confirmed{booking.meetup_verified_at ? ` · ${new Date(booking.meetup_verified_at).toLocaleString()}` : ''}</p> : <>
        <p className="mt-1 text-xs text-[#706a80]">At the meetup, scan the other participant’s appointment QR to confirm you met.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" onClick={() => { setShowQr((visible) => !visible); setMessage(''); }} className="rounded-lg border border-violet-200 bg-white px-3 py-2 text-xs font-semibold text-violet-700 hover:bg-violet-50">{showQr ? 'Hide my QR' : 'Show my check-in QR'}</button>
          <button type="button" onClick={() => { setShowScanner(true); setMessage(''); setScannerError(''); }} className="rounded-lg bg-violet-700 px-3 py-2 text-xs font-semibold text-white hover:bg-violet-800">Scan participant QR</button>
        </div>
        {showQr && <div className="mt-3 flex flex-col items-center rounded-xl border border-violet-100 bg-white p-4 sm:w-fit">
          {qrDataUrl ? <img src={qrDataUrl} alt="Your appointment check-in QR code" className="h-60 w-60" /> : <p className="p-8 text-xs text-[#706a80]">Generating QR…</p>}
          <p className="mt-2 text-xs text-[#706a80]">Let the other participant scan this code.</p>
        </div>}
        {showScanner && <CheckInScanner scannerId={scannerId} onScan={handleScan} onClose={() => setShowScanner(false)} onError={setScannerError} />}
        {scannerError && <p role="alert" className="mt-3 text-xs text-red-700">{scannerError}</p>}
        {message && <p role="status" className="mt-3 text-xs text-violet-800">{message}</p>}
      </>}
      <p className="mt-3 text-[11px] text-[#8b849d]">Check-in is stored locally in this demo. Shared verification between accounts requires a booking check-in endpoint.</p>
    </div>}
  </section>;
}
