// src/api/authApi.js
// Centralized auth API calls (login + register). Keep this file the single
// place that knows about auth endpoints — components should never call
// fetch() directly for auth.

const API_BASE_URL = 'https://rental-backend.kudoo-live.workers.dev';

const TOKEN_KEY = 'rp_auth_token';
const TOKEN_TYPE_KEY = 'rp_auth_token_type';
const USER_KEY = 'rp_auth_user';

/**
 * Low-level request helper: sets JSON headers, attaches the bearer token
 * when present, and normalizes error handling so every caller gets a
 * consistent shape back (or a thrown Error with a readable message).
 */
async function request(endpoint, { method = 'GET', body, rawBody, contentType, auth = false } = {}) {
  const headers = contentType
    ? { 'Content-Type': contentType }
    : { 'Content-Type': 'application/json' };

  if (auth) {
    const token = getToken();
    if (token) {
      // Login returns token_type: "bearer" -> normalize to "Bearer"
      const type = localStorage.getItem(TOKEN_TYPE_KEY) || 'Bearer';
      const scheme = type.charAt(0).toUpperCase() + type.slice(1).toLowerCase();
      headers.Authorization = `${scheme} ${token}`;
    }
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method,
      headers,
      body: rawBody ?? (body ? JSON.stringify(body) : undefined),
    });
  } catch (networkErr) {
    const reason = networkErr instanceof Error ? networkErr.message : String(networkErr);
    const origin = typeof window !== 'undefined' ? window.location.origin : 'this app';
    throw new Error(`Could not reach the API at ${API_BASE_URL} from ${origin}. ${reason} Check the API URL, network connection, and backend CORS settings.`);
  }

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await response.json().catch(() => ({})) : null;

  // Expired / invalid token on an authenticated call
  if (response.status === 401 && auth) {
    clearSession();
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    const message = data?.message || data?.error || data?.detail || `Request failed (${response.status})`;
    const error = new Error(typeof message === 'string' ? message : `Request failed (${response.status})`);
    const payload = data?.detail && typeof data.detail === 'object' ? data.detail : data;
    error.data = payload;
    error.code = payload?.code;
    error.booking_amount = payload?.booking_amount;
    error.available_balance = payload?.available_balance;
    error.amount_needed = payload?.amount_needed;
    throw error;
  }

  return data;
}

// ---------- Token / session storage helpers ----------

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    clearSession();
    return null;
  }
}

export function isAuthenticated() {
  return Boolean(getToken());
}

function persistSession({ token, access_token: accessToken, token_type: tokenType, user } = {}) {
  const sessionToken = token || accessToken;
  if (sessionToken) localStorage.setItem(TOKEN_KEY, sessionToken);
  if (tokenType) localStorage.setItem(TOKEN_TYPE_KEY, tokenType);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_TYPE_KEY);
  localStorage.removeItem(USER_KEY);
}

// ---------- Login ----------

/**
 * Step 1 of OTP login: trigger an SMS OTP to the given 10-digit phone number.
 */
export async function sendLoginOtp(phone) {
  return request('/auth/otp/send', {
    method: 'POST',
    body: { phone },
  });
}

/**
 * Step 2 of OTP login: verify the code the user received, get back a session.
 */
export async function verifyLoginOtp(phone, otp) {
  const data = await request('/auth/otp/verify', {
    method: 'POST',
    body: { phone, otp },
  });
  persistSession(data);
  await loadProfileIntoSession(data);
  return data;
}

/**
 * Password login with the registered email address.
 * Backend returns: { access_token, token_type: "bearer" } (no user object),
 * so we fetch the profile with the token right after saving it.
 */
export async function loginWithPassword(email, password) {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: { email, password },
  });
  persistSession(data);
  await loadProfileIntoSession(data);
  return data;
}

/**
 * If the login response has no user object, load it from /api/profile
 * using the saved bearer token. Failure here is non-fatal: the token is
 * already saved and the profile can be loaded later.
 */
async function loadProfileIntoSession(data) {
  if (data?.user) return;
  try {
    const profile = await getMyProfile();
    if (profile) {
      localStorage.setItem(USER_KEY, JSON.stringify(profile));
      data.user = profile;
    }
  } catch {
    // ignore – user can be fetched later via getMyProfile()
  }
}

export async function logout() {
  clearSession();
}

// ---------- Register ----------

/**
 * @param {Object} payload
 * @param {string} payload.country
 * @param {string} payload.city
 * @param {string} payload.pincode
 * @param {string} payload.gender
 * @param {string} payload.accountIntent  'finder' | 'companion'
 * @param {string} payload.phone
 * @param {string} payload.email
 * @param {string} payload.password
 */
