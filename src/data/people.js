export const people = [
  { id: 'kiara', name: 'Kiara', age: 24, location: 'Mumbai', rate: 1500, tags: ['Travel buddy', 'Event partner', 'Conversation'], image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=800&auto=format&fit=crop' },
  { id: 'aanya', name: 'Aanya', age: 23, location: 'Bangalore', rate: 1200, tags: ['Fitness', 'Travel'], image: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?q=80&w=400&auto=format&fit=crop' },
  { id: 'rohan', name: 'Rohan', age: 26, location: 'Delhi', rate: 1200, tags: ['Events', 'Travel'], image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=400&auto=format&fit=crop' },
];

export const findPerson = (id) => people.find((person) => person.id === id) ?? people[0];
export const formatPrice = (amount) => `₹${amount.toLocaleString('en-IN')}`;
