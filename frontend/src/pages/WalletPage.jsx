import { useEffect, useMemo, useState } from 'react';
import { 
  Wallet, 
  PlusCircle, 
  HelpCircle, 
  ShieldCheck, 
  Zap, 
  Gift, 
  ArrowUpRight, 
  ArrowDownLeft, 
  Clock, 
  AlertCircle,
  ChevronRight,
  Sparkles,
  CreditCard
} from 'lucide-react';
import FeaturePage from '../components/FeaturePage';
import { getMyProfile, getStoredUser, getWalletTransactions, topUpWallet } from '../auth/auth';

const QUICK_AMOUNTS = [500, 1000, 2000, 5000];

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
  if (normalized === 'companion' || normalized === 'become') {
    return {
      title: 'Earn as a RentCoPartner',
      description: 'Your earnings from completed bookings will be shown here.',
      canAdd: false,
      canEarn: true,
    };
  }
  return {
    title: 'Add money to book',
    description: 'Top up your wallet to pay for RentCoPartner bookings.',
    canAdd: true,
    canEarn: false,
  };
}

function formatMoney(value) {
  if (value == null || value === '') return '—';
  const amount = typeof value === 'string'
    ? Number(value.replace(/[₹,\s]/g, ''))
    : Number(value);
  return Number.isFinite(amount)
    ? `₹${amount.toLocaleString('en-IN')}`
    : '—';
}

function getTransactionAmount(transaction) {
  const rawAmount = transaction.amount ?? transaction.total_amount ?? transaction.value
    ?? transaction.transaction_amount ?? transaction.credit_amount ?? transaction.debit_amount;
  if (rawAmount == null || rawAmount === '') return null;
  const amount = typeof rawAmount === 'string'
    ? Number(rawAmount.replace(/[₹,\s]/g, ''))
    : Number(rawAmount);
  return Number.isFinite(amount) ? amount : null;
}

function summarizeTransactions(transactions) {
  return transactions.reduce((totals, transaction) => {
    const amount = getTransactionAmount(transaction);
    if (amount == null) return totals;

    const category = String(transaction.category || transaction.type || '').toLowerCase().replace(/[\s_-]/g, '');
    if (category.includes('refund')) {
      totals.refunded += Math.abs(amount);
    } else if (category.includes('spent') || category.includes('debit') || amount < 0) {
      totals.spent += Math.abs(amount);
    } else if (category.includes('added') || category.includes('credit') || category.includes('topup') || amount > 0) {
      totals.added += Math.abs(amount);
    }
    return totals;
  }, { added: 0, spent: 0, refunded: 0 });
}

