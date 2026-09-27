export default function FeaturePage({ title, subtitle, children }) {
  return <section className="min-h-full bg-[#f8f6ff] p-6 lg:p-8"><h1 className="text-2xl font-bold text-[#171426]">{title}</h1>{subtitle && <p className="mt-1 text-sm text-[#706a80]">{subtitle}</p>}<div className="mt-6">{children}</div></section>;
}
