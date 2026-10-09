import { useEffect } from 'react';
import { Navigate, Outlet, useNavigate } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import { getStoredUser, isAuthenticated } from './auth/auth';
import Seo from './components/Seo';

function LandingRoute() {
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated()) navigate('/dashboard', { replace: true });
  }, [navigate]);

  return <Outlet />;
}

function BrowseRoute() {
  const user = getStoredUser();
  const role = String(user?.want_to || user?.wantTo || user?.accountIntent || '').trim().toLowerCase();
  const canBrowse = role !== 'companion';
  return canBrowse ? <Seo title="Browse Companions by Service and City | RentCoPartner" description="Explore RentCoPartner profiles, compare listed social and lifestyle services, and review availability and rates to find a companion for your plans." noIndex><Outlet /></Seo> : <Navigate to="/dashboard" replace />;
}

function seoRoute(importer, seo) {
  return {
    lazy: async () => {
      const { default: Page } = await importer();
      return { Component: () => <><Seo {...seo} /><Page /></> };
    },
  };
}

function notFoundRoute(importer) {
  return {
    lazy: async () => {
      const { default: Page } = await importer();
      return { Component: Page };
    },
  };
}

export const routes = [
  {
    path: '/',
    element: <LandingRoute />,
    children: [
      { index: true, lazy: () => import('./pages/Home.jsx').then(({ default: Page }) => ({ Component: Page })) },
    ],
  },
  { path: '/login', element: <Navigate to="/?auth=login" replace /> },
  { path: '/privacy-policy', ...notFoundRoute(() => import('./pages/PrivacyPolicyPage.jsx')) },
  { path: '/terms-and-conditions', ...notFoundRoute(() => import('./pages/TermsAndConditionsPage.jsx')) },
  { path: '/refund-policy', ...notFoundRoute(() => import('./pages/RefundPolicyPage.jsx')) },
  { path: '/contact', ...notFoundRoute(() => import('./pages/ContactPage.jsx')) },
  { path: '/help', ...notFoundRoute(() => import('./pages/HelpPage.jsx')) },
  { path: '/404', ...notFoundRoute(() => import('./pages/NotFoundPage.jsx')) },
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { path: 'dashboard', ...seoRoute(() => import('./pages/DashboardPage.jsx'), { title: 'Your Booking Dashboard | RentCoPartner', description: 'Manage your RentCoPartner profile, companion bookings, messages, saved profiles and wallet from your account dashboard. View updates and manage plans.', noIndex: true }) },
      { path: 'browse', ...seoRoute(() => import('./pages/Browse.jsx'), { title: 'Browse Companions and Services | RentCoPartner', description: 'Browse RentCoPartner companions by city and service. Compare profile details, availability and rates before sending a booking request for your plans.', noIndex: true }) },
      { path: 'bookings', ...seoRoute(() => import('./pages/BookingsList.jsx'), { title: 'Manage Your Bookings | RentCoPartner', description: 'Review RentCoPartner booking requests, upcoming plans, completed appointments and booking details in your account. Manage every booking from your dashboard.', noIndex: true }) },
      { path: 'search', ...seoRoute(() => import('./pages/SearchResultsPage.jsx'), { title: 'Search Companions and Services | RentCoPartner', description: 'Search RentCoPartner companion profiles, social activities and lifestyle services for your city. Review service details and listed availability before booking.', noIndex: true }) },
      { path: 'people/:personId', ...seoRoute(() => import('./pages/ProfilePage.jsx'), { title: 'Companion Profile and Services | RentCoPartner', description: 'View a RentCoPartner companion profile, listed social services, availability, rates and booking options. Review profile details before you send a request.', noIndex: true }) },
      { path: 'finders/:finderId', ...seoRoute(() => import('./pages/FinderProfilePage.jsx'), { title: 'Finder Profile | RentCoPartner', description: 'View profile details shared by a finder for an incoming booking.', noIndex: true }) },
      { path: 'favorites', ...seoRoute(() => import('./pages/FavoritesPage.jsx'), { title: 'Your Favorite Companions | RentCoPartner', description: 'View and manage companion profiles saved to favorites in your RentCoPartner account. Revisit service details and availability as you plan a booking.', noIndex: true }) },
      { path: 'messages', ...seoRoute(() => import('./pages/MessagesPage.jsx'), { title: 'Your Messages | RentCoPartner', description: 'Open RentCoPartner messages to discuss booking details and coordinate with other members. Access account conversations and review recent messages.', noIndex: true }) },
      { path: 'my-profile', ...seoRoute(() => import('./pages/MyProfilePage.jsx'), { title: 'Manage Your Profile | RentCoPartner', description: 'Update your RentCoPartner profile, service details, location, availability, photos and account information. Keep your profile details current for other members.', noIndex: true }) },
      { path: 'wallet', ...seoRoute(() => import('./pages/WalletPage.jsx'), { title: 'Manage Your Wallet | RentCoPartner', description: 'View wallet activity and manage eligible booking payments or earnings in your RentCoPartner account. Review transaction details and your balance.', noIndex: true }) },
      { path: 'date-companion', ...seoRoute(() => import('./pages/CategoryPages.jsx').then(({ DateCompanionPage }) => ({ default: DateCompanionPage })), { title: 'Social Companion Services | RentCoPartner', description: 'Browse social companion profiles on RentCoPartner by listed activity, location and availability. Compare profile details and rates before sending a request.', noIndex: true }) },
      { path: 'travel-buddy', ...seoRoute(() => import('./pages/CategoryPages.jsx').then(({ TravelBuddyPage }) => ({ default: TravelBuddyPage })), { title: 'Travel Companion Services | RentCoPartner', description: 'Find travel companion profiles on RentCoPartner by location and listed services. Review availability and rates as you plan a trip or local outing.', noIndex: true }) },
      { path: 'event-partner', ...seoRoute(() => import('./pages/CategoryPages.jsx').then(({ EventPartnerPage }) => ({ default: EventPartnerPage })), { title: 'Event Companion Services | RentCoPartner', description: 'Explore event companion profiles on RentCoPartner and compare listed activities, availability and rates before you send a booking request on the platform.', noIndex: true }) },
      { path: 'conversation', ...seoRoute(() => import('./pages/CategoryPages.jsx').then(({ ConversationPage }) => ({ default: ConversationPage })), { title: 'Conversation Companion Services | RentCoPartner', description: 'Browse conversation companion profiles on RentCoPartner and review listed services, location and availability before sending a booking request.', noIndex: true }) },
      { path: 'fitness', ...seoRoute(() => import('./pages/CategoryPages.jsx').then(({ FitnessPage }) => ({ default: FitnessPage })), { title: 'Fitness Companion Services | RentCoPartner', description: 'Explore fitness companion profiles on RentCoPartner and review listed activities, location and availability before you arrange a session through the platform.', noIndex: true }) },
      { path: 'networking', ...seoRoute(() => import('./pages/CategoryPages.jsx').then(({ NetworkingPage }) => ({ default: NetworkingPage })), { title: 'Networking Companion Services | RentCoPartner', description: 'Browse networking companion profiles on RentCoPartner and compare listed activities, location, availability and rates before making a booking request.', noIndex: true }) },
      { path: 'photoshoot', ...seoRoute(() => import('./pages/CategoryPages.jsx').then(({ PhotoshootPage }) => ({ default: PhotoshootPage })), { title: 'Photoshoot Companion Services | RentCoPartner', description: 'Find photoshoot companion profiles on RentCoPartner and check listed services, location and availability as you plan a creative session for your next shoot.', noIndex: true }) },
      { path: 'gaming', ...seoRoute(() => import('./pages/CategoryPages.jsx').then(({ GamingPage }) => ({ default: GamingPage })), { title: 'Gaming Companion Services | RentCoPartner', description: 'Explore gaming companion profiles on RentCoPartner and compare listed activities, location and availability before sending a booking request.', noIndex: true }) },
      { path: 'other', ...seoRoute(() => import('./pages/CategoryPages.jsx').then(({ OtherPage }) => ({ default: OtherPage })), { title: 'Companion Services | RentCoPartner', description: 'Browse additional companion profiles on RentCoPartner and review listed services, location, availability and rates before you send a booking request.', noIndex: true }) },
    ],
  },
  { path: '*', ...notFoundRoute(() => import('./pages/NotFoundPage.jsx')) },
];
