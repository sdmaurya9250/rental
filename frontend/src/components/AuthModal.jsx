import React, { useState, useEffect } from 'react';
import { X, RefreshCw, Phone, Globe, Mail, Lock, Eye, EyeOff, MapPin, Hash, Search, UserPlus, Users } from 'lucide-react';

export default function AuthModal({ isOpen, onClose, onLogin, initialMode = 'login' }) {
  // Mode: 'login' | 'register'
  const [mode, setMode] = useState(initialMode);
  // Login Type: 'otp' | 'password'
  const [loginType, setLoginType] = useState('otp');

  // Form States
  const [phone, setPhone] = useState('');
  const [country, setCountry] = useState('IN India (+91)');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [city, setCity] = useState('');
  const [pincode, setPincode] = useState('');
  const [gender, setGender] = useState('');
  const [accountIntent, setAccountIntent] = useState('find');

  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      {/* Modal Box Container */}
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden my-8 transform transition-all">
        
        {/* Header Gradient Strip */}
        <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-rose-500 p-6 text-white relative">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 text-white/80 hover:text-white p-1 rounded-full transition"
          >
            <X className="w-6 h-6" />
          </button>

          <h2 className="text-2xl font-bold tracking-tight">Welcome to RentPeople</h2>
          <p className="text-xs text-white/90 mt-1 font-medium">
            Your social & lifestyle support platform
          </p>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 text-gray-800 max-h-[80vh] overflow-y-auto">
          
          {/* Main Mode Toggle Tabs (Login vs Register) */}
          <div className="bg-gray-100 p-1 rounded-xl flex items-center">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition duration-200 ${
                mode === 'login'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Login
            </button>
            <button
              type="button"
              onClick={() => setMode('register')}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition duration-200 ${
                mode === 'register'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Register
            </button>
          </div>

          {/* ================= LOGIN FORM ================= */}
          {mode === 'login' && (
            <div className="space-y-4">
              {/* Sub-toggle: Password vs Login with OTP */}
              <div className="bg-gray-100 p-1 rounded-xl flex items-center">
                <button
                  type="button"
                  onClick={() => setLoginType('password')}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
                    loginType === 'password'
                      ? 'bg-white text-purple-700 shadow-sm'
                      : 'text-gray-500 hover:text-gray-800'
                  }`}
                >
                  Password
                </button>
                <button
                  type="button"
                  onClick={() => setLoginType('otp')}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
                    loginType === 'otp'
                      ? 'bg-white text-purple-700 shadow-sm'
                      : 'text-gray-500 hover:text-gray-800'
                  }`}
                >
                  Login with OTP
                </button>
              </div>

              {loginType === 'otp' ? (
                /* OTP Login Field */
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-700">Phone Number</label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="Enter your mobile number"
                      className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-purple-600 focus:ring-1 focus:ring-purple-600 transition"
                    />
                  </div>
                </div>
              ) : (
                /* Password Login Fields */
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-700">Mobile / Email</label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        placeholder="Enter email or mobile"
                        className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-purple-600 transition"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-700">Password</label>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter password"
                        className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-10 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-purple-600 transition"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="text-right">
                    <button type="button" className="text-xs text-purple-600 font-medium hover:underline">
                      Forgot Password?
                    </button>
                  </div>
                </div>
              )}

              {/* Action Submit Button */}
              <button
                type="button"
                onClick={onLogin}
                className="w-full mt-2 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-95 text-white font-semibold rounded-xl text-sm transition duration-200 shadow-md shadow-pink-500/20"
              >
                {loginType === 'otp' ? 'Send OTP' : 'Login'}
              </button>
            </div>
          )}

          {/* ================= REGISTER FORM ================= */}
          {mode === 'register' && (
            <div className="space-y-4">
              {/* Country Select Field */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700">
                  Country <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Globe className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-800 font-medium focus:outline-none focus:border-purple-600 transition"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-700">City <span className="text-red-500">*</span></label>
                  <div className="relative">
                    <MapPin className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input type="text" value={city} onChange={(event) => setCity(event.target.value)} placeholder="Your city" className="w-full rounded-xl border border-gray-300 bg-white py-3 pl-10 pr-4 text-sm text-gray-800 placeholder-gray-400 focus:border-purple-600 focus:outline-none" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-700">Pincode <span className="text-red-500">*</span></label>
                  <div className="relative">
                    <Hash className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input type="text" inputMode="numeric" maxLength="6" value={pincode} onChange={(event) => setPincode(event.target.value)} placeholder="6-digit" className="w-full rounded-xl border border-gray-300 bg-white py-3 pl-10 pr-4 text-sm text-gray-800 placeholder-gray-400 focus:border-purple-600 focus:outline-none" />
                  </div>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700">Gender <span className="text-red-500">*</span></label>
                <select value={gender} onChange={(event) => setGender(event.target.value)} className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-800 focus:border-purple-600 focus:outline-none">
                  <option value="" disabled>Select gender</option>
                  <option value="woman">Woman</option>
                  <option value="man">Man</option>
                  <option value="non-binary">Non-binary</option>
                  <option value="prefer-not-to-say">Prefer not to say</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-700">I want to <span className="text-red-500">*</span></label>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  {[
                    { value: 'find', label: 'Find a RentPeople', icon: Search },
                    { value: 'become', label: 'Become a RentPeople', icon: UserPlus },
                    { value: 'both', label: 'Both', icon: Users },
                  ].map((option) => {
                    const Icon = option.icon;
                    const selected = accountIntent === option.value;
                    return <button key={option.value} type="button" onClick={() => setAccountIntent(option.value)} className={`flex min-h-24 flex-col items-center justify-center gap-2 rounded-xl border p-3 text-center text-xs font-semibold transition ${selected ? 'border-fuchsia-500 bg-fuchsia-50 text-fuchsia-700 ring-1 ring-fuchsia-300' : 'border-gray-300 bg-white text-gray-700 hover:border-violet-300'}`}><Icon className="h-5 w-5" />{option.label}</button>;
                  })}
                </div>
                <p className="text-[11px] text-gray-500">All options will create a RentPeople account.</p>
              </div>

              {/* Mobile Number Field */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700">
                  Mobile Number <span className="text-red-500">*</span>
                </label>
                <div className="flex rounded-xl border border-gray-300 overflow-hidden focus-within:border-purple-600 transition">
                  <span className="bg-gray-50 border-r border-gray-300 px-3.5 flex items-center text-xs font-semibold text-gray-600">
                    +91
                  </span>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="Enter mobile number"
                    className="w-full bg-white px-3.5 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none"
                  />
                </div>
                <p className="text-[11px] text-gray-400">IN India (10 digit number only)</p>
              </div>

              {/* Email Field */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700">
                  Email <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-purple-600 transition"
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700">
                  Password <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password (min 6 characters)"
                    className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-10 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-purple-600 transition"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Action Submit Button */}
              <button
                type="button"
                onClick={onLogin}
                className="w-full mt-2 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-95 text-white font-semibold rounded-xl text-sm transition duration-200 shadow-md shadow-pink-500/20"
              >
                Create Account
              </button>
            </div>
          )}

          {/* Footer Terms Note */}
          <p className="text-center text-[11px] text-gray-500 pt-2">
            By continuing, you agree to our{' '}
            <a href="#terms" className="text-purple-600 hover:underline">
              Terms
            </a>{' '}
            and{' '}
            <a href="#privacy" className="text-purple-600 hover:underline">
              Privacy Policy
            </a>
          </p>

        </div>
      </div>
    </div>
  );
}
