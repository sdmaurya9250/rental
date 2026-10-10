import {
  CircleHelp,
  ShieldCheck,
  CreditCard,
  FileText,
  UserRound,
  MapPin,
  CalendarCheck,
  MessageCircle,
  AlertCircle,
  Mail,
  Phone,
} from 'lucide-react';
import InfoPageLayout from './InfoPageLayout';
import Seo from '../components/Seo';

export default function HelpPage() {
  const categories = [
    {
      icon: UserRound,
      title: 'Getting Started',
      description: 'Account, registration, profile and basic usage',
    },
    {
      icon: ShieldCheck,
      title: 'Safety & Security',
      description: 'Account safety, privacy and reporting',
    },
    {
      icon: CreditCard,
      title: 'Payments & Wallet',
      description: 'Wallet, payments, refunds and transactions',
    },
    {
      icon: FileText,
      title: 'Policies',
      description: 'Terms, privacy and platform guidelines',
    },
  ];

  const popularTopics = [
    {
      icon: UserRound,
      question: 'How do I create a RentCoPartner account?',
      answer:
        'Open the registration page and provide the required account information. After registration, complete your profile to start using RentCoPartner.',
    },
    {
      icon: CreditCard,
      question: 'How does the wallet work?',
      answer:
        'You can add money to your RentCoPartner wallet using the available payment methods. Your wallet balance can then be used for eligible bookings and services.',
    },
    {
      icon: CalendarCheck,
      question: 'How do I make a booking?',
      answer:
        'Find a suitable profile, review the available details and booking information, select the required date and time, and confirm the booking using the available payment option.',
    },
    {
      icon: MapPin,
      question: 'Why is my location not detected?',
      answer:
        'Make sure your browser has permission to access your location. You can also enter your city or location manually if you do not want to use location detection.',
    },
    {
      icon: MessageCircle,
      question: 'How do I contact another user?',
      answer:
        'Use the messaging or communication features available on the relevant profile or booking. Do not share passwords, OTPs, UPI PINs, or other sensitive information.',
    },
    {
      icon: CircleHelp,
      question: 'Where can I see my bookings?',
      answer:
        'Sign in to your account and open My Bookings to view your upcoming, completed, cancelled, or other available booking information.',
    },
  ];

  return (
    <>
    <Seo title="Help & FAQs | RentCoPartner" description="Find answers about RentCoPartner accounts, companion profiles, bookings, wallet payments, cancellations, safety, privacy and getting support." />
    <InfoPageLayout
      title="How can we help you?"
      description="Find answers and get support for your RentCoPartner account."
      icon={CircleHelp}
    >
      {/* Help Categories */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {categories.map((category) => {
          const Icon = category.icon;

          return (
            <div
              key={category.title}
              className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-pink-200 hover:shadow-md"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-pink-100 to-purple-100 text-pink-600">
                <Icon size={20} />
              </div>

              <h3 className="text-sm font-semibold text-slate-900">
                {category.title}
              </h3>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                {category.description}
              </p>
            </div>
          );
        })}
      </div>

      {/* Main Help Area */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Popular Topics */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-5">
            <h2 className="text-lg font-bold text-slate-900">
              Popular Topics
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Quick answers to common questions
            </p>
          </div>

          <div className="space-y-2">
            {popularTopics.map((topic) => {
              const Icon = topic.icon;

              return (
                <details
                  key={topic.question}
                  className="group rounded-xl border border-slate-100 bg-slate-50/70 transition hover:border-pink-100 hover:bg-pink-50/30"
                >
                  <summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-3.5 text-sm font-medium text-slate-800">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-pink-500 shadow-sm">
                      <Icon size={16} />
                    </span>

                    <span className="flex-1">{topic.question}</span>

                    <span className="text-slate-400 transition-transform group-open:rotate-180">
                      ↓
                    </span>
                  </summary>

                  <div className="border-t border-slate-100 px-4 pb-4 pt-3 pl-[60px] text-sm leading-6 text-slate-600">
                    {topic.answer}
                  </div>
                </details>
              );
            })}
          </div>
        </div>

        {/* Right Side */}
        <div className="space-y-4">
          {/* Emergency Support */}
          <div className="rounded-2xl border border-red-200 bg-red-50 p-5">
            <div className="flex gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
                <AlertCircle size={18} />
              </div>

              <div>
                <h3 className="text-sm font-bold text-red-700">
                  Safety & Emergency Support
                </h3>

                <p className="mt-2 text-xs leading-5 text-red-600">
                  If you are in immediate danger, contact your local emergency
                  services first. RentCoPartner support should not be used as a
                  replacement for emergency services.
                </p>

                <div className="mt-3 space-y-1 text-xs font-medium text-red-700">
                  <p>India Emergency: 112</p>
                  <p>Police: 100</p>
                  <p>Women Helpline: 1091</p>
                </div>
              </div>
            </div>
          </div>

          {/* Direct Support */}
          <div className="overflow-hidden rounded-2xl bg-gradient-to-br from-pink-600 via-purple-600 to-fuchsia-600 p-6 text-white shadow-lg">
            <h3 className="text-lg font-bold">Need Direct Support?</h3>

            <p className="mt-1 text-sm text-white/80">
              Our support team can help with account, booking, wallet and
              payment-related questions.
            </p>

            <div className="mt-5 space-y-3">
              <a
                href="tel:+919XXXXXXXXX"
                className="flex items-center gap-3 text-sm transition hover:text-white/80"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/15">
                  <Phone size={16} />
                </span>
                <span>+91 XXXXXXXXXX</span>
              </a>

              <a
                href="mailto:support@rentcopartner.com"
                className="flex items-center gap-3 text-sm transition hover:text-white/80"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/15">
                  <Mail size={16} />
                </span>
                <span>support@rentcopartner.com</span>
              </a>
            </div>

            <div className="mt-5 border-t border-white/20 pt-4 text-xs text-white/70">
              Support hours: Monday – Saturday, 10 AM – 6 PM
            </div>
          </div>
        </div>
      </div>

      {/* Additional Help */}
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <a
          href="/privacy-policy"
          className="rounded-xl border border-slate-200 bg-white p-4 text-center transition hover:border-pink-200 hover:shadow-sm"
        >
          <ShieldCheck className="mx-auto text-purple-500" size={20} />
          <h3 className="mt-2 text-sm font-semibold text-slate-900">
            Privacy Policy
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Learn how your information is handled
          </p>
        </a>

        <a
          href="/terms"
          className="rounded-xl border border-slate-200 bg-white p-4 text-center transition hover:border-pink-200 hover:shadow-sm"
        >
          <FileText className="mx-auto text-purple-500" size={20} />
          <h3 className="mt-2 text-sm font-semibold text-slate-900">
            Terms & Conditions
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Rules for using RentCoPartner
          </p>
        </a>

        <a
          href="/refund-policy"
          className="rounded-xl border border-slate-200 bg-white p-4 text-center transition hover:border-pink-200 hover:shadow-sm"
        >
          <CreditCard className="mx-auto text-purple-500" size={20} />
          <h3 className="mt-2 text-sm font-semibold text-slate-900">
            Refund Policy
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Wallet, bookings and refunds
          </p>
        </a>
      </div>
    </InfoPageLayout>
    </>
  );
}
