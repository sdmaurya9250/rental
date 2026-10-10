import React, { useState } from 'react';
import { Phone, Mail, MapPin, Clock, Send, User, MessageSquare } from 'lucide-react';
import HomeHeader from '../components/HomeHeader';
import HomeFooter from '../components/HomeFooter';
import Seo from '../components/Seo';

const ContactPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Form Submitted:', formData);
    // Add your form submission logic here
  };

  const contactDetails = [
    {
      id: 1,
      title: 'Phone',
      value: '8796371910',
      subtext: 'Mon - Sat, 10:00 AM - 6:00 PM',
      icon: Phone,
      bgColor: 'bg-pink-100',
      iconColor: 'text-pink-600',
    },
    {
      id: 2,
      title: 'Email',
      value: 'help@kopartner.in',
      subtext: 'Response within 24 hours',
      icon: Mail,
      bgColor: 'bg-purple-100',
      iconColor: 'text-purple-600',
    },
    {
      id: 3,
      title: 'Location',
      value: 'Serving major cities across India',
      subtext: '',
      icon: MapPin,
      bgColor: 'bg-pink-100',
      iconColor: 'text-pink-600',
    },
    {
      id: 4,
      title: 'Business Hours',
      value: 'Monday - Saturday',
      subtext: '10:00 AM - 6:00 PM',
      icon: Clock,
      bgColor: 'bg-purple-100',
      iconColor: 'text-purple-600',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50/50 font-sans">
      <HomeHeader />
      <Seo title="Contact RentCoPartner Support" description="Contact RentCoPartner for questions about your account, companion bookings, payments or platform support. Our team is available Monday through Saturday." />
      <main className="relative overflow-hidden px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
      {/* Background Soft Glow Circles */}
      <div className="absolute -top-24 -left-24 w-96 h-96 bg-pink-100/60 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-purple-100/50 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 mx-auto max-w-6xl">
        {/* Header Section */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-50 text-purple-600 text-xs font-semibold uppercase tracking-wider mb-3">
            <span className="w-8 h-[1px] bg-purple-300"></span>
            CONTACT US
            <span className="w-8 h-[1px] bg-purple-300"></span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight mb-3">
            Get in <span className="bg-gradient-to-r from-purple-600 to-pink-500 bg-clip-text text-transparent">Touch</span>
          </h1>
          <p className="text-slate-500 text-sm sm:text-base max-w-2xl mx-auto">
            We're here to help! Reach out to us anytime. Our team will get back to you as soon as possible.
          </p>
        </div>

        {/* Content Section: 2 Columns */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Column: Contact Cards */}
          <div className="lg:col-span-5 space-y-4">
            {contactDetails.map((item) => {
              const IconComponent = item.icon;
              return (
                <div
                  key={item.id}
                  className="p-5 rounded-2xl bg-white/70 backdrop-blur-md border border-slate-100/80 shadow-sm hover:shadow-md transition-all duration-200 flex items-center gap-4"
                >
                  <div className={`w-12 h-12 rounded-xl ${item.bgColor} flex items-center justify-center shrink-0`}>
                    <IconComponent className={`w-6 h-6 ${item.iconColor}`} />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900 leading-tight">
                      {item.title}
                    </h3>
                    <p className="text-sm font-semibold text-slate-700 mt-0.5">
                      {item.value}
                    </p>
                    {item.subtext && (
                      <p className="text-xs text-slate-400 mt-0.5">
                        {item.subtext}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Column: Send Us a Message Form */}
          <div className="lg:col-span-7 bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-100">
            {/* Form Header */}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-full bg-pink-100 flex items-center justify-center shrink-0">
                <Send className="w-5 h-5 text-pink-500 fill-pink-500" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">Send us a message</h2>
                <p className="text-xs sm:text-sm text-slate-500">
                  Have a question or need support? Fill out the form below.
                </p>
              </div>
            </div>

            {/* Form Fields */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-xs font-bold text-slate-800 mb-1.5">
                  Name
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Your name"
                    required
                    className="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl border border-slate-200 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200/50 transition-all text-slate-700 placeholder:text-slate-400"
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-bold text-slate-800 mb-1.5">
                  Email
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="Your email address"
                    required
                    className="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl border border-slate-200 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200/50 transition-all text-slate-700 placeholder:text-slate-400"
                  />
                </div>
              </div>

              {/* Message */}
              <div>
                <label className="block text-xs font-bold text-slate-800 mb-1.5">
                  Message
                </label>
                <div className="relative">
                  <MessageSquare className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <textarea
                    name="message"
                    rows="4"
                    value={formData.message}
                    onChange={handleChange}
                    placeholder="Write your message here..."
                    required
                    className="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl border border-slate-200 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200/50 transition-all text-slate-700 placeholder:text-slate-400 resize-none"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                className="w-full mt-2 py-3 px-6 rounded-xl text-white font-semibold text-sm bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600 shadow-md shadow-purple-500/20 active:scale-[0.99] transition-all flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4 fill-white" />
                Send Message
              </button>
            </form>
          </div>

        </div>
      </div>
      </main>
      <HomeFooter />
    </div>
  );
};

export default ContactPage;
