import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import AuthModal from './AuthModal';
import BrandLogo from './BrandLogo';

const SERVICE_LINKS = ['Movie Partner', 'In-Person Meeting', 'Elder Care', 'Hangingout'];
const SOCIAL_LINKS = [
  {
    name: 'Facebook',
    href: 'https://www.facebook.com/',
    color: '#1877F2',
    icon: (
      <path
        d="M13.5 21v-8h2.7l.4-3h-3.1V8.1c0-.9.3-1.5 1.6-1.5h1.6V3.9c-.3 0-1.3-.1-2.4-.1-2.4 0-4.1 1.5-4.1 4.2V10H7.6v3h2.7v8h3.2Z"
        fill="currentColor"
        stroke="none"
      />
    ),
  },
  {
    name: 'Instagram',
    href: 'https://www.instagram.com/',
    color: '#E4405F',
    icon: (
      <>
        <rect x="3" y="3" width="18" height="18" rx="5" />
        <circle cx="12" cy="12" r="4" />
        <circle
          cx="18"
          cy="6"
          r=".8"
          fill="currentColor"
          stroke="none"
        />
      </>
    ),
  },
  {
    name: 'X',
    href: 'https://x.com/',
    color: '#000000',
    icon: (
      <path
        d="M18.9 3H22l-6.8 7.8L23.2 21h-6.3L12 14.7 6.4 21H3.2l7.3-8.4L2.8 3h6.5l4.5 5.9L18.9 3Zm-1.1 16h1.7L8.3 4.9H6.5L17.8 19Z"
        fill="currentColor"
        stroke="none"
      />
    ),
  },
  {
    name: 'LinkedIn',
    href: 'https://www.linkedin.com/',
    color: '#0A66C2',
    icon: (
      <>
        <path d="M5 9v10M5 5v.01M9 19v-6a4 4 0 0 1 8 0v6M9 10v9" />
        <circle
          cx="5"
          cy="5"
          r="1"
          fill="currentColor"
          stroke="none"
        />
      </>
    ),
  },
  {
    name: 'WhatsApp',
    href: 'https://www.whatsapp.com/',
    color: '#25D366',
    icon: (
      <>
        <path d="M20.2 11.7a8.2 8.2 0 0 1-12.1 7.2L4 20l1.1-4A8.2 8.2 0 1 1 20.2 11.7Z" />
        <path d="M9 8.5c.4 2.4 2.1 4.1 4.5 4.6l1.1-1.1 2 .9c-.1 1.5-1.2 2.2-2.5 2.1-3.5-.3-6.5-3.3-6.8-6.8-.1-1.3.6-2.4 2.1-2.5l.9 2L9 8.5Z" />
      </>
    ),
  },
];

export default function HomeFooter() {
  const [authMode, setAuthMode] = useState(null);
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const sectionHref = (id) => pathname === '/' ? `#${id}` : `/#${id}`;
  const handleLogin = (data) => {
    setAuthMode(null);
    navigate('/dashboard', { replace: true, state: { user: data?.user } });
  };

  return (
    <footer className="z-10 w-full border-t border-violet-100/60 bg-white">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-8 px-6 py-10 md:grid-cols-5">
        <div className="col-span-2 md:col-span-1">
          <BrandLogo className="mb-3 gap-2" compact />
          <p className="max-w-xs text-xs leading-relaxed text-gray-500">Find trusted companions for every occasion, or join and earn on your own terms.</p>
        </div>

        <div>
          <h5 className="mb-3 text-xs font-bold uppercase tracking-wider text-[#16132a]">Quick Links</h5>
          <ul className="space-y-2 text-xs text-gray-500">
            <li><Link to="/" className="transition hover:text-violet-600">Home</Link></li>
            <li><Link to="/browse" className="transition hover:text-violet-600">Browse</Link></li>
            <li><a href={sectionHref('why-join')} className="transition hover:text-violet-600">Why Join</a></li>
            <li><a href={sectionHref('how-it-works')} className="transition hover:text-violet-600">How It Works</a></li>
          </ul>
        </div>

        <div>
          <h5 className="mb-3 text-xs font-bold uppercase tracking-wider text-[#16132a]">Services</h5>
          <ul className="space-y-2 text-xs text-gray-500">
            {SERVICE_LINKS.map((service) => <li key={service}><a href={sectionHref('services')} className="transition hover:text-violet-600">{service}</a></li>)}
          </ul>
        </div>

        <div>
          <h5 className="mb-3 text-xs font-bold uppercase tracking-wider text-[#16132a]">Policies & Help</h5>
          <ul className="space-y-2 text-xs text-gray-500">
            <li><Link to="/privacy-policy" className="transition hover:text-violet-600">Privacy Policy</Link></li>
            <li><Link to="/terms-and-conditions" className="transition hover:text-violet-600">Terms & Conditions</Link></li>
            <li><Link to="/refund-policy" className="transition hover:text-violet-600">Refund Policy</Link></li>
            <li><Link to="/help" className="transition hover:text-violet-600">Help</Link></li>
          </ul>
        </div>

<div className="p-4 sm:p-5">
  <h5 className="mb-4 text-sm font-bold text-[#16132a]">
    Connect With Us
  </h5>

  <div className="flex items-center justify-between gap-3">
    {SOCIAL_LINKS.map((social) => (
      <a
        key={social.name}
        href={social.href}
        target="_blank"
        rel="noreferrer"
        aria-label={`Visit ${social.name}`}
        title={social.name}
        style={{ color: social.color }}
        className="
          flex h-9 w-9 items-center justify-center
          rounded-xl
          transition-all duration-200
          hover:-translate-y-1
          hover:scale-110
          hover:bg-slate-50
        "
      >
        <svg
          className="h-5 w-5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          {social.icon}
        </svg>
      </a>
    ))}
  </div>
</div>
      </div>
      <div className="border-t border-violet-100/60 py-4 text-center text-[11px] text-gray-400">© {new Date().getFullYear()} RentCoPartner. All rights reserved.</div>
      {authMode && <AuthModal isOpen initialMode={authMode} onClose={() => setAuthMode(null)} onLogin={handleLogin} />}
    </footer>
  );
}
