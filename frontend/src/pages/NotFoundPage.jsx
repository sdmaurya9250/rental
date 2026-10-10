import { Link } from 'react-router-dom';
import HomeHeader from '../components/HomeHeader';
import HomeFooter from '../components/HomeFooter';
import Seo from '../components/Seo';

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#fcfaff] font-sans text-[#16132a]">
      <Seo title="Page Not Found | RentCoPartner" description="This RentCoPartner page could not be found. Return home to explore companion profiles, social services and booking information. Browse our public pages." noIndex />
      <HomeHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-5 py-20 text-center">
        <p className="text-sm font-bold uppercase tracking-[0.2em] text-violet-600">404 · Page not found</p>
        <h1 className="mt-3 text-3xl font-black tracking-tight sm:text-5xl">We couldn’t find that page</h1>
        <p className="mt-4 max-w-xl text-sm leading-6 text-slate-600">The link may be outdated, or the page may have moved. Head back to RentCoPartner to explore companion services.</p>
        <Link to="/" className="mt-7 rounded-full bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] px-6 py-3 text-sm font-bold text-white shadow-md">Go to home</Link>
      </main>
      <HomeFooter />
    </div>
  );
}
