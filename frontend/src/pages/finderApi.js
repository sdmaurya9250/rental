const API_BASE_URL = 'https://rental-backend.kudoo-live.workers.dev/api/people';

async function requestPeople(path = '') {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Unable to load people (HTTP ${response.status}).`);
  }

  const result = await response.json();
  return result;
}

export async function fetchPeople() {
  const result = await requestPeople();
  const people = Array.isArray(result) ? result : result.people;
  if (!Array.isArray(people)) {
    throw new Error('The people API returned an unexpected response.');
  }
  return people;
}

export async function fetchPersonById(personId) {
  const result = await requestPeople(`/${encodeURIComponent(personId)}`);
  const person = result.person || result;
  if (!person || !person.id) {
    throw new Error('The profile could not be found.');
  }
  return person;
}

export function getPersonPrice(person) {
  return Number(person.priceValue ?? person.rate ?? person.price?.replace(/[^\d.]/g, '')) || 0;
}

export function formatPersonPrice(amount) {
  return `₹${Number(amount || 0).toLocaleString('en-IN')}`;
}
