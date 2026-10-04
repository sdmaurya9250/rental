import { approveBooking, createBooking, getConversationMessages, getConversations, getMyBookings, rejectBooking, sendMessage } from '../auth/auth';

const API_BASE_URL = 'https://rental-backend.kudoo-live.workers.dev/api/people';
const API_ROOT_URL = 'https://rental-backend.kudoo-live.workers.dev/api';
const LOCATION_PREFERENCE_KEY = 'rp_location_preference';

export function getLocationPreference() {
  if (typeof window === 'undefined') return null;
  try {
    return JSON.parse(window.localStorage.getItem(LOCATION_PREFERENCE_KEY) || 'null');
  } catch {
    return null;
  }
}

export function saveLocationPreference(preference) {
  if (typeof window !== 'undefined') window.localStorage.setItem(LOCATION_PREFERENCE_KEY, JSON.stringify(preference));
}

export function clearLocationPreference() {
  if (typeof window !== 'undefined') window.localStorage.removeItem(LOCATION_PREFERENCE_KEY);
}

async function requestPeople(path = '') {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Unable to load people (HTTP ${response.status}).`);
  }

  const result = await response.json();
  return result;
}

export async function fetchPeople(options = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(options)) {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value));
  }
  const result = await requestPeople(params.size ? `?${params}` : '');
  const people = Array.isArray(result) ? result : result.people;
  if (!Array.isArray(people)) {
    throw new Error('The people API returned an unexpected response.');
  }
  return people;
}

export function getCurrentLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Location access is not supported by this browser.'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ lat: coords.latitude, lng: coords.longitude }),
      (error) => reject(new Error(error.code === error.PERMISSION_DENIED
        ? 'Location permission was denied. You can still choose a city manually.'
        : error.code === error.TIMEOUT
          ? 'Location lookup timed out. Please try again.'
          : 'Unable to get your location. You can still choose a city manually.')),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });
}

export async function reverseGeocode({ lat, lng }) {
  const params = new URLSearchParams({ lat: String(lat), lng: String(lng) });
  const response = await fetch(`${API_ROOT_URL}/geo/reverse?${params}`);
  if (!response.ok) throw new Error(`Reverse geocoding failed (HTTP ${response.status}).`);
  return response.json();
}

export async function geocodeCity(query) {
  const params = new URLSearchParams({ q: query });
  const response = await fetch(`${API_ROOT_URL}/geo/geocode?${params}`);
  if (!response.ok) throw new Error(`City search failed (HTTP ${response.status}).`);
  const result = await response.json();
  return Array.isArray(result.results) ? result.results : [];
}

export async function fetchPersonById(personId) {
  const result = await requestPeople(`/${encodeURIComponent(personId)}`);
  const person = result.person || result;
  if (!person || !person.id) {
    throw new Error('The profile could not be found.');
  }
  return person;
}

export function createBookingRecord(booking) {
  return createBooking(booking);
}

export function fetchBookingRecords() {
  return getMyBookings();
}

export function approveBookingRecord(bookingId) {
  return approveBooking(bookingId);
}

export function rejectBookingRecord(bookingId, message) {
  return rejectBooking(bookingId, message);
}

export function fetchConversations() {
  return getConversations();
}

export function fetchConversationMessages(userId) {
  return getConversationMessages(userId);
}

export function sendChatMessage(receiverId, content) {
  return sendMessage(receiverId, content);
}

export function getPersonPrice(person) {
  return Number(person.priceValue ?? person.rate ?? person.price?.replace(/[^\d.]/g, '')) || 0;
}

export function formatPersonPrice(amount) {
  return `₹${Number(amount || 0).toLocaleString('en-IN')}`;
}
