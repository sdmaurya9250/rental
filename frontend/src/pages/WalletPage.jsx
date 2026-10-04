import { useEffect, useState } from 'react';
import { 
  ArrowDownToLine, 
  ArrowUpFromLine, 
  Wallet, 
  PlusCircle, 
  Clock, 
  AlertCircle 
} from 'lucide-react';
import FeaturePage from '../components/FeaturePage';
import { getMyProfile, getStoredUser } from '../auth/auth';

const QUICK_AMOUNTS = [500, 1000, 2000];

function getRoleDetails(role) {
  const normalized = String(role || '').trim().toLowerCase();
  if (normalized === 'both') {
    return {
      title: 'Earn and add money',
      description: 'Use your wallet to pay for bookings as a Finder and receive earnings as a RentCoPartner.',
      canAdd: true,
      canEarn: true,
    };
  }
  if (normalized === 'become a rentpeople' || normalized === 'become') {
    return {
      title: 'Earn as a RentCoPartner',
      description: 'Your earnings from completed bookings will be shown here.',
      canAdd: false,
      canEarn: true,
    };
  }
  return {
    title: 'Add money to book',
    description: 'Add funds to your wallet to pay for RentCoPartner bookings.',
    canAdd: true,
    canEarn: false,
  };
}

function formatMoney(value) {
  if (value == null || value === '') return '—';
  const amount = Number(value);
  return Number.isFinite(amount)
    ? `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
    : '—';
}

export default function WalletPage() {
  const [profile, setProfile] = useState(() => getStoredUser() || {});
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [topUpAmount, setTopUpAmount] = useState('');
  const [topUpMessage, setTopUpMessage] = useState('');

  useEffect(() => {
    let active = true;
    getMyProfile()
      .then((result) => {
        if (active) {
          setProfile({ ...(getStoredUser() || {}), ...(result?.profile || result || {}) });
        }
      })
      .catch((error) => {
        if (active) {
          setLoadError(error.message || 'Wallet profile details could not be loaded.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const role = profile.want_to || profile.wantTo || profile.accountIntent || '';
  const details = getRoleDetails(role);
  const balance = profile.wallet_balance ?? profile.walletBalance ?? profile.wallet?.balance;
  const earned = profile.total_earned ?? profile.totalEarned ?? profile.wallet?.total_earned;
  const transactions = Array.isArray(profile.transactions)
    ? profile.transactions
    : Array.isArray(profile.wallet?.transactions)
    ? profile.wallet.transactions
    : [];

  function handleAddMoney(event) {
    event.preventDefault();
    setTopUpMessage('');
    const amount = Number(topUpAmount);

    if (!Number.isFinite(amount) || amount <= 100) {
      setTopUpMessage('Please enter an amount greater than ₹100.');
      return;
    }

    setTopUpMessage('Payment gateway integration required. No funds were added.');
  }

  return (
    <FeaturePage 
      title="My Wallet" 
      subtitle="Manage your balance, add funds, and view earnings in one place."
    >
      <div className="w-full max-w-5xl space-y-6">
        {/* Error Banner */}
        {loadError && (
          <div role="alert" className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <AlertCircle className="h-5 w-5 shrink-0 text-amber-600" />
            <span>{loadError}</span>
          </div>
        )}

        {/* Balance Header Card */}
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-violet-900 via-violet-800 to-fuchsia-800 p-6 text-white shadow-md sm:p-8">
<div className="flex items-center justify-between gap-3">
  <div>
    <p className="text-[11px] font-medium tracking-wide text-violet-200">Total Balance</p>
    <p className="mt-0.5 text-xl font-semibold sm:text-2xl">
      {loading ? (
        <span className="animate-pulse">Loading...</span>
      ) : (
        balance == null ? '₹0.00' : formatMoney(balance)
      )}
    </p>
    {!loading && balance == null && (
      <p className="mt-0.5 text-[11px] text-violet-200">Balance will update once setup is complete.</p>
    )}
  </div>
  <div className="rounded-xl bg-white/10 p-2.5 backdrop-blur-md">
    <Wallet className="h-5 w-5 text-white" />
  </div>
</div>
        </section>

        {/* Action Grid */}
        <section className="grid gap-6 md:grid-cols-2">
          {/* Top Up Card */}
          {details.canAdd && (
            <article className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div>
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-violet-50 p-2.5 text-violet-700">
                    <ArrowDownToLine className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">Add Money</h2>
                    <p className="text-xs text-slate-500">Top up your wallet balance</p>
                  </div>
                </div>

                <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                  {details.canEarn 
                    ? 'Add wallet funds to pay for bookings anytime.' 
                    : details.description}
                </p>

                {/* Quick Selection Chips */}
                <div className="mt-4 flex flex-wrap gap-2">
                  {QUICK_AMOUNTS.map((amt) => (
                    <button
                      key={amt}
                      type="button"
                      onClick={() => setTopUpAmount(String(amt))}
                      className="rounded-lg border border-violet-100 bg-violet-50/50 px-2.5 py-1 text-xs font-medium text-violet-700 transition hover:bg-violet-100 hover:text-violet-800"
                    >
                      +₹{amt}
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleAddMoney} className="mt-5 space-y-3">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <span className="absolute inset-y-0 left-3 flex items-center text-sm font-medium text-slate-400">₹</span>
                    <input
                      id="wallet-top-up-amount"
                      type="number"
                      min="100.01"
                      step="0.01"
                      inputMode="decimal"
                      value={topUpAmount}
                      onChange={(e) => {
                        setTopUpAmount(e.target.value);
                        setTopUpMessage('');
                      }}
                      placeholder="More than ₹100"
                      className="w-full rounded-xl border border-slate-200 pl-7 pr-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
                    />
                  </div>
                  <button
                    type="submit"
                    className="inline-flex items-center gap-1.5 shrink-0 rounded-xl bg-violet-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-violet-800 active:bg-violet-900"
                  >
                    <PlusCircle className="h-4 w-4" /> Add
                  </button>
                </div>

                {topUpMessage && (
                  <p role="status" className="text-xs font-medium text-amber-700">
                    {topUpMessage}
                  </p>
                )}
              </form>
            </article>
          )}

          {/* Earnings Card */}
          {details.canEarn && (
            <article className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div>
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-fuchsia-50 p-2.5 text-fuchsia-700">
                    <ArrowUpFromLine className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">Total Earnings</h2>
                    <p className="text-xs text-slate-500">Income from completed bookings</p>
                  </div>
                </div>

                <div className="mt-4">
                  <p className="text-3xl font-black text-slate-900">
                    {loading ? <span className="animate-pulse text-lg text-slate-400">Loading...</span> : formatMoney(earned)}
                  </p>
                </div>
              </div>

              <p className="mt-4 text-sm text-slate-500 leading-relaxed">
                {details.canAdd 
                  ? 'Earnings accumulated through your RentCoPartner services.' 
                  : details.description}
              </p>
            </article>
          )}
        </section>

        {/* Recent Transactions Card */}
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <h2 className="text-base font-bold text-slate-900">Recent Transactions</h2>
            <Clock className="h-4 w-4 text-slate-400" />
          </div>

          {transactions.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {transactions.map((tx, idx) => {
                const isCredit = tx.type?.toLowerCase() === 'credit' || (tx.amount && Number(tx.amount) > 0);
                return (
                  <div key={tx.id || idx} className="flex items-center justify-between py-3.5 text-sm transition hover:bg-slate-50/50 rounded-lg px-2 -mx-2">
                    <div className="space-y-0.5">
                      <p className="font-semibold text-slate-800">
                        {tx.description || tx.type || 'Wallet Transaction'}
                      </p>
                      <p className="text-xs text-slate-400">
                        {tx.created_at || tx.date || 'Recent'}
                      </p>
                    </div>
                    <span className={`font-bold ${isCredit ? 'text-emerald-600' : 'text-slate-900'}`}>
                      {isCredit ? '+' : ''}{formatMoney(tx.amount)}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-8 text-center">
              <p className="text-sm text-slate-400">No transactions recorded yet.</p>
            </div>
          )}
        </section>
      </div>
    </FeaturePage>
  );
}