export default function WalletPage() {
  const [profile, setProfile] = useState(() => getStoredUser() || {});
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [topUpAmount, setTopUpAmount] = useState('2000');
  const [topUpMessage, setTopUpMessage] = useState('');
  const [topUpError, setTopUpError] = useState(false);
  const [topUpLoading, setTopUpLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('All');
  const [transactions, setTransactions] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.allSettled([getWalletTransactions(), getMyProfile()])
      .then(([transactionResult, profileResult]) => {
        if (!active) return;
        const errors = [];
        if (transactionResult.status === 'fulfilled') {
          const body = transactionResult.value?.data || transactionResult.value;
          const transactionPayload = body?.transactions || body?.results || body;
          if (Array.isArray(transactionPayload)) setTransactions(transactionPayload);
          else errors.push('Transactions: the API returned an unexpected response.');
        } else {
          errors.push(`Transactions: ${transactionResult.reason?.message || 'could not be loaded'}`);
        }

        if (profileResult.status === 'fulfilled' && profileResult.value) {
          setProfile({ ...(getStoredUser() || {}), ...(profileResult.value?.profile || profileResult.value || {}) });
        }
        setLoadError(errors.join(' '));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [refreshKey]);

  const role = profile.want_to || profile.wantTo || profile.accountIntent || '';
  const details = getRoleDetails(role);
  const rawTransactions = transactions;
  const transactionTotals = useMemo(() => summarizeTransactions(rawTransactions), [rawTransactions]);
  const balance = transactionTotals.added + transactionTotals.refunded - transactionTotals.spent;
  const totalAdded = transactionTotals.added;
  const totalSpent = transactionTotals.spent;

  const filteredTransactions = rawTransactions.filter(tx => {
    if (activeTab === 'All') return true;
    if (activeTab === 'Added') return (tx.category === 'Added' || Number(tx.amount) > 0);
    if (activeTab === 'Spent') return (tx.category === 'Spent' || Number(tx.amount) < 0);
    if (activeTab === 'Refunded') return tx.category === 'Refunded';
    return true;
  });

  async function handleAddMoney(event) {
    event.preventDefault();
    setTopUpMessage('');
    const amount = Number(topUpAmount);

    if (!Number.isFinite(amount) || amount < 100) {
      setTopUpError(true);
      setTopUpMessage('Please enter an amount of at least ₹100.');
      return;
    }

    setTopUpLoading(true);
    setTopUpError(false);
    try {
      const result = await topUpWallet(amount);
      setTopUpMessage(result?.message || 'Money added to your wallet successfully.');
      setRefreshKey((key) => key + 1);
    } catch (error) {
      setTopUpError(true);
      setTopUpMessage(error.message || 'Unable to add money. Please try again.');
    } finally {
      setTopUpLoading(false);
    }
  }

  return (
    <FeaturePage 
      title="My Wallet" 
      subtitle="Manage your balance, add funds and view your transaction history."
      actionButton={
        <button className="inline-flex items-center gap-1.5 rounded-full border border-purple-200 bg-white px-4 py-2 text-xs font-semibold text-purple-700 shadow-sm hover:bg-purple-50 transition">
          <HelpCircle className="h-4 w-4" />
          Wallet Help
        </button>
      }
    >
      <div className="w-full max-w-6xl space-y-6 text-slate-800">
        
        {/* Error Banner */}
        {loadError && (
          <div role="alert" className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <AlertCircle className="h-5 w-5 shrink-0 text-amber-600" />
            <span>{loadError}</span>
          </div>
        )}

        {/* TOP SECTION: Hero Card + Stats Cards */}
        <div className="grid gap-6 lg:grid-cols-12">
          
          {/* Main Gradient Wallet Balance Card */}
          <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-purple-700 via-purple-600 to-fuchsia-500 p-6 sm:p-8 text-white shadow-lg lg:col-span-7 flex flex-col justify-between min-h-[180px]">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-purple-100 uppercase tracking-wider">Total Balance</p>
                <p className="mt-1 text-3xl font-extrabold sm:text-4xl tracking-tight">
                  {loading ? (
                    <span className="animate-pulse">Loading...</span>
                  ) : (
                    formatMoney(balance)
                  )}
                </p>
              </div>

              {/* Wallet Illustration Badge */}
              <div className="relative">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/20 backdrop-blur-md border border-white/30 shadow-inner">
                  <Wallet className="h-7 w-7 text-white" />
                </div>
              </div>
            </div>

            {/* Bottom Row inside Wallet Hero */}
            <div className="mt-6 flex items-center justify-between pt-2">
              <div className="inline-flex items-center gap-1.5 rounded-full bg-white/20 px-3 py-1 text-xs font-medium text-white backdrop-blur-md">
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-400 text-[10px] text-purple-900 font-bold">↑</span>
                Wallet balance
              </div>

              <button className="inline-flex items-center gap-1 rounded-xl bg-white/20 border border-white/30 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/30 transition backdrop-blur-md">
                View Details
              </button>
            </div>
          </section>

          {/* Quick Stats Grid */}
          <section className="grid grid-cols-3 gap-3 rounded-3xl border border-slate-100 bg-white p-4 shadow-sm lg:col-span-5 items-center">
            
            {/* Total Added */}
            <div className="flex flex-col items-center justify-center border-r border-slate-100 pr-2 text-center">
              <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <PlusCircle className="h-4 w-4" />
              </div>
              <span className="text-[11px] font-medium text-slate-400">Total Added</span>
              <span className="mt-0.5 text-base font-bold text-slate-800">{formatMoney(totalAdded)}</span>
              <span className="text-[10px] text-slate-400">All transactions</span>
            </div>

            {/* Total Spent */}
            <div className="flex flex-col items-center justify-center border-r border-slate-100 pr-2 text-center">
              <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                <ArrowUpRight className="h-4 w-4" />
              </div>
              <span className="text-[11px] font-medium text-slate-400">Total Spent</span>
              <span className="mt-0.5 text-base font-bold text-slate-800">{formatMoney(totalSpent)}</span>
              <span className="text-[10px] text-slate-400">All transactions</span>
            </div>

            {/* Available Balance */}
            <div className="flex flex-col items-center justify-center text-center">
              <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-purple-100 text-purple-600">
                <Clock className="h-4 w-4" />
              </div>
              <span className="text-[11px] font-medium text-slate-400">Available Balance</span>
              <span className="mt-0.5 text-base font-bold text-slate-800">{formatMoney(balance)}</span>
              <span className="text-[10px] text-slate-400">Current balance</span>
            </div>

          </section>
        </div>

        {/* MIDDLE SECTION: Top Up Form + Wallet Benefits */}
        <div className="grid gap-6 lg:grid-cols-12">
          
          {/* Add Money Card */}
          {details.canAdd && (
            <article className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm lg:col-span-7 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-600 text-white shadow-md shadow-purple-200">
                    <PlusCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">Add Money</h2>
                    <p className="text-xs text-slate-400">{details.description}</p>
                  </div>
                </div>

                {/* Quick Selection Buttons */}
                <div className="mt-6 flex flex-wrap gap-2">
                  {QUICK_AMOUNTS.map((amt) => {
                    const isSelected = String(amt) === String(topUpAmount);
                    return (
                      <button
                        key={amt}
                        type="button"
                        onClick={() => setTopUpAmount(String(amt))}
                        className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                          isSelected
                            ? 'border-2 border-purple-600 bg-purple-50 text-purple-700 shadow-sm'
                            : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        ₹{amt.toLocaleString('en-IN')}
                      </button>
                    );
                  })}
                </div>

                {/* Input + Action Form */}
                <form onSubmit={handleAddMoney} className="mt-5 space-y-3">
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="relative flex-1">
                      <span className="absolute inset-y-0 left-4 flex items-center text-sm font-semibold text-slate-400">₹</span>
                      <input
                        id="wallet-top-up-amount"
                        type="number"
                        min="100"
                        step="1"
                        inputMode="decimal"
                        value={topUpAmount}
                        onChange={(e) => {
                          setTopUpAmount(e.target.value);
                          setTopUpMessage('');
                        }}
                        placeholder="2000"
                        className="w-full rounded-2xl border border-slate-200 py-3 pl-8 pr-4 text-sm font-semibold text-slate-800 outline-none transition focus:border-purple-600 focus:ring-2 focus:ring-purple-100"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={topUpLoading}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl bg-purple-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-purple-200 transition hover:bg-purple-700 active:scale-95 disabled:cursor-wait disabled:opacity-60"
                    >
                      <PlusCircle className="h-4 w-4" /> {topUpLoading ? 'Adding…' : 'Add Money'}
                    </button>
                  </div>

                  {topUpMessage && (
                    <p role={topUpError ? 'alert' : 'status'} className={`text-xs font-medium ${topUpError ? 'text-rose-700' : 'text-emerald-700'}`}>
                      {topUpMessage}
                    </p>
                  )}
                </form>
              </div>

              {/* Supported Payment Options Footer */}
              <div className="mt-6 border-t border-slate-100 pt-4 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-slate-400" />
                  <span>Secure payments powered by trusted payment gateways</span>
                </div>
                <div className="flex items-center gap-2 font-bold tracking-wider text-slate-600 italic">
                  <span>UPI</span>
                  <span>VISA</span>
                  <span>RuPay</span>
                </div>
              </div>
            </article>
          )}

          {/* Wallet Benefits Card */}
          <article className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm lg:col-span-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-pink-100 text-pink-600">
                  <Gift className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">Wallet Benefits</h2>
                  <p className="text-xs text-slate-400">Enjoy a seamless booking experience</p>
                </div>
              </div>

              {/* Benefits List */}
              <div className="space-y-4 mt-4">
                <div className="flex items-center justify-between p-2 rounded-xl hover:bg-slate-50 transition">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-50 text-amber-500">
                      <Zap className="h-4 w-4" />
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-slate-800">Faster Bookings</h3>
                      <p className="text-[11px] text-slate-400">Instant payments, no delays</p>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300" />
                </div>

                <div className="flex items-center justify-between p-2 rounded-xl hover:bg-slate-50 transition">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-50 text-emerald-500">
                      <ShieldCheck className="h-4 w-4" />
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-slate-800">Secure Transactions</h3>
                      <p className="text-[11px] text-slate-400">Your payments are safe and encrypted</p>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300" />
                </div>

                <div className="flex items-center justify-between p-2 rounded-xl hover:bg-slate-50 transition">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-50 text-amber-500">
                      <Sparkles className="h-4 w-4" />
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-slate-800">Exclusive Offers</h3>
                      <p className="text-[11px] text-slate-400">Get special discounts and cashback</p>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300" />
                </div>
              </div>
            </div>
          </article>

        </div>

        {/* BOTTOM SECTION: Transaction History & Benefit Promo Banner */}
        <div className="grid gap-6 lg:grid-cols-12">
          
          {/* Transaction History Card */}
          <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm lg:col-span-7">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-purple-100 text-purple-600">
                  <Clock className="h-4 w-4" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">Transaction History</h2>
                  <p className="text-xs text-slate-400">View all your wallet transactions</p>
                </div>
              </div>

              {/* Transaction Filters */}
              <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1">
                {['All', 'Added', 'Spent', 'Refunded'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`rounded-lg px-3 py-1 text-xs font-medium transition ${
                      activeTab === tab
                        ? 'bg-purple-600 text-white shadow-xs'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            {/* List */}
            {filteredTransactions.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {filteredTransactions.map((tx, idx) => {
                  const amount = getTransactionAmount(tx);
                  const category = String(tx.category || '').toLowerCase();
                  const isCredit = ['added', 'refunded'].includes(category) || (amount != null && amount >= 0);
                  return (
                    <div key={tx.id || idx} className="flex items-center justify-between py-4 transition hover:bg-slate-50/60 rounded-xl px-2 -mx-2">
                      <div className="flex items-center gap-3">
                        <div className={`flex h-9 w-9 items-center justify-center rounded-full ${isCredit ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-500'}`}>
                          {isCredit ? <PlusCircle className="h-4 w-4" /> : <ArrowUpRight className="h-4 w-4" />}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-slate-800">
                            {tx.type || tx.description || 'Wallet Transaction'}
                          </p>
                          <p className="text-xs text-slate-400">
                            {tx.subtitle || tx.date || tx.created_at || 'Recent'}
                          </p>
                        </div>
                      </div>
                      <span className={`text-sm font-bold ${isCredit ? 'text-emerald-600' : 'text-red-500'}`}>
                        {amount == null ? '—' : `${isCredit ? '+' : '-'} ${formatMoney(Math.abs(amount))}`}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-12 text-center">
                <p className="text-sm text-slate-400">No transactions recorded yet in this category.</p>
              </div>
            )}
          </section>

          {/* Bottom Right Promo Banner Card */}
          <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-purple-600 via-purple-700 to-fuchsia-600 p-6 text-white shadow-md lg:col-span-5 flex flex-col justify-between min-h-[160px]">
            <div className="flex items-start justify-between">
              <div className="max-w-[70%]">
                <div className="flex items-center gap-1 text-amber-300 mb-1">
                  <Sparkles className="h-4 w-4 fill-amber-300" />
                  <span className="text-xs font-bold uppercase tracking-wider">Get More Benefits</span>
                </div>
                <p className="text-xs text-purple-100 leading-relaxed">
                  Maintain a higher wallet balance for exclusive offers and priority booking.
                </p>
              </div>

              {/* Wallet illustration */}
              <div className="rounded-2xl bg-white/10 p-3 backdrop-blur-md">
                <Wallet className="h-8 w-8 text-amber-300" />
              </div>
            </div>

            <div className="mt-4">
              <button className="inline-flex items-center gap-1 rounded-xl bg-white px-4 py-2 text-xs font-bold text-purple-700 shadow-sm transition hover:bg-purple-50">
                Learn More <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </section>

        </div>

      </div>
    </FeaturePage>
  );
}