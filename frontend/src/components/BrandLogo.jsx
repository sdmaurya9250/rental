import { Link } from 'react-router-dom';

export default function BrandLogo({ dark = false, className = '', onClick }) {
  const wordmarkColor = dark ? 'text-white' : 'text-slate-900';

  return (
    <Link to="/" onClick={onClick} className={`group inline-flex items-center gap-3 whitespace-nowrap transition-transform hover:scale-[1.02] ${className}`}>
      <span className="relative flex items-center justify-center rounded-xl border border-slate-100 bg-white p-2 shadow-sm transition-shadow group-hover:shadow-md">
        <span className="relative flex -space-x-2">
          <span className="h-5 w-5 rounded-full bg-gradient-to-tr from-pink-600 to-rose-400 opacity-90 shadow-sm" />
          <span className="h-5 w-5 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 opacity-90 mix-blend-multiply" />
        </span>
      </span>


<span className={`text-xl font-extrabold tracking-[-0.045em] -ml-2 leading-none ${wordmarkColor}`}>
  Rent
  <span className="bg-gradient-to-r from-pink-500 via-rose-500 to-purple-600 bg-clip-text text-transparent">
    CoPartner
  </span>
</span>

    </Link>
  );
}
