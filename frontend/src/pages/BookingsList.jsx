import React, { useState } from 'react';

const BOOKINGS = [
  {
    id: 1,
    name: 'Kiara',
    age: 24,
    date: '14 Sep 2025',
    time: '6:00 PM',
    duration: '3 Hours',
    status: 'Confirmed', // Confirmed | Pending | Completed | Cancelled
    image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop',
    type: 'Upcoming'
  },
  {
    id: 2,
    name: 'Rohan',
    age: 26,
    date: '20 Sep 2025',
    time: '5:00 PM',
    duration: 'Full Day',
    status: 'Pending',
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=200&auto=format&fit=crop',
    type: 'Upcoming'
  },
  {
    id: 3,
    name: 'Meera',
    age: 25,
    date: '28 Sep 2025',
    time: '7:00 PM',
    duration: '2 Hours',
    status: 'Completed',
    image: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?q=80&w=200&auto=format&fit=crop',
    type: 'Completed'
  }
];

export default function BookingsList() {
  const [activeTab, setActiveTab] = useState('Upcoming');

  const tabs = ['Upcoming', 'Completed', 'Cancelled'];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Confirmed':
        return (
          <span className="px-4 py-1.5 rounded-full text-xs font-semibold bg-emerald-900/40 text-emerald-400 border border-emerald-500/40">
            Confirmed
          </span>
        );
      case 'Pending':
        return (
          <span className="px-4 py-1.5 rounded-full text-xs font-semibold bg-amber-900/40 text-amber-400 border border-amber-500/40">
            Pending
          </span>
        );
      case 'Completed':
        return (
          <span className="px-4 py-1.5 rounded-full text-xs font-semibold bg-emerald-900/40 text-emerald-400 border border-emerald-500/40">
            Completed
          </span>
        );
      case 'Cancelled':
        return (
          <span className="px-4 py-1.5 rounded-full text-xs font-semibold bg-red-900/40 text-red-400 border border-red-500/40">
            Cancelled
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <main className="flex-1 bg-[#f8f6ff] p-6 lg:p-8 overflow-y-auto space-y-8 text-[#171426]">
      {/* Section Title & Tabs Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#171426] mb-5">My Bookings</h1>
        
        <div className="flex items-center justify-between border-b border-gray-800/80 pb-4">
          <div className="flex items-center space-x-3 bg-white p-1.5 rounded-xl border border-[#e7e1f2] shadow-sm">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-2 rounded-lg text-sm font-medium transition duration-200 ${
                  activeTab === tab
                    ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-md'
                    : 'text-[#706a80] hover:text-violet-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <button className="text-sm text-pink-500 font-semibold hover:underline">
            View All
          </button>
        </div>
      </div>

      {/* Bookings List Cards */}
      <div className="space-y-4">
        {BOOKINGS.map((booking) => (
          <div
            key={booking.id}
            className="bg-white border border-[#e7e1f2] hover:border-violet-300 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4 transition duration-200 shadow-sm"
          >
            {/* Person Profile Info */}
            <div className="flex items-center space-x-4 w-full sm:w-auto">
              <img
                src={booking.image}
                alt={booking.name}
                className="w-16 h-16 rounded-xl object-cover border border-gray-700"
              />
              <div>
                <h3 className="text-base font-bold text-[#24202e]">
                  {booking.name}, {booking.age}
                </h3>
                <p className="text-xs text-[#706a80] mt-1">
                  {booking.date} &nbsp;•&nbsp; {booking.time} &nbsp;•&nbsp; {booking.duration}
                </p>
              </div>
            </div>

            {/* Status & Action */}
            <div className="flex items-center space-x-5 w-full sm:w-auto justify-between sm:justify-end">
              {getStatusBadge(booking.status)}

              <button className="px-5 py-2 text-xs font-semibold text-pink-500 border border-pink-500/50 rounded-lg hover:bg-pink-500 hover:text-white transition duration-200">
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom Hero Banner */}
      <div className="relative rounded-2xl overflow-hidden min-h-[220px] flex items-center p-8 bg-gradient-to-r from-orange-900/60 via-pink-900/40 to-purple-900/60 border border-pink-500/20">
        {/* Banner Silhouette Overlay */}
        <img
          src="https://images.unsplash.com/photo-1529156069898-49953e39b3ac?q=80&w=1200&auto=format&fit=crop"
          alt="People banner background"
          className="absolute inset-0 w-full h-full object-cover mix-blend-overlay opacity-40"
        />

        <div className="relative z-10">
          <h2 className="text-3xl md:text-4xl font-serif italic text-white tracking-wide flex items-center space-x-2">
            <span>People Make</span>
          </h2>
          <h2 className="text-3xl md:text-4xl font-serif italic text-white tracking-wide flex items-center space-x-3 mt-1">
            <span>Life Better</span>
            <span className="text-pink-500 not-italic text-2xl">♥</span>
          </h2>
        </div>
      </div>
    </main>
  );
}
