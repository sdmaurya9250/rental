// src/api/authApi.js
// Centralized auth API calls (login + register). Keep this file the single
// place that knows about auth endpoints — components should never call
// fetch() directly for auth.

const API_BASE_URL = 'https://rental-backend.kudoo-live.workers.dev' || 'http://localhost:5000/api';

const TOKEN_KEY = 'rp_auth_token';
const USER_KEY = 'rp_auth_user';

/**
 * Low-level request helper: sets JSON headers, attaches the bearer token
 * when present, and normalizes error handling so every caller gets a
 * consistent shape back (or a thrown Error with a readable message).
 */
async function request(endpoint, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' };

  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (networkErr) {
    throw new Error('Network error — please check your connection and try again.');
  }

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await response.json().catch(() => ({})) : null;

  if (!response.ok) {
    const message = data?.message || data?.error || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

// ---------- Token / session storage helpers ----------

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function isAuthenticated() {
  return Boolean(getToken());
}

function persistSession({ token, user }) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
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
  return data;
}

/**
 * Password login with either email or phone as the identifier.
 */
export async function loginWithPassword(email, password) {
  const data = await request('/api/auth/login', {
    method: 'POST',
    body: { email, password },
  });
  persistSession(data);
  return data;
}

export async function logout() {
  try {
    await request('/auth/logout', { method: 'POST', auth: true });
  } finally {
    clearSession();
  }
}

// ---------- Register ----------

/**
 * @param {Object} payload
 * @param {string} payload.country
 * @param {string} payload.city
 * @param {string} payload.pincode
 * @param {string} payload.gender
 * @param {string} payload.accountIntent  'find' | 'become' | 'both'
 * @param {string} payload.phone
 * @param {string} payload.email
 * @param {string} payload.password
 */
export async function registerUser(payload) {
  const data = await request('/api/auth/register', {
    method: 'POST',
    body: payload,
  });
  persistSession(data);
  return data;
}

export async function checkEmailAvailable(email) {
  return request(`/auth/check-email?email=${encodeURIComponent(email)}`);
}

export async function checkPhoneAvailable(phone) {
  return request(`/auth/check-phone?phone=${encodeURIComponent(phone)}`);
}