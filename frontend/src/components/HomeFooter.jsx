import { Heart } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const SERVICE_LINKS = ['Movie Partner', 'In-Person Meeting', 'Elder Care', 'Hangingout'];

export default function HomeFooter() {
  const { pathname } = useLocation();
  const sectionHref = (id) => pathname === '/' ? `#${id}` : `/#${id}`;

  return (
    <footer className="z-10 w-full border-t border-violet-100/60 bg-white">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-8 px-6 py-10 md:grid-cols-5">
        <div className="col-span-2 md:col-span-1">
          <div className="mb-3 flex items-center space-x-2">
            <Heart className="h-6 w-6 fill-pink-500 text-pink-500" />
            <span className="text-lg font-extrabold text-[#16132a]">RentCoPartner</span>
          </div>
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
          <h5 className="mb-3 text-xs font-bold uppercase tracking-wider text-[#16132a]">Account</h5>
          <ul className="space-y-2 text-xs text-gray-500">
            <li><Link to="/login" className="transition hover:text-violet-600">Login</Link></li>
            <li><Link to="/login?mode=register" className="transition hover:text-violet-600">Sign Up</Link></li>
            <li><a href="https://t.me" target="_blank" rel="noreferrer" className="transition hover:text-violet-600">Telegram</a></li>
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
      </div>
      <div className="border-t border-violet-100/60 py-4 text-center text-[11px] text-gray-400">© {new Date().getFullYear()} RentCoPartner. All rights reserved.</div>
    </footer>
  );
}
