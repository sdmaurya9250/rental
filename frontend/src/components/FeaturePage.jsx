export default function FeaturePage({ title, subtitle, children }) {
  return <section className="min-h-full bg-[#f5f3ff] px-4 py-5 sm:px-6 sm:py-6 xl:px-8"><div className="mx-auto w-full max-w-[1600px]">{(title || subtitle) && <header className="mb-5 sm:mb-6">{title && <h1 className="text-xl font-bold text-[#171426] sm:text-2xl">{title}</h1>}{subtitle && <p className="mt-1 text-sm text-[#706a80]">{subtitle}</p>}</header>}{children}</div></section>;
}
