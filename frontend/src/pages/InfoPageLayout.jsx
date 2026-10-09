import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import HomeHeader from '../components/HomeHeader';
import HomeFooter from '../components/HomeFooter';

const PAGE_LINKS = [
  ['/privacy-policy', 'Privacy Policy'],
  ['/terms-and-conditions', 'Terms & Conditions'],
  ['/refund-policy', 'Refund Policy'],
  ['/help', 'Help'],
  ['/contact', 'Contact Us'],
];

export default function InfoPageLayout({ title, description, icon: Icon, children }) {
  return (
    <div className="min-h-screen bg-[#fcfaff] font-sans text-[#16132a]">
      <HomeHeader />

      <main className="mx-auto max-w-4xl px-5 py-10 sm:px-8 sm:py-14">
        <div className="mb-8 rounded-3xl bg-gradient-to-r from-[#8a1cf7] to-[#c800d8] p-6 text-white shadow-lg shadow-violet-200 sm:p-8">
          <span className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white/15"><Icon className="h-5 w-5" /></span>
          <h1 className="text-3xl font-black tracking-tight sm:text-4xl">{title}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/90">{description}</p>
        </div>

        <div className="space-y-4">{children}</div>

        <nav aria-label="Policies and help" className="mt-8 rounded-2xl border border-violet-100 bg-white p-5 sm:p-6">
          <h2 className="font-bold">More information</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {PAGE_LINKS.map(([to, label]) => (
              <Link key={to} to={to} className="inline-flex items-center gap-1 rounded-full bg-violet-50 px-3 py-2 text-xs font-semibold text-violet-700 transition hover:bg-violet-100">
                {label}<ArrowRight className="h-3 w-3" />
              </Link>
            ))}
          </div>
        </nav>
      </main>

      <HomeFooter />
    </div>
  );
}

export function InfoSection({ title, children }) {
  return (
    <section className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="text-base font-bold text-[#20183a]">{title}</h2>
      <p className="mt-2 text-sm leading-7 text-gray-600">{children}</p>
    </section>
  );
}
