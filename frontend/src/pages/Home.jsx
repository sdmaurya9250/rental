import React from 'react';
import {
  ArrowRight, Send, MapPin, Banknote, CalendarDays, Star, Shield,
  Smartphone, UserPlus, Sparkles, Inbox, Handshake, CircleDollarSign, TrendingUp,
  Clapperboard, Users, HeartHandshake, PartyPopper, ShoppingBag, Stethoscope,
  Home as HomeIcon, Plane, Theater, Dumbbell, Music, Coffee, Utensils,
  MoreHorizontal, Clock, Lock, CheckCircle2, Heart, ChevronRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import HomeHeader from '../components/HomeHeader';
import HomeFooter from '../components/HomeFooter';

/* ---------- Shared layout tokens (change here to affect every section) ---------- */
// Same left/right spacing for every section
const CONTAINER = 'w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8';
// Same (compact) top/bottom spacing for every section
const SECTION_Y = 'py-10 lg:py-12';

/* ---------- Shared section heading (same font/size/colour everywhere) ---------- */
function SectionHeading({ eyebrow, title, subtitle, className = '' }) {
  return (
    <div className={`text-center mb-8 ${className}`}>
      <span className="text-[11px] font-bold tracking-widest text-violet-700 uppercase">
        {eyebrow}
      </span>
      <h2 className="text-3xl sm:text-4xl font-black text-[#16132a] mt-2 tracking-tight">
        {title}
      </h2>
      {subtitle && (
        <p className="mx-auto mt-2 max-w-xl text-sm font-medium leading-relaxed text-gray-500">
          {subtitle}
        </p>
      )}
    </div>
  );
}

export default function Home() {
  const quickServices = [
    { icon: <Coffee className="w-5 h-5 text-pink-500" />, label: 'Coffee Partner', bg: 'bg-pink-50' },
    { icon: <Utensils className="w-5 h-5 text-amber-500" />, label: 'Café & Food', bg: 'bg-amber-50' },
    { icon: <Theater className="w-5 h-5 text-purple-500" />, label: 'Event Partner', bg: 'bg-purple-50' },
    { icon: <Plane className="w-5 h-5 text-blue-500" />, label: 'Travel Buddy', bg: 'bg-blue-50' },
    { icon: <Clapperboard className="w-5 h-5 text-emerald-500" />, label: 'Movie Buddy', bg: 'bg-emerald-50' },
    { icon: <ShoppingBag className="w-5 h-5 text-rose-500" />, label: 'Shopping Buddy', bg: 'bg-rose-50' },
    { icon: <Dumbbell className="w-5 h-5 text-teal-500" />, label: 'Gym Partner', bg: 'bg-teal-50' },
    { icon: <Music className="w-5 h-5 text-indigo-500" />, label: 'Music Jam', bg: 'bg-indigo-50' },
    { icon: <MoreHorizontal className="w-5 h-5 text-gray-500" />, label: 'More', bg: 'bg-gray-100' },
  ];

  const popularCompanions = [
    { name: 'Aarohi', age: 24, rating: 4.8, location: 'Mumbai, Andheri', image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=400' },
    { name: 'Karan', age: 26, rating: 4.6, location: 'Delhi, Connaught Place', image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=400' },
    { name: 'Priya', age: 23, rating: 4.9, location: 'Bangalore, Koramangala', image: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&q=80&w=400' },
    { name: 'Rohit', age: 27, rating: 4.7, location: 'Pune, Viman Nagar', image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=400' },
    { name: 'Neha', age: 25, rating: 4.8, location: 'Hyderabad, Banjara Hills', image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=400' },
    { name: 'Arjun', age: 28, rating: 4.6, location: 'Mumbai, Bandra', image: 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&q=80&w=400' },
  ];

  const btnBg = 'bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] hover:opacity-90';
  const services = [
    { icon: <Clapperboard className="w-5 h-5" />, title: 'Movie Partner', subtitle: 'Watch together, share laughs', price: '₹4,500', duration: '3.5 hours' },
    { icon: <Users className="w-5 h-5" />, title: 'In-Person Meeting', subtitle: 'Face-to-face meeting and conversation', price: '₹2,000', duration: '1 hour' },
    { icon: <HeartHandshake className="w-5 h-5" />, title: 'Elder Care', subtitle: 'Senior assistance & daily support', price: '₹1,000', duration: '1 hour' },
    { icon: <Users className="w-5 h-5" />, title: 'Hangingout', subtitle: 'Casual social time together', price: '₹1,500', duration: '1 hour' },
    { icon: <PartyPopper className="w-5 h-5" />, title: 'Clubbing', subtitle: 'Nightlife & party assistance', price: '₹4,500', duration: '3 hours' },
    { icon: <ShoppingBag className="w-5 h-5" />, title: 'Shopping Buddy', subtitle: 'Groceries, errands, or shopping', price: '₹2,000', duration: '1 hour' },
    { icon: <Stethoscope className="w-5 h-5" />, title: 'Medical Support', subtitle: 'Hospital & appointment assistance', price: '₹2,000', duration: '1 hour' },
    { icon: <HomeIcon className="w-5 h-5" />, title: 'Domestic Help', subtitle: 'Light support & organizing', price: '₹2,000', duration: '1 hour' },
  ];

  const whyJoinFeatures = [
    { icon: <MapPin className="w-5 h-5 text-violet-600" />, title: 'City-Based Discovery', description: 'Let visitors discover profiles based on their city and preferred location.' },
    { icon: <Banknote className="w-5 h-5 text-violet-600" />, title: 'Set Your Rate', description: "Display the rate you choose according to the platform's applicable rules." },
    { icon: <CalendarDays className="w-5 h-5 text-violet-600" />, title: 'Control Availability', description: 'Keep your availability updated and accept requests that fit your schedule.' },
    { icon: <Star className="w-5 h-5 text-amber-500 fill-amber-400" />, title: 'Reviews & Ratings', description: 'Approved reviews and ratings can help visitors understand your profile and experience.' },
    { icon: <Shield className="w-5 h-5 text-violet-600" />, title: 'Profile Verification', description: 'Build trust with complete profile information and applicable verification features.' },
    { icon: <Smartphone className="w-5 h-5 text-violet-600" />, title: 'Booking Requests', description: 'Receive booking requests through the platform and review the details before accepting.' },
  ];

  const stepProcess = [
    { step: '01', icon: <UserPlus className="w-5 h-5 text-violet-600" />, title: 'Create Your Account', description: 'Start with your basic details and create your account in a few simple steps.' },
    { step: '02', icon: <Sparkles className="w-5 h-5 text-violet-600" />, title: 'Build Your Profile', description: 'Add your photo, city, age, rate, availability and other profile information.' },
    { step: '03', icon: <Inbox className="w-5 h-5 text-violet-600" />, title: 'Receive Requests', description: 'People can discover your profile and send booking or contact requests.' },
    { step: '04', icon: <Handshake className="w-5 h-5 text-violet-600" />, title: 'Accept Bookings', description: 'Review each request and decide which bookings fit your schedule.' },
    { step: '05', icon: <CircleDollarSign className="w-5 h-5 text-violet-600" />, title: 'Complete & Earn', description: 'Complete accepted bookings and keep track of your earnings from your profile.' },
    { step: '06', icon: <TrendingUp className="w-5 h-5 text-violet-600" />, title: 'Track Your Progress', description: 'Keep your profile updated and build trust through reviews and completed activity.' },
  ];

  return (
    <div className="min-h-screen bg-[#fcfaff] text-[#16132a] font-sans flex flex-col selection:bg-violet-100 selection:text-violet-900 overflow-x-hidden relative">

      {/* Soft Glow Backgrounds */}
      <div className="absolute top-[-5%] left-[-5%] w-[500px] h-[500px] bg-pink-100/40 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-[5%] right-[-5%] w-[550px] h-[550px] bg-violet-200/30 rounded-full blur-3xl pointer-events-none" />

      <HomeHeader />

      {/* HERO */}
      <section className={`relative z-10 ${CONTAINER} pt-4 pb-10 lg:pb-12`}>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-6 space-y-6">
            <div className="inline-flex items-center space-x-2 text-[11px] font-bold tracking-widest text-pink-600 uppercase">
              <span>MEET</span><span>•</span><span>HANGOUT</span><span>•</span><span>EXPLORE</span><span>•</span><span>EARN</span>
            </div>

            <h1 className="text-4xl sm:text-5xl xl:text-6xl font-black text-[#16132a] tracking-tight leading-[1.12]">
              Find Your Perfect <br />
              <span className="bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] bg-clip-text text-transparent">
                Rental Companion
              </span> <br />
              for Any Occasion
            </h1>

            <p className="text-gray-500 text-sm sm:text-base max-w-lg leading-relaxed font-normal">
              Safe, verified and trusted companions for events, travel, dining, movies and more. Choose your service, location and time.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-1">
              <Link
                to="/browse"
                className="inline-flex items-center px-7 py-3.5 bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] hover:opacity-95 text-white font-semibold text-sm rounded-full shadow-lg shadow-violet-400/25 transition-all duration-200 group"
              >
                Find a Companion
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/login?mode=register"
                className="inline-flex items-center px-7 py-3.5 bg-white hover:bg-gray-50 text-gray-800 font-semibold text-sm rounded-full border border-gray-200 shadow-sm transition-all duration-200"
              >
                Become a Companion
              </Link>
            </div>

            <div className="grid grid-cols-3 gap-4 pt-6 border-t border-gray-100 max-w-md">
              <div>
                <p className="text-2xl font-black text-[#16132a]">10K+</p>
                <p className="text-xs text-gray-500 font-medium">Verified Members</p>
              </div>
              <div>
                <p className="text-2xl font-black text-[#16132a]">5K+</p>
                <p className="text-xs text-gray-500 font-medium">Successful Bookings</p>
              </div>
              <div>
                <p className="text-2xl font-black text-[#16132a] flex items-center gap-1">
                  4.8 <Star className="w-4 h-4 text-amber-400 fill-amber-400 inline" />
                </p>
                <p className="text-xs text-gray-500 font-medium">Average Rating</p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-6 relative flex justify-center lg:justify-end">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[380px] h-[380px] sm:w-[450px] sm:h-[450px] bg-gradient-to-tr from-pink-200/60 to-violet-200/60 rounded-full blur-2xl -z-10" />

            <div className="absolute top-2 left-10 hidden sm:block text-pink-400 text-xs font-handwriting -rotate-12">
              <span className="text-pink-500 text-lg">✦</span> Good Company Brighter Moments
            </div>
            <Heart className="w-6 h-6 text-pink-400 fill-pink-300 absolute top-0 right-1/3 animate-bounce hidden sm:block" />

            <div className="relative rounded-3xl overflow-hidden shadow-2xl max-w-md border-4 border-white">
              <img
                src="Joyful South Asian Couple Portrait.png"
                alt="Rental Companion Couple"
                className="w-full h-[400px] sm:h-[460px] object-cover"
              />
            </div>

            <div className="absolute right-[-10px] sm:right-[-20px] top-1/2 -translate-y-1/2 bg-white/95 backdrop-blur-md rounded-2xl p-4 shadow-xl border border-gray-100 w-44 sm:w-52 space-y-3 z-20">
              {[
                { i: <Clock className="w-4 h-4" />, t: 'Flexible Schedule', c: 'bg-pink-100 text-pink-600' },
                { i: <Heart className="w-4 h-4" />, t: 'Your Choice', c: 'bg-purple-100 text-purple-600' },
                { i: <Lock className="w-4 h-4" />, t: 'Safe & Secure', c: 'bg-indigo-100 text-indigo-600' },
                { i: <CheckCircle2 className="w-4 h-4" />, t: 'Verified Profiles', c: 'bg-emerald-100 text-emerald-600' },
              ].map((f) => (
                <div key={f.t} className="flex items-center space-x-2.5">
                  <div className={`p-2 rounded-lg ${f.c}`}>{f.i}</div>
                  <span className="text-xs font-bold text-gray-800">{f.t}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick services bar */}
        <div className="mt-10 w-full bg-white/80 backdrop-blur-md border border-gray-100 rounded-3xl p-4 sm:p-6 shadow-xl shadow-purple-500/5">
          <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-9 gap-3 text-center">
            {quickServices.map((srv, index) => (
              <div
                key={index}
                className="flex flex-col items-center justify-center p-2 rounded-2xl hover:bg-violet-50/60 cursor-pointer transition duration-200 group"
              >
                <div className={`w-12 h-12 rounded-2xl ${srv.bg} flex items-center justify-center mb-2 shadow-sm group-hover:scale-110 transition-transform`}>
                  {srv.icon}
                </div>
                <span className="text-[11px] font-semibold text-gray-700 group-hover:text-violet-600 line-clamp-1">
                  {srv.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* POPULAR COMPANIONS */}
      <section className={`relative z-10 w-full bg-gradient-to-b from-pink-50/40 via-white to-pink-50/20 ${SECTION_Y}`}>
        <div className={CONTAINER}>
          <SectionHeading
            eyebrow="Top Rated"
            title="Popular Companions"
            subtitle="Discover verified companions near you."
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {popularCompanions.map((person, index) => (
              <div
                key={index}
                className="bg-white rounded-2xl p-2.5 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100 flex flex-col group/card cursor-pointer"
              >
                <div className="relative rounded-xl overflow-hidden h-44 w-full">
                  <img
                    src={person.image}
                    alt={person.name}
                    className="w-full h-full object-cover group-hover/card:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute bottom-2 left-2 bg-[#00d084] text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 shadow-sm">
                    <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                    Online
                  </div>
                  <button className="absolute top-2 right-2 w-7 h-7 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center text-pink-500 hover:scale-110 shadow-sm transition-transform">
                    <Heart className="w-4 h-4 text-pink-500" />
                  </button>
                </div>

                <div className="pt-3 pb-1 px-1">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-black text-[#16132a]">
                      {person.name}, <span className="font-semibold text-gray-700">{person.age}</span>
                    </h3>
                    <div className="flex items-center gap-0.5 text-xs font-bold text-gray-800">
                      <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                      <span>{person.rating}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] text-gray-400 font-medium mt-1">
                    <MapPin className="w-3 h-3 text-gray-400 shrink-0" />
                    <span className="truncate">{person.location}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 flex justify-center">
            <Link
              to="/browse"
              className="px-6 py-2.5 rounded-full border border-pink-200 text-pink-600 hover:bg-pink-50 font-semibold text-xs transition-all flex items-center gap-1 shadow-sm"
            >
              View All <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* OUR SERVICES */}
      <section id="services" className={`relative z-10 w-full bg-white/40 ${SECTION_Y}`}>
        <div className={CONTAINER}>
          <SectionHeading
            eyebrow="What We Offer"
            title="Our Services"
            subtitle="Choose from our wide range of professional support services designed to make every experience comfortable and enjoyable."
          />

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
            {services.map((item, idx) => (
              <div
                key={idx}
                className="group relative flex min-h-[195px] flex-col overflow-hidden rounded-2xl border border-gray-100 bg-white p-3.5 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-violet-200 hover:shadow-xl"
              >
                <div className="flex items-start justify-between">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-violet-100 bg-violet-50 text-violet-600 transition-all duration-300 group-hover:bg-[#7a0ff0] group-hover:text-white">
                    {item.icon}
                  </div>
                  <span className="text-[9px] font-bold text-gray-300">
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                </div>

                <div className="mt-3 flex-1">
                  <h3 className="line-clamp-2 min-h-[40px] text-sm font-extrabold leading-5 text-[#16132a]">{item.title}</h3>
                  <p className="mt-1 line-clamp-2 min-h-[32px] text-[10px] font-medium leading-4 text-gray-400">{item.subtitle}</p>
                </div>

                <div className="mt-3 flex items-center">
                  <span className="text-sm font-black text-violet-700">{item.price}</span>
                  <span className="ml-1 text-[9px] font-semibold text-gray-400">/ {item.duration}</span>
                </div>

                <button
                  type="button"
                  className={`mt-3 flex w-full items-center justify-center rounded-lg py-2 text-[10px] font-bold text-white shadow-sm transition-all duration-200 hover:shadow-md active:scale-95 ${btnBg}`}
                >
                  Book Now
                  <span className="ml-1 transition-transform duration-200 group-hover:translate-x-0.5">→</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WHY JOIN */}
      <section id="why-join" className={`relative z-10 w-full bg-gradient-to-b from-[#f8f6ff] via-violet-50/30 to-[#f8f6ff] ${SECTION_Y}`}>
        <div className={CONTAINER}>
          <SectionHeading eyebrow="Why Join" title="Everything You Need to Get Started" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 auto-rows-fr">
            {whyJoinFeatures.map((item, index) => (
              <div
                key={index}
                className="bg-white/90 backdrop-blur-sm border border-violet-100/80 rounded-3xl p-6 h-full shadow-sm hover:shadow-md hover:border-violet-200 transition-all duration-300 flex flex-col"
              >
                <div className="w-11 h-11 rounded-2xl bg-violet-50/80 flex items-center justify-center mb-4">{item.icon}</div>
                <h3 className="text-lg font-bold text-[#16132a] mb-2">{item.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" className={`relative z-10 w-full ${SECTION_Y}`}>
        <div className={CONTAINER}>
          <SectionHeading eyebrow="How It Works" title="Get Started in 6 Simple Steps" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 auto-rows-fr">
            {stepProcess.map((item, index) => (
              <div
                key={index}
                className="bg-white/90 backdrop-blur-sm border border-violet-100/80 rounded-3xl p-6 h-full shadow-sm hover:shadow-md transition-all duration-300 flex flex-col"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-2xl bg-violet-50/80 flex items-center justify-center">{item.icon}</div>
                  <span className="text-2xl font-black text-violet-200/90 tracking-tight">{item.step}</span>
                </div>
                <h3 className="text-base font-bold text-[#16132a] mb-2">{item.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Floating Telegram Button */}
      <a
        href="https://t.me"
        target="_blank"
        rel="noreferrer"
        className="fixed bottom-6 right-6 z-50 bg-[#22c55e] hover:bg-[#16a34a] text-white text-xs font-semibold px-4 py-2.5 rounded-full flex items-center space-x-2 shadow-lg hover:shadow-xl transition duration-200"
      >
        <Send className="w-4 h-4 fill-white" />
        <span>Telegram</span>
      </a>

      <HomeFooter />
    </div>
  );
}
