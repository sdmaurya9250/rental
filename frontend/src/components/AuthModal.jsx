import React, { useState, useEffect } from 'react';
import { X, Phone, Mail, Lock, Eye, EyeOff, MapPin, Hash, Search, UserPlus, Users, Loader2 } from 'lucide-react';
import {
  sendLoginOtp,
  verifyLoginOtp,
  loginWithPassword,
  registerUser,
} from '../auth/auth';
import { getCurrentLocation, reverseGeocode } from '../pages/finderApi';

// --- Maps between what the UI shows and what the backend's Literal types expect ---
const GENDER_OPTIONS = [
  { value: 'Male', label: 'Male' },
  { value: 'Female', label: 'Female' },
  { value: 'Other', label: 'Other' },
];

const INTENT_OPTIONS = [
  { value: 'Find a RentCoPartner', label: 'Find a RentCoPartner', icon: Search },
  { value: 'Become a RentCoPartner', label: 'Become a RentCoPartner', icon: UserPlus },
  { value: 'Both', label: 'Both', icon: Users },
];

export default function AuthModal({ isOpen, onClose, onLogin, initialMode = 'login' }) {
  // Mode: 'login' | 'register'
  const [mode, setMode] = useState(initialMode);
  // Login Type: 'otp' | 'password'
  const [loginType, setLoginType] = useState('password');

  // Form States
  const [phone, setPhone] = useState('');
  const country = 'India';
  const [email, setEmail] = useState('');
  const [identifier, setIdentifier] = useState(''); // password-login email/mobile field
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [city, setCity] = useState('');
  const [coordinates, setCoordinates] = useState(null);
  const [pincode, setPincode] = useState('');
  const [gender, setGender] = useState(''); // now holds 'Male' | 'Female' | 'Other'
  const [accountIntent, setAccountIntent] = useState('Find a RentCoPartner');
  const [detectingLocation, setDetectingLocation] = useState(false);

  // OTP flow state
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);

  // UX state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setMode(initialMode);
    setError('');
  }, [initialMode]);

  // Reset transient state whenever the tab/type changes so stale errors
  // and OTP steps don't leak between flows.
  useEffect(() => {
    setError('');
    setOtpSent(false);
    setOtp('');
  }, [mode, loginType]);

  if (!isOpen) return null;

  async function handleSendOtp() {
    setError('');
    if (!/^\d{10}$/.test(phone)) {
      setError('Enter a valid 10-digit mobile number.');
      return;
    }
    try {
      setLoading(true);
      await sendLoginOtp(phone);
      setOtpSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp() {
    setError('');
    if (!/^\d{4,6}$/.test(otp)) {
      setError('Enter the OTP you received.');
      return;
    }
    try {
      setLoading(true);
      const data = await verifyLoginOtp(phone, otp);
      onLogin?.(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handlePasswordLogin() {
    setError('');
    if (!identifier || !password) {
      setError('Enter your email/mobile and password.');
      return;
    }
    try {
      setLoading(true);
      const data = await loginWithPassword(identifier, password);
      onLogin?.(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister() {
    setError('');
    if (!city || !pincode || !gender || !phone || !email || !password) {
      setError('Please fill in all required fields.');
      return;
    }
    if (!/^\d{10}$/.test(phone)) {
      setError('Enter a valid 10-digit mobile number.');
      return;
    }
    if (!/^\d{6}$/.test(pincode)) {
      setError('Enter a valid 6-digit pincode.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    try {
      setLoading(true);
      // Keys and values here must match RegisterRequest exactly:
      // country, city, pincode, gender ('Male'|'Female'|'Other'),
      // want_to ('Find a RentCoPartner'|'Become a RentCoPartner'|'Both'),
      // mobile, email, password
      const data = await registerUser({
        country,
        city,
        pincode,
        gender,
        want_to: accountIntent,
        lat: coordinates?.lat ?? null,
        lng: coordinates?.lng ?? null,
        mobile: phone,
        email,
        password,
      });
      onLogin?.(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function detectRegistrationCity() {
    setError('');
    setDetectingLocation(true);
    try {
      const coordinates = await getCurrentLocation();
      const place = await reverseGeocode(coordinates);
      if (!place.city) {
        throw new Error('Could not identify your city. Please enter it manually.');
      }
      setCoordinates(coordinates);
      setCity(place.city);
    } catch (err) {
      const message = err.message || '';
      setError(/permission was denied/i.test(message)
        ? 'Location is blocked. In Chrome, open the site settings from the icon beside the address bar, set Location to Allow, then tap Detect my location again.'
        : `${message || 'Unable to detect your location.'} You can also enter your city manually.`);
    } finally {
      setDetectingLocation(false);
    }
  }

  function handlePrimaryAction() {
    if (mode === 'login') {
      if (loginType === 'otp') {
        return otpSent ? handleVerifyOtp() : handleSendOtp();
      }
      return handlePasswordLogin();
    }
    return handleRegister();
  }

  function primaryLabel() {
    if (loading) return '...';
    if (mode === 'register') return 'Create Account';
    if (loginType === 'password') return 'Login';
    return otpSent ? 'Verify OTP' : 'Send OTP';
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#211536]/35 backdrop-blur-[2px] p-3 overflow-y-auto">
      {/* Modal Box Container */}
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden my-8 transform transition-all">

        {/* Header Gradient Strip */}
        <div className="bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] p-5 text-white relative">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 text-white/80 hover:text-white p-1 rounded-full transition"
          >
            <X className="w-6 h-6" />
          </button>

          <h2 className="text-2xl font-bold tracking-tight">Welcome to RentCoPartner</h2>
          <p className="text-xs text-white/90 mt-1 font-medium">
            Your social & lifestyle support platform
          </p>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 text-gray-800 max-h-[82vh] overflow-y-auto">

          {/* Main Mode Toggle Tabs (Login vs Register) */}
          <div className="bg-gray-100 p-1 rounded-xl flex items-center">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition duration-200 ${
                mode === 'login' ? 'bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] text-white shadow-md' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Login
            </button>
            <button
              type="button"
              onClick={() => setMode('register')}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition duration-200 ${
                mode === 'register' ? 'bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] text-white shadow-md' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Register
            </button>
          </div>

          {/* Shared error banner */}
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-xs font-medium text-red-600">
              {error}
            </div>
          )}

          {/* ================= LOGIN FORM ================= */}
          {mode === 'login' && (
            <div className="space-y-4">
              {/* Sub-toggle: Password vs Login with OTP */}
              <div className="bg-gray-100 p-1 rounded-xl flex items-center">
                <button
                  type="button"
                  onClick={() => setLoginType('password')}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
                    loginType === 'password' ? 'bg-white text-[#8a1cf7] shadow-sm' : 'text-gray-500 hover:text-gray-800'
                  }`}
                >
                  Password
                </button>
                <button
                  type="button"
                  onClick={() => setLoginType('otp')}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
                    loginType === 'otp' ? 'bg-white text-[#8a1cf7] shadow-sm' : 'text-gray-500 hover:text-gray-800'
                  }`}
                >
                  Login with OTP
                </button>
              </div>

              {loginType === 'otp' ? (
                <div className="space-y-3">
                  {/* Phone field — locked once OTP is sent */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-700">Phone Number</label>
                    <div className="relative">
                      <Phone className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="tel"
                        value={phone}
                        disabled={otpSent}
                        onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                        placeholder="Enter your mobile number"
                        maxLength={10}
                        className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#8a1cf7] focus:ring-1 focus:ring-[#8a1cf7] transition disabled:bg-gray-50 disabled:text-gray-500"
                      />
                    </div>
                  </div>

                  {otpSent && (
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-gray-700">Enter OTP</label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={otp}
                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                        placeholder="6-digit code"
                        maxLength={6}
                        className="w-full bg-white border border-gray-300 rounded-xl px-4 py-3 text-sm tracking-widest text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#8a1cf7] transition"
                      />
                      <button
                        type="button"
                        onClick={handleSendOtp}
                        disabled={loading}
                        className="text-xs text-[#8a1cf7] font-medium hover:underline"
                      >
                        Resend OTP
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                /* Password Login Fields */
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-700">Email</label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={identifier}
                        onChange={(e) => setIdentifier(e.target.value)}
                        placeholder="Enter your registered email"
                        className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#8a1cf7] transition"
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
                        className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-10 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#8a1cf7] transition"
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
                    <button type="button" className="text-xs text-[#8a1cf7] font-medium hover:underline">
                      Forgot Password?
                    </button>
                  </div>
                </div>
              )}

              {/* Action Submit Button */}
              <button
                type="button"
                onClick={handlePrimaryAction}
                disabled={loading}
                className="w-full mt-2 py-3 bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] hover:opacity-95 text-white font-semibold rounded-xl text-sm transition duration-200 shadow-md shadow-violet-500/20 disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {primaryLabel()}
              </button>
            </div>
          )}

          {/* ================= REGISTER FORM ================= */}
          {mode === 'register' && (
            <div className="space-y-4">
              {/* Contact and password details come first; country and account intent use defaults. */}
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-700">Mobile Number <span className="text-red-500">*</span></label>
                  <div className="flex rounded-xl border border-gray-300 overflow-hidden focus-within:border-[#8a1cf7] transition">
                    <span className="bg-gray-50 border-r border-gray-300 px-3 flex items-center text-xs font-semibold text-gray-600">+91</span>
                    <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))} placeholder="Enter mobile number" maxLength={10} className="w-full bg-white px-3 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none" />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-700">Email <span className="text-red-500">*</span></label>
                  <div className="relative"><Mail className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" /><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.com" className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#8a1cf7] transition" /></div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-700">Password <span className="text-red-500">*</span></label>
                  <div className="relative"><Lock className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" /><input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-10 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#8a1cf7] transition" /><button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">{showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}</button></div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-700">Confirm Password <span className="text-red-500">*</span></label>
                  <div className="relative"><Lock className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" /><input type={showPassword ? 'text' : 'password'} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Re-enter your password" className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#8a1cf7] transition" /></div>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700">I want to <span className="text-red-500">*</span></label>
                <div className="grid grid-cols-3 gap-2">
                  {INTENT_OPTIONS.map((option) => {
                    const Icon = option.icon;
                    const selected = accountIntent === option.value;
                    return (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setAccountIntent(option.value)}
                        className={`flex min-h-14 items-center justify-center gap-1.5 rounded-lg border px-2 py-2 text-center text-[11px] font-semibold transition ${
                          selected ? 'border-[#8a1cf7] bg-violet-50 text-[#8a1cf7] ring-1 ring-violet-200' : 'border-gray-300 bg-white text-gray-700 hover:border-violet-300'
                        }`}
                      >
                        <Icon className="h-4 w-4 shrink-0" />
                        <span>{option.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

<div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
  {/* CITY */}
  <div className="space-y-1.5">
    <label className="text-xs font-semibold text-gray-700">
      City <span className="text-red-500">*</span>
    </label>

    <div className="relative">
      {/* Location Icon */}
      <MapPin
        className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
      />

      <input
        type="text"
        value={city}
        onChange={(event) => setCity(event.target.value)}
        placeholder="Your city"
        className="w-full rounded-xl border border-gray-300 bg-white py-2.5 pl-10 pr-12 text-sm text-gray-800 placeholder-gray-400 transition focus:border-[#8a1cf7] focus:outline-none focus:ring-2 focus:ring-[#8a1cf7]/10"
      />

      {/* Detect Location */}
      {(accountIntent === 'Become a RentCoPartner' ||
        accountIntent === 'Both') && (
        <button
          type="button"
          onClick={detectRegistrationCity}
          disabled={detectingLocation}
          title="Detect my location"
          aria-label={detectingLocation ? 'Detecting your location' : 'Detect my location'}
          className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-lg bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] text-white shadow-sm transition hover:scale-105 disabled:cursor-wait disabled:opacity-60"
        >
          {detectingLocation ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <MapPin className="h-4 w-4" />
          )}
        </button>
      )}
    </div>

    {/* Small detected status */}
    {coordinates && city && (
      <div className="flex items-center gap-1.5 px-1 text-[11px] font-medium text-[#8a1cf7]">
        <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
        Location detected: {city}
      </div>
    )}
    {!coordinates && (accountIntent === 'Become a RentCoPartner' || accountIntent === 'Both') && (
      <p className="px-1 text-[11px] leading-4 text-gray-500">
        Tap the pin and choose Allow when Chrome asks. If location is blocked, open the site settings beside the address bar, allow Location, then try again.
      </p>
    )}
  </div>

  {/* PINCODE */}
  <div className="space-y-1.5">
    <label className="text-xs font-semibold text-gray-700">
      Pincode <span className="text-red-500">*</span>
    </label>

    <div className="relative">
      <Hash
        className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
      />

      <input
        type="text"
        inputMode="numeric"
        maxLength="6"
        value={pincode}
        onChange={(event) =>
          setPincode(event.target.value.replace(/\D/g, ''))
        }
        placeholder="6-digit"
        className="w-full rounded-xl border border-gray-300 bg-white py-2.5 pl-10 pr-4 text-sm text-gray-800 placeholder-gray-400 transition focus:border-[#8a1cf7] focus:outline-none focus:ring-2 focus:ring-[#8a1cf7]/10"
      />
    </div>
  </div>
</div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700">Gender <span className="text-red-500">*</span></label>
                <select value={gender} onChange={(event) => setGender(event.target.value)} className="w-full rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-800 focus:border-[#8a1cf7] focus:outline-none">
                  <option value="" disabled>Select gender</option>
                  {GENDER_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Action Submit Button */}
              <button
                type="button"
                onClick={handlePrimaryAction}
                disabled={loading}
                className="w-full mt-2 py-3 bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] hover:opacity-95 text-white font-semibold rounded-xl text-sm transition duration-200 shadow-md shadow-violet-500/20 disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {primaryLabel()}
              </button>
            </div>
          )}

          {/* Footer Terms Note */}
          <p className="text-center text-[11px] text-gray-500 pt-2">
            By continuing, you agree to our{' '}
            <a href="#terms" className="text-[#8a1cf7] hover:underline">Terms</a>{' '}
            and{' '}
            <a href="#privacy" className="text-[#8a1cf7] hover:underline">Privacy Policy</a>
          </p>

        </div>
      </div>
    </div>
  );
}
