import React, { useMemo, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import FeaturePage from '../components/FeaturePage';
import { findPerson, formatPrice } from '../data/people';
import { 
  Coffee, 
  Utensils, 
  Calendar, 
  Plane, 
  Check, 
  ShieldCheck, 
  Clock, 
  Lock, 
  Info,
  ChevronRight,
  MapPin
} from 'lucide-react';

function hoursBetween(start, end) {
  const [sh, sm] = start.split(':').map(Number);
  const [eh, em] = end.split(':').map(Number);
  return Math.max(0, (eh * 60 + em - sh * 60 - sm) / 60);
}

export default function AvailabilityPage() {
  const person = findPerson(useParams().personId) || {
    id: 'kiara',
    name: 'Kiara',
    age: 24,
    location: 'Mumbai, India',
    rate: 1200,
    image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=800',
    tags: ['Friendly', 'Fun', 'Good Listener', 'Travel Lover', 'Event Partner'],
  };

  const navigate = useNavigate();
  const location = useLocation();

  const queryParams = new URLSearchParams(location.search);
  const initialService = queryParams.get('service') || location.state?.service;

  // Available services list with icons matching your design
  const services = person?.services || [
    { id: 'coffee', title: 'Coffee Partner', price: person?.rate || 1200, duration: '1 hr', hoursNeeded: 1, icon: Coffee },
    { id: 'food', title: 'Café & Food Partner', price: (person?.rate || 1200) * 1.5, duration: '2 hrs', hoursNeeded: 2, icon: Utensils },
    { id: 'event', title: 'Event Partner', price: (person?.rate || 1200) * 2.5, duration: '3 hrs', hoursNeeded: 3, icon: Calendar },
    { id: 'travel', title: 'Travel Buddy', price: (person?.rate || 1200) * 4, duration: 'Full Day', hoursNeeded: 6, icon: Plane },
  ];

  const [selectedServiceTitle, setSelectedServiceTitle] = useState(
    initialService || services[0].title
  );
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [startTime, setStartTime] = useState('12:00');
  const [endTime, setEndTime] = useState('14:00');

  const hourlySlots = Array.from({ length: 13 }, (_, index) => index + 8);
  const hours = useMemo(() => hoursBetween(startTime, endTime), [startTime, endTime]);
  const valid = hours > 0;

  const activeService = services.find((s) => s.title === selectedServiceTitle) || services[0];
  
  // Calculate pricing breakdown
  const serviceCharge = activeService.price * (hours / (activeService.hoursNeeded || 1));
  const platformFee = Math.round(serviceCharge * 0.125);
  const totalAmount = serviceCharge + platformFee;

  const handleServiceSelect = (service) => {
    setSelectedServiceTitle(service.title);
    const startHour = parseInt(startTime.split(':')[0], 10);
    const newEndHour = Math.min(20, startHour + service.hoursNeeded);
    setEndTime(`${String(newEndHour).padStart(2, '0')}:00`);
  };

  const continueBooking = () => {
    if (valid) {
      navigate('/booking-summary', {
        state: {
          personId: person.id,
          service: activeService.title,
          price: totalAmount,
          date,
          startTime,
          endTime,
          hours,
        },
      });
    }
  };

  return (
    <FeaturePage 
      title="Choose service, date & time" 
      subtitle={`Set when you would like to meet ${person.name}.`}
    >
      <Link to={`/people/${person.id}`} className="text-sm font-medium text-violet-700 hover:underline">
        ← Back to profile
      </Link>

      <div className="mt-5 grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        {/* Left Form Column (Steps 1, 2, 3) */}
        <div className="lg:col-span-7 space-y-4">
          
          {/* STEP 1: Service Category */}
          <div className="rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-600 text-xs font-bold text-white">
                  1
                </span>
                <div>
                  <h3 className="text-sm font-bold text-[#171426]">Select Service Category</h3>
                  <p className="text-xs text-gray-500">Choose the type of service you need</p>
                </div>
              </div>

              {/* Dropdown */}
              <select
                value={selectedServiceTitle}
                onChange={(e) => {
                  const s = services.find((srv) => srv.title === e.target.value);
                  if (s) handleServiceSelect(s);
                }}
                className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-700 outline-none focus:ring-2 focus:ring-violet-300"
              >
                {services.map((service) => (
                  <option key={service.title} value={service.title}>
                    {service.title} — {formatPrice(service.price)} · {service.duration}
                  </option>
                ))}
              </select>
            </div>

            {/* Visual Icon Cards Grid */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {services.map((service) => {
                const isSelected = selectedServiceTitle === service.title;
                const IconComponent = service.icon;
                return (
                  <button
                    key={service.title}
                    type="button"
                    onClick={() => handleServiceSelect(service)}
                    className={`relative flex flex-col items-center justify-center rounded-xl border p-3.5 text-center transition-all ${
                      isSelected
                        ? 'border-violet-600 bg-violet-50/60 ring-2 ring-violet-600/20'
                        : 'border-gray-100 bg-gray-50/40 hover:border-violet-200 hover:bg-white'
                    }`}
                  >
                    {isSelected && (
                      <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-violet-600 text-[10px] text-white">
                        <Check className="h-3 w-3 stroke-[3]" />
                      </span>
                    )}
                    <IconComponent className={`h-6 w-6 mb-1.5 ${isSelected ? 'text-violet-600' : 'text-gray-400'}`} />
                    <p className="text-xs font-bold text-gray-800">{service.title}</p>
                    <p className="text-[11px] text-gray-500 mt-0.5">
                      {formatPrice(service.price)} · {service.duration}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* STEP 2: Date Picker */}
          <div className="rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3 mb-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-600 text-xs font-bold text-white">
                2
              </span>
              <div>
                <h3 className="text-sm font-bold text-[#171426]">Select Date</h3>
                <p className="text-xs text-gray-500">Choose your preferred date</p>
              </div>
            </div>
            <input
              type="date"
              value={date}
              min={new Date().toISOString().slice(0, 10)}
              onChange={(e) => setDate(e.target.value)}
              className="w-full rounded-xl border border-[#e4dff0] bg-white px-3.5 py-3 text-sm font-medium text-gray-800 outline-none focus:ring-2 focus:ring-violet-300"
            />
          </div>

          {/* STEP 3: Available Time */}
          <div className="rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3 mb-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-violet-600 text-xs font-bold text-white">
                3
              </span>
              <div>
                <h3 className="text-sm font-bold text-[#171426]">Available time</h3>
                <p className="text-xs text-gray-500">Select start and end time</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-gray-500 mb-1 block">From</label>
                <select
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="w-full rounded-xl border border-[#e4dff0] bg-white px-3 py-2.5 text-sm font-medium text-gray-800 outline-none focus:ring-2 focus:ring-violet-300"
                >
                  {hourlySlots.map((hour) => (
                    <option key={hour} value={`${String(hour).padStart(2, '0')}:00`}>
                      {hour > 12 ? hour - 12 : hour}:00 {hour >= 12 ? 'PM' : 'AM'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-500 mb-1 block">To</label>
                <select
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="w-full rounded-xl border border-[#e4dff0] bg-white px-3 py-2.5 text-sm font-medium text-gray-800 outline-none focus:ring-2 focus:ring-violet-300"
                >
                  {hourlySlots.map((hour) => (
                    <option key={hour} value={`${String(hour).padStart(2, '0')}:00`}>
                      {hour > 12 ? hour - 12 : hour}:00 {hour >= 12 ? 'PM' : 'AM'}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Selected Booking Info Notice */}
          <div className="flex items-center gap-3 rounded-2xl border border-violet-100 bg-violet-50/70 p-4 text-xs text-violet-950">
            <Info className="h-5 w-5 shrink-0 text-violet-600" />
            <div>
              <p className="font-bold">Selected booking</p>
              <p className="mt-0.5">
                {activeService.title} ({activeService.duration}) · {hours} hours slot ·{' '}
                <strong>{formatPrice(serviceCharge)} total</strong>
              </p>
            </div>
          </div>

          {/* Continue Button */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={continueBooking}
              disabled={!valid}
              className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-violet-600 hover:bg-violet-700 py-3.5 px-6 font-semibold text-white shadow-md transition disabled:cursor-not-allowed disabled:opacity-50"
            >
              Continue to booking <ChevronRight className="h-4 w-4" />
            </button>
          </div>
          <p className="flex items-center gap-1.5 text-xs text-gray-400">
            <Lock className="h-3.5 w-3.5" /> You can review all details before payment. Your information is safe with us.
          </p>
        </div>

        {/* Right Side: Booking Summary Preview Card */}
        <div className="lg:col-span-5 rounded-2xl border border-violet-200 bg-white p-5 shadow-sm space-y-5">
          <div className="rounded-xl bg-violet-700 p-4 text-white flex items-center justify-between">
            <div>
              <h3 className="font-bold text-base">Booking summary</h3>
              <p className="text-xs text-violet-200">Review your selection</p>
            </div>
            <div className="flex items-center gap-1 bg-white/10 px-2.5 py-1 rounded-full text-[11px]">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" /> 100% Secure
            </div>
          </div>

          {/* Person Profile Snippet */}
          <div className="flex items-center gap-3 border-b border-gray-100 pb-4">
            <div className="relative h-14 w-14 shrink-0 overflow-hidden rounded-xl bg-gray-100">
              <img src={person.image} alt={`${person.name} profile`} width="320" height="320" loading="lazy" className="h-full w-full object-cover" />
              <span className="absolute bottom-1 right-1 h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-white"></span>
            </div>
            <div>
              <h4 className="font-bold text-gray-900 text-sm flex items-center gap-1">
                {person.name}, {person.age}
                <Check className="h-3.5 w-3.5 text-blue-500 stroke-[3]" />
              </h4>
              <p className="text-xs text-gray-500 flex items-center gap-0.5">
                <MapPin className="h-3 w-3" /> {person.location}
              </p>
              <div className="flex flex-wrap gap-1 mt-1.5">
                {person.tags?.slice(0, 3).map((tag) => (
                  <span key={tag} className="rounded-full bg-violet-50 px-2 py-0.5 text-[10px] text-violet-700 font-medium">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Booking Details Table */}
          <div>
            <div className="flex items-center justify-between text-xs font-bold text-gray-900 mb-2">
              <span>Booking details</span>
              <button className="text-violet-600 hover:underline font-semibold">Edit</button>
            </div>
            <div className="space-y-2.5 text-xs text-gray-600 bg-gray-50/70 p-3.5 rounded-xl border border-gray-100">
              <div className="flex justify-between">
                <span className="text-gray-500">Service</span>
                <span className="font-medium text-gray-900">{activeService.title}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Date</span>
                <span className="font-medium text-gray-900">{date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Start time</span>
                <span className="font-medium text-gray-900">{startTime} PM</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">End time</span>
                <span className="font-medium text-gray-900">{endTime} PM</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Duration</span>
                <span className="font-medium text-gray-900">{hours} hours</span>
              </div>
            </div>
          </div>

          {/* Price Breakdown */}
          <div className="border-t border-gray-100 pt-4 space-y-2 text-xs">
            <p className="font-bold text-gray-900 mb-2">Price details</p>
            <div className="flex justify-between text-gray-600">
              <span>Service charge</span>
              <span>{formatPrice(serviceCharge)}</span>
            </div>
            <div className="flex justify-between text-gray-600">
              <span className="flex items-center gap-1">
                Platform fee <Info className="h-3 w-3 text-gray-400" />
              </span>
              <span>{formatPrice(platformFee)}</span>
            </div>
            <div className="flex justify-between border-t border-gray-100 pt-3 text-sm font-bold text-gray-900">
              <span>Total amount</span>
              <span className="text-violet-700 text-base">{formatPrice(totalAmount)}</span>
            </div>
          </div>

          {/* Proceed Button */}
          <button
            type="button"
            onClick={continueBooking}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-violet-600 hover:bg-violet-700 py-3.5 text-xs font-semibold text-white shadow transition"
          >
            <Lock className="h-3.5 w-3.5" /> Proceed to payment <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>

      </div>
    </FeaturePage>
  );
}
