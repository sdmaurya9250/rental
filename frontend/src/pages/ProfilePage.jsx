import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Heart, MapPin } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import FeaturePage from '../components/FeaturePage';
import { createBooking, isAuthenticated } from '../auth/auth';
import { formatPersonPrice as formatPrice, fetchPersonById, getPersonPrice } from './finderApi';

function localDate() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

function slug(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function durationHours(service) {
  if (/full day/i.test(service.duration || '')) return 6;
  return Number(service.duration?.match(/\d+/)?.[0]) || 1;
}

function formatAvailability(value) {
  if (!value) return 'Not specified';
  try {
    const parsed = typeof value === 'string' ? JSON.parse(value) : value;
    if (Array.isArray(parsed.days) && parsed.days.length) return parsed.days.join(', ');
  } catch {
    return value;
  }
  return typeof value === 'string' ? value : 'Not specified';
}

export default function ProfilePage() {
  const { personId } = useParams();
  const [person, setPerson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadError('');
    fetchPersonById(personId)
      .then((result) => { if (active) setPerson({ ...result, rate: getPersonPrice(result), tags: result.tags || [] }); })
      .catch((error) => { if (active) setLoadError(error.message || 'Unable to load this profile.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [personId]);

  if (loading) return <FeaturePage title="Loading profile…" subtitle="Fetching profile details." />;
  if (loadError || !person) return <FeaturePage title="Profile unavailable" subtitle={loadError || 'This profile could not be found.'}><Link to="/browse" className="text-sm font-medium text-violet-700 hover:underline">← Back to browse</Link></FeaturePage>;

  return <ProfileDetails person={person} />;
}

function ProfileDetails({ person }) {
  const services = useMemo(() => (person.services || [
    { title: 'Coffee Partner', price: person.rate || 1500, duration: '1 hr' },
    { title: 'Cafe & Food Partner', price: (person.rate || 1500) * 1.5, duration: '2 hrs' },
    { title: 'Event Partner', price: (person.rate || 1500) * 2.5, duration: '3 hrs' },
    { title: 'Travel Buddy', price: (person.rate || 1500) * 4, duration: 'Full Day' },
  ]).map((service, index) => ({
    ...service,
    id: String(service.id || slug(service.title || service.name || `service-${index + 1}`)),
    title: service.title || service.name || 'Service',
    price: Number(service.price) || Number(person.rate) || 1500,
  })), [person]);
  const [activeImage, setActiveImage] = useState(person.image || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=800&auto=format&fit=crop');
  const [selectedServiceId, setSelectedServiceId] = useState(services[0]?.id || '');
  const [bookingDate, setBookingDate] = useState(localDate);
  const [startTime, setStartTime] = useState('12:00');
  const [endTime, setEndTime] = useState('14:00');
  const [locationType, setLocationType] = useState('in_person');
  const [location, setLocation] = useState(person.location || '');
  const [specialRequirements, setSpecialRequirements] = useState('');
  const [customerNote, setCustomerNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [createdBooking, setCreatedBooking] = useState(null);
  const [showBookingForm, setShowBookingForm] = useState(false);

  const selectedService = services.find((service) => service.id === selectedServiceId) || services[0];
  const galleryImages = person.images || [
    person.image || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=800&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&q=80&w=800',
    'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&q=80&w=800',
  ];
  const [startHour, startMinute] = startTime.split(':').map(Number);
  const [endHour, endMinute] = endTime.split(':').map(Number);
  const durationMinutes = endHour * 60 + endMinute - (startHour * 60 + startMinute);
  const price = selectedService && durationMinutes > 0
    ? Math.round(selectedService.price * durationMinutes / (durationHours(selectedService) * 60))
    : 0;
  const platformFee = Math.round(price * 0.125);
  const totalAmount = price + platformFee;

  async function submitBooking(event) {
    event.preventDefault();
    setBookingError('');
    setCreatedBooking(null);
    if (!isAuthenticated()) {
      setBookingError('Please sign in before submitting a booking.');
      return;
    }
    if (!selectedService || durationMinutes <= 0) {
      setBookingError('Choose a valid start and end time.');
      return;
    }
    if (!bookingDate || (locationType === 'in_person' && !location.trim())) {
      setBookingError('Please complete the date and location.');
      return;
    }

    setSubmitting(true);
    try {
      const booking = await createBooking({
        booking_date: bookingDate,
        start_time: startTime,
        end_time: endTime,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata',
        duration_minutes: durationMinutes,
        location_type: locationType,
        location: location.trim(),
        service_id: selectedService.id,
        rent_person_id: person.id,
        special_requirements: specialRequirements.trim() || null,
        customer_note: customerNote.trim() || null,
        price,
        platform_fee: platformFee,
        total_amount: totalAmount,
      });
      setCreatedBooking(booking);
    } catch (error) {
      setBookingError(error.message || 'Unable to submit this booking. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FeaturePage title={`${person.name}'s profile`} subtitle="Choose a service and send a booking request from this page.">
      <Link to="/browse" className="text-sm font-medium text-violet-700 hover:underline">← Back to browse</Link>

      <div className="mt-5 grid max-w-5xl gap-6 rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm md:grid-cols-[300px_1fr]">
        <div className="space-y-3">
          <div className="relative h-80 w-full overflow-hidden rounded-xl bg-gray-100">
            <img src={activeImage} alt={person.name} className="h-full w-full object-cover" />
            {person.isOnline && <span className="absolute left-3 top-3 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">● Online</span>}
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {galleryImages.map((image, index) => (
              <button key={image} type="button" onClick={() => setActiveImage(image)} className={`h-14 w-14 shrink-0 overflow-hidden rounded-lg border-2 ${activeImage === image ? 'border-violet-600' : 'border-transparent opacity-75'}`}>
                <img src={image} alt={`${person.name} photo ${index + 1}`} className="h-full w-full object-cover" />
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-3xl font-bold text-[#171426]">{person.name}{person.age ? `, ${person.age}` : ''} <CheckCircle2 className="inline h-5 w-5 text-blue-500" /></h2>
              <p className="mt-2 flex items-center gap-1 text-sm text-[#706a80]"><MapPin className="h-4 w-4" />{person.location}</p>
            </div>
            <Heart className="text-fuchsia-500" />
          </div>
          <p className="mt-4 leading-7 text-[#5d586e]">{person.bio || `Hi! I’m ${person.name}. I enjoy meeting new people, exploring places, attending events, and creating memorable experiences together.`}</p>
          <div className="mt-4 space-y-2 rounded-xl border border-violet-100 bg-violet-50/50 p-3.5 text-xs text-[#5d586e]">
            {person.gender && <p><strong className="text-gray-900">Gender:</strong> {person.gender}</p>}
            {person.want_to && <p><strong className="text-gray-900">Role:</strong> {person.want_to}</p>}
            {person.email && <p><strong className="text-gray-900">Email:</strong> {person.email}</p>}
            {person.phone && <p><strong className="text-gray-900">Phone:</strong> {person.phone}</p>}
            <p><strong className="text-gray-900">Languages:</strong> {person.languages?.join(', ') || 'English, Hindi, Marathi'}</p>
            <p><strong className="text-gray-900">Interests:</strong> {person.interests?.join(', ') || person.tags.join(', ')}</p>
            <p><strong className="text-gray-900">Available:</strong> <span className="font-semibold text-emerald-700">{formatAvailability(person.availability || person.availableTime)}</span></p>
          </div>
        </div>
      </div>

      {!showBookingForm && <button type="button" onClick={() => setShowBookingForm(true)} className="mt-6 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:opacity-90">Add Book Appointment</button>}

      {showBookingForm && <form onSubmit={submitBooking} className="mt-6 grid max-w-5xl gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-5 rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm">
          <section>
            <h2 className="text-lg font-bold text-[#171426]">Book {person.name}</h2>
            <p className="mt-1 text-sm text-[#706a80]">Select the service, meeting time, and location.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {services.map((service) => (
                <button key={service.id} type="button" onClick={() => { setSelectedServiceId(service.id); setCreatedBooking(null); }} className={`rounded-xl border p-3 text-left transition ${selectedServiceId === service.id ? 'border-violet-500 bg-violet-50 ring-1 ring-violet-300' : 'border-[#e4dff0] hover:border-violet-300'}`}>
                  <span className="block text-sm font-semibold text-[#24202e]">{service.title}</span>
                  <span className="mt-1 block text-xs text-violet-700">{formatPrice(service.price)} · {service.duration || 'hourly'}</span>
                </button>
              ))}
            </div>
          </section>

          <div className="grid gap-4 sm:grid-cols-3">
            <label className="text-sm font-semibold text-[#40394f]">Date<input required type="date" min={localDate()} value={bookingDate} onChange={(event) => setBookingDate(event.target.value)} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal" /></label>
            <label className="text-sm font-semibold text-[#40394f]">Start time<input required type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal" /></label>
            <label className="text-sm font-semibold text-[#40394f]">End time<input required type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal" /></label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-semibold text-[#40394f]">Meeting type<select value={locationType} onChange={(event) => setLocationType(event.target.value)} className="mt-2 w-full rounded-lg border border-[#e4dff0] bg-white px-3 py-2.5 text-sm font-normal"><option value="in_person">In person</option><option value="online">Online</option></select></label>
            <label className="text-sm font-semibold text-[#40394f]">{locationType === 'online' ? 'Meeting link or details' : 'Meeting location'}<input value={location} onChange={(event) => setLocation(event.target.value)} placeholder={locationType === 'online' ? 'Add meeting details' : 'Enter address or venue'} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal" /></label>
          </div>

          <label className="block text-sm font-semibold text-[#40394f]">Special requirements<textarea rows="3" value={specialRequirements} onChange={(event) => setSpecialRequirements(event.target.value)} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal" placeholder="Anything the RentPeople should know before meeting?" /></label>
          <label className="block text-sm font-semibold text-[#40394f]">Note to the RentPeople<textarea rows="2" value={customerNote} onChange={(event) => setCustomerNote(event.target.value)} className="mt-2 w-full rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm font-normal" placeholder="Optional note" /></label>
        </div>

        <aside className="h-fit rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm">
          <h3 className="font-bold text-[#171426]">Booking total</h3>
          <div className="mt-4 space-y-3 text-sm text-[#5d586e]">
            <p>Duration <span className="float-right">{durationMinutes > 0 ? `${durationMinutes} min` : 'Invalid time'}</span></p>
            <p>Service price <span className="float-right">{formatPrice(price)}</span></p>
            <p>Platform fee <span className="float-right">{formatPrice(platformFee)}</span></p>
            <p className="border-t border-[#eeeaf5] pt-3 text-base font-bold text-[#24202e]">Total <span className="float-right">{formatPrice(totalAmount)}</span></p>
            <p className="text-xs text-[#8b849d]">Payment remains pending; this form does not charge a payment method.</p>
          </div>
          {!isAuthenticated() && <p className="mt-4 text-sm text-amber-700">Please <Link className="font-semibold underline" to="/login">sign in</Link> to submit a booking.</p>}
          {bookingError && <p role="alert" className="mt-4 text-sm text-red-600">{bookingError}</p>}
          {createdBooking && <div role="status" className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">Booking request saved. Reference: <strong>{createdBooking.id}</strong><Link to="/bookings" className="mt-2 block font-semibold underline">View my bookings</Link></div>}
          <button type="submit" disabled={submitting || durationMinutes <= 0 || !selectedService} className="mt-5 w-full rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 py-3 text-sm font-semibold text-white disabled:opacity-50">{submitting ? 'Submitting…' : 'Submit booking request'}</button>
        </aside>
      </form>}
    </FeaturePage>
  );
}
