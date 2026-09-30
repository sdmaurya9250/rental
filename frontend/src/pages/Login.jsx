import { useNavigate, useSearchParams } from 'react-router-dom';
import AuthModal from '../components/AuthModal';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialMode = searchParams.get('mode') === 'register' ? 'register' : 'login';

  // AuthModal calls this once sendLoginOtp/verifyLoginOtp/loginWithPassword/
  // registerUser resolves. `data` is the API response ({ token, user, ... });
  // authApi.js has already stored it in localStorage, so this only needs to
  // handle where the app goes next.
  function handleLoginSuccess(data) {
    navigate('/browse', { replace: true, state: { user: data?.user } });
  }

  return (
    <div className="min-h-screen bg-[#0b0c10]">
      <AuthModal isOpen initialMode={initialMode} onClose={() => navigate('/')} onLogin={handleLoginSuccess} />
    </div>
  );
}
