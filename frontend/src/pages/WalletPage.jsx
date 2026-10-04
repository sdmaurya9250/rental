import { useEffect, useState } from 'react';
import { ArrowDownToLine, ArrowUpFromLine, Wallet } from 'lucide-react';
import FeaturePage from '../components/FeaturePage';
import { getMyProfile, getStoredUser } from '../auth/auth';

function roleDetails(role) {
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
  return Number.isFinite(amount) ? `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—';
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
        if (active) setProfile({ ...(getStoredUser() || {}), ...(result?.profile || result || {}) });
      })
      .catch((error) => {
        if (active) setLoadError(error.message || 'Wallet profile details could not be loaded.');
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const role = profile.want_to || profile.wantTo || profile.accountIntent || '';
  const details = roleDetails(role);
  const balance = profile.wallet_balance ?? profile.walletBalance ?? profile.wallet?.balance;
  const earned = profile.total_earned ?? profile.totalEarned ?? profile.wallet?.total_earned;
  const transactions = Array.isArray(profile.transactions)
    ? profile.transactions
    : Array.isArray(profile.wallet?.transactions) ? profile.wallet.transactions : [];

  function handleAddMoney(event) {
    event.preventDefault();
    setTopUpMessage('');
    const amount = Number(topUpAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      setTopUpMessage('Enter an amount greater than ₹0.');
      return;
    }
    setTopUpMessage('The amount is ready, but adding money needs the wallet payment API to be connected. No funds were added.');
  }

  return (
    <FeaturePage title="My wallet" subtitle="See how your account role uses the RentCoPartner wallet.">
      <div className="w-full max-w-5xl space-y-5">
        {loadError && <p role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">{loadError}</p>}

        <section className="rounded-2xl bg-gradient-to-br from-violet-950 via-violet-800 to-fuchsia-700 p-6 text-white shadow-lg">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-violet-100">Wallet balance</p>
              <p className="mt-2 text-3xl font-extrabold">{loading ? '…' : formatMoney(balance)}</p>
              {!loading && balance == null && <p className="mt-2 text-xs text-violet-100">Balance will appear when wallet data is available.</p>}
            </div>
            <span className="rounded-xl bg-white/15 p-3"><Wallet className="h-6 w-6" /></span>
          </div>
          <div className="mt-6 flex flex-wrap gap-2">
            <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-semibold">Account role: {role || 'Not set'}</span>
            {details.canAdd && <span className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-violet-800"><ArrowDownToLine className="h-3.5 w-3.5" />Add money</span>}
            {details.canEarn && <span className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-fuchsia-800"><ArrowUpFromLine className="h-3.5 w-3.5" />Earn money</span>}
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2">
          {details.canAdd && <article className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
            <span className="inline-flex rounded-xl bg-violet-50 p-2.5 text-violet-700"><ArrowDownToLine className="h-5 w-5" /></span>
            <h2 className="mt-3 font-bold text-[#211a35]">Add money</h2>
            <p className="mt-1 text-sm leading-relaxed text-[#706a80]">{details.canEarn ? 'Add wallet funds for bookings, and earn money when you provide a service.' : details.description}</p>
            <form onSubmit={handleAddMoney} className="mt-4 space-y-3">
              <label htmlFor="wallet-top-up-amount" className="block text-xs font-semibold text-[#40394f]">Amount (₹)</label>
              <div className="flex gap-2">
                <input id="wallet-top-up-amount" type="number" min="1" step="1" inputMode="decimal" value={topUpAmount} onChange={(event) => { setTopUpAmount(event.target.value); setTopUpMessage(''); }} placeholder="Enter amount" className="min-w-0 flex-1 rounded-lg border border-[#e4dff0] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-violet-300" />
                <button type="submit" className="shrink-0 rounded-lg bg-violet-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-800">Add money</button>
              </div>
              {topUpMessage && <p role="status" className="text-xs text-amber-800">{topUpMessage}</p>}
            </form>
          </article>}
          {details.canEarn && <article className="rounded-2xl border border-fuchsia-100 bg-white p-5 shadow-sm">
            <span className="inline-flex rounded-xl bg-fuchsia-50 p-2.5 text-fuchsia-700"><ArrowUpFromLine className="h-5 w-5" /></span>
            <h2 className="mt-3 font-bold text-[#211a35]">Your earnings</h2>
            <p className="mt-1 text-2xl font-extrabold text-[#211a35]">{loading ? '…' : formatMoney(earned)}</p>
            <p className="mt-1 text-sm text-[#706a80]">{details.canAdd ? 'Earnings from your RentCoPartner services.' : details.description}</p>
          </article>}
        </section>

        <section className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
          <h2 className="font-bold text-[#211a35]">Recent transactions</h2>
          {transactions.length ? <div className="mt-3 divide-y divide-violet-50">
            {transactions.map((transaction, index) => <div key={transaction.id || index} className="flex items-center justify-between gap-3 py-3 text-sm">
              <div><p className="font-semibold text-[#211a35]">{transaction.description || transaction.type || 'Wallet transaction'}</p><p className="text-xs text-[#827b95]">{transaction.created_at || transaction.date || ''}</p></div>
              <span className="font-bold text-[#211a35]">{formatMoney(transaction.amount)}</span>
            </div>)}
          </div> : <p className="mt-2 text-sm text-[#827b95]">No transactions to show yet.</p>}
        </section>
      </div>
    </FeaturePage>
  );
}
