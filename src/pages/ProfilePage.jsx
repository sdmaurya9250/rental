import React, { useState } from 'react';
import { CheckCircle2, Heart, MapPin } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import FeaturePage from '../components/FeaturePage';
import { findPerson, formatPrice } from '../data/people';

export default function ProfilePage() {
  const person = findPerson(useParams().personId);

  // Fallback gallery images using person.image as main photo
  const galleryImages = person?.images || [
    person?.image,
    'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&q=80&w=800',
    'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&q=80&w=800',
    'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=800',
  ];

  const [activeImage, setActiveImage] = useState(galleryImages[0]);
  const [selectedService, setSelectedService] = useState(null);

  // Default services list mapped dynamically
  const services = person?.services || [
    { title: 'Coffee Partner', price: person?.rate || 1500, duration: '1 hr' },
    { title: 'Cafe & Food Partner', price: (person?.rate || 1500) * 1.5, duration: '2 hrs' },
    { title: 'Event Partner', price: (person?.rate || 1500) * 2.5, duration: '3 hrs' },
    { title: 'Travel Buddy', price: (person?.rate || 1500) * 4, duration: 'Full Day' },
  ];

  if (!person) return <div>Person not found</div>;

  return (
    <FeaturePage title="Profile">
      <Link to="/browse" className="text-sm font-medium text-violet-700 hover:underline">
        ← Back to browse
      </Link>

      <div className="mt-5 grid max-w-4xl gap-6 rounded-2xl border border-[#e7e1f2] bg-white p-5 shadow-sm md:grid-cols-[300px_1fr]">
        
        {/* Left Side: Photo Gallery */}
        <div className="space-y-3">
          <div className="relative h-80 w-full overflow-hidden rounded-xl bg-gray-100">
            <img 
              src={activeImage || person.image} 
              alt={person.name} 
              className="h-full w-full object-cover" 
            />
            <span className="absolute left-3 top-3 inline-block rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
              ● Online
            </span>
          </div>

          {/* Image Thumbnails */}
          <div className="flex gap-2 overflow-x-auto pb-1">
            {galleryImages.map((img, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setActiveImage(img)}
                className={`h-14 w-14 shrink-0 overflow-hidden rounded-lg border-2 transition-all ${
                  (activeImage || person.image) === img ? 'border-violet-600' : 'border-transparent opacity-75 hover:opacity-100'
                }`}
              >
                <img src={img} alt={`${person.name} thumbnail ${idx}`} className="h-full w-full object-cover" />
              </button>
            ))}
          </div>
        </div>

        {/* Right Side: Profile Info & Pricing */}
        <div className="flex flex-col justify-between">
          <div>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-3xl font-bold text-[#171426]">
                  {person.name}, {person.age} <CheckCircle2 className="inline h-5 w-5 text-blue-500" />
                </h2>
                <p className="mt-2 flex items-center gap-1 text-sm text-[#706a80]">
                  <MapPin className="h-4 w-4" />{person.location}
                </p>
              </div>
              <button type="button" className="p-1">
                <Heart className="text-fuchsia-500 hover:fill-fuchsia-500 transition" />
              </button>
            </div>

            <p className="mt-4 leading-7 text-[#5d586e]">
              {person.bio || `Hi! I’m ${person.name}. I enjoy meeting new people, exploring places, attending events, and creating memorable experiences together.`}
            </p>

            {/* Languages, Interests & Availability Info */}
            <div className="mt-4 space-y-2 rounded-xl border border-violet-100 bg-violet-50/50 p-3.5 text-xs text-[#5d586e]">
              <p><strong className="text-gray-900">🗣️ Languages:</strong> {person.languages?.join(', ') || 'English, Hindi, Marathi'}</p>
              <p><strong className="text-gray-900">🎨 Interests:</strong> {person.interests?.join(', ') || 'Travel, Movies, Food, Fitness'}</p>
              <p><strong className="text-gray-900">📅 Available:</strong> <span className="text-emerald-700 font-semibold">{person.availability || 'Mon, Tue, Thu, Fri (10 AM - 8 PM)'}</span></p>
            </div>

            {/* Pricing Options */}
            <div className="mt-5">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Available Services & Pricing</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {services.map((service, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedService(service)}
                    className={`flex items-center justify-between p-2.5 rounded-xl border cursor-pointer transition ${
                      selectedService?.title === service.title
                        ? 'border-violet-600 bg-violet-50'
                        : 'border-gray-200 bg-white hover:border-violet-300'
                    }`}
                  >
                    <div>
                      <p className="text-xs font-bold text-gray-800">{service.title}</p>
                      <span className="text-[11px] text-violet-600 font-medium">{service.duration}</span>
                    </div>
                    <span className="text-sm font-bold text-violet-700">{formatPrice(service.price)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Tags */}
            <div className="mt-4 flex flex-wrap gap-2">
              {person.tags.map(tag => (
                <span key={tag} className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Working Link Button */}
          <Link
            to={`/book/${person.id}${selectedService ? `?service=${encodeURIComponent(selectedService.title)}` : ''}`}
            className="mt-6 inline-flex w-full items-center justify-center rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-6 py-3 text-center font-semibold text-white shadow-lg shadow-violet-200 hover:opacity-95 transition"
          >
            {selectedService ? `Book ${selectedService.title} (${formatPrice(selectedService.price)})` : 'Book now'}
          </Link>
        </div>

      </div>
    </FeaturePage>
  );
}