import Link from 'next/link';
import { API_BASE_URL } from '../../lib/atlas';

const navItems = [
  { href: '/atlas', label: 'Atlas' },
  { href: '/civilizations', label: 'Civilizations' },
  { href: '/places', label: 'Places' },
  { href: '/sources', label: 'Sources' },
];

export function SiteShell({
  children,
  title,
  subtitle,
}: Readonly<{
  children: React.ReactNode;
  title: string;
  subtitle: string;
}>) {
  return (
    <div className="min-h-screen p-4 md:p-6">
      <header className="mb-5 rounded-[28px] border border-slate-300/70 bg-[rgba(255,250,242,0.82)] px-5 py-5 shadow-[0_24px_60px_rgba(61,45,18,0.08)] backdrop-blur">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-4xl">
            <p className="mb-2 text-xs uppercase tracking-[0.22em] text-[--muted]">
              Civil Atlas Operations Deck
            </p>
            <h1 className="font-serif text-4xl leading-none tracking-[-0.05em] md:text-6xl">
              {title}
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700 md:text-base">
              {subtitle}
            </p>
          </div>
          <a
            className="inline-flex items-center rounded-full border border-slate-300 bg-white/80 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-500 hover:text-slate-950"
            href={`${API_BASE_URL}/docs`}
            rel="noreferrer"
            target="_blank"
          >
            API docs
          </a>
        </div>
        <nav className="mt-5 flex flex-wrap gap-2">
          {navItems.map((item) => (
            <Link
              className="rounded-full border border-slate-300 bg-white/80 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-500 hover:text-slate-950"
              href={item.href}
              key={item.href}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      {children}
    </div>
  );
}
