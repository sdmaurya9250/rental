import { useNavigate, useSearchParams } from 'react-router-dom';
import AuthModal from '../components/AuthModal';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialMode = searchParams.get('mode') === 'register' ? 'register' : 'login';
  return (
    <div className="min-h-screen bg-[#0b0c10]">
      <AuthModal isOpen initialMode={initialMode} onClose={() => navigate('/')} onLogin={() => navigate('/', { replace: true })} />
    </div>
  );
}
