import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './components/AppLayout';
import Home from './pages/Home';
import Browse from './pages/Browse';
import BookingsList from './pages/BookingsList';
import Login from './pages/Login';
import { ConversationPage, DateCompanionPage, EventPartnerPage, FitnessPage, GamingPage, NetworkingPage, OtherPage, PhotoshootPage, TravelBuddyPage } from './pages/CategoryPages';
import FavoritesPage from './pages/FavoritesPage';
import MessagesPage from './pages/MessagesPage';
import ProfilePage from './pages/ProfilePage';
import SearchResultsPage from './pages/SearchResultsPage';
import MyProfilePage from './pages/MyProfilePage';
import DashboardPage from './pages/DashboardPage';
import WalletPage from './pages/WalletPage';
import { isAuthenticated } from './auth/auth';
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Home />} />
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/browse" element={<Browse />} />
          <Route path="/bookings" element={<BookingsList />} />
          <Route path="/search" element={<SearchResultsPage />} />
          <Route path="/people/:personId" element={<ProfilePage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
          <Route path="/messages" element={<MessagesPage />} />
          <Route path="/my-profile" element={<MyProfilePage />} />
          <Route path="/wallet" element={<WalletPage />} />
          <Route path="/date-companion" element={<DateCompanionPage />} />
          <Route path="/travel-buddy" element={<TravelBuddyPage />} />
          <Route path="/event-partner" element={<EventPartnerPage />} />
          <Route path="/conversation" element={<ConversationPage />} />
          <Route path="/fitness" element={<FitnessPage />} />
          <Route path="/networking" element={<NetworkingPage />} />
          <Route path="/photoshoot" element={<PhotoshootPage />} />
          <Route path="/gaming" element={<GamingPage />} />
          <Route path="/other" element={<OtherPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