export async function registerUser(payload) {
  const registration = await request('/api/auth/register', {
    method: 'POST',
    body: payload,
  });

  // Registration already returned a token -> save it and use it.
  if (registration?.access_token || registration?.token) {
    persistSession(registration);
    await loadProfileIntoSession(registration);
    return registration;
  }

  // Otherwise log in with the credentials just used.
  const session = await loginWithPassword(payload.email, payload.password);
  if (registration?.user && !session.user) {
    session.user = registration.user;
    persistSession(session);
  }
  return session;
}

export async function checkEmailAvailable(email) {
  return request(`/auth/check-email?email=${encodeURIComponent(email)}`);
}

export async function checkPhoneAvailable(phone) {
  return request(`/auth/check-phone?phone=${encodeURIComponent(phone)}`);
}

// ---------- Profile & bookings (bearer token required) ----------

// The backend uses the bearer token to identify the logged-in user's profile.
let profileRequest = null;

export function getMyProfile() {
  if (profileRequest) return profileRequest;

  profileRequest = request('/api/profile', { auth: true })
    .then((result) => {
      const profile = result?.profile || result;
      if (profile && typeof profile === 'object') {
        const updatedUser = { ...(getStoredUser() || {}), ...profile };
        localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
        if (typeof window !== 'undefined') window.dispatchEvent(new Event('rp-profile-updated'));
      }
      return result;
    })
    .finally(() => {
      profileRequest = null;
    });

  return profileRequest;
}

// Profile save uses POST with the bearer token.
export function updateMyProfile(profile) {
  return request('/api/profile', { method: 'PATCH', body: profile, auth: true }).then((result) => {
    const storedUser = getStoredUser() || {};
    const updatedUser = { ...storedUser, ...profile, ...(result?.profile || {}) };
    localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
    if (typeof window !== 'undefined') window.dispatchEvent(new Event('rp-profile-updated'));
    return result;
  });
}

export async function uploadProfilePhoto(file, type = 'avatar') {
  const contentType = file.type?.startsWith('image/') ? file.type : 'image/jpeg';
  const result = await request(`/api/profile/photo?type=${encodeURIComponent(type)}`, {
    method: 'POST',
    rawBody: file,
    contentType,
    auth: true,
  });
  const payload = result?.profile || result?.data || result || {};
  const image = payload.image || payload.profile_image || payload.avatar_url || payload.photo || (type === 'avatar' ? payload.url : undefined);
  const url = payload.url || image;
  if (image && type === 'avatar') {
    const storedUser = getStoredUser() || {};
    localStorage.setItem(USER_KEY, JSON.stringify({ ...storedUser, image, profile_image: image, avatar_url: image }));
    if (typeof window !== 'undefined') window.dispatchEvent(new Event('rp-profile-updated'));
  }
  return { ...result, image, url, gallery: payload.gallery };
}

export function createBooking(booking) {
  return request('/api/bookings', { method: 'POST', body: booking, auth: true });
}

export function getMyBookings() {
  return request('/api/bookings', { auth: true });
}

export function topUpWallet(amount) {
  return request('/api/wallet/top-up', { method: 'POST', body: { amount }, auth: true });
}

export function getWalletTransactions() {
  return request('/api/wallet/transactions', { auth: true });
}

export function approveBooking(bookingId) {
  return request(`/api/bookings/${encodeURIComponent(bookingId)}/approve`, { method: 'POST', auth: true });
}

export function verifyBookingOtp(bookingId, otp) {
  return request(`/api/bookings/${encodeURIComponent(bookingId)}/verify-otp`, {
    method: 'POST',
    body: { otp },
    auth: true,
  });
}

export function rejectBooking(bookingId, rejectionMessage = '') {
  return request(`/api/bookings/${encodeURIComponent(bookingId)}/reject`, {
    method: 'POST',
    body: rejectionMessage ? { rejection_message: rejectionMessage } : {},
    auth: true,
  });
}

export function cancelBooking(bookingId) {
  return request(`/api/bookings/${encodeURIComponent(bookingId)}/cancel`, {
    method: 'POST',
    auth: true,
  });
}

export function getFavoritePeople() {
  return request('/api/favorites', { auth: true });
}

export function checkFavorite(favoriteUserId) {
  return request(`/api/favorites/check/${encodeURIComponent(favoriteUserId)}`, { auth: true });
}

export function addFavorite(favoriteUserId) {
  return request(`/api/favorites/${encodeURIComponent(favoriteUserId)}`, { method: 'POST', auth: true });
}

export function removeFavorite(favoriteUserId) {
  return request(`/api/favorites/${encodeURIComponent(favoriteUserId)}`, { method: 'DELETE', auth: true });
}

export function getConversations() {
  return request('/api/messages/conversations', { auth: true });
}

export function getConversationMessages(userId) {
  return request(`/api/messages/${encodeURIComponent(userId)}`, { auth: true });
}

export function sendMessage(receiverId, content) {
  return request('/api/messages', {
    method: 'POST',
    body: { receiver_id: receiverId, content },
    auth: true,
  });
}
