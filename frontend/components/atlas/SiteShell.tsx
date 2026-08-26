import Link from 'next/link';
import { API_BASE_URL, HAS_REMOTE_API } from '../../lib/atlas';

const navItems = [
  { href: '/atlas', label: 'Atlas' },
  { href: '/civilizations', label: 'Civilizations' },
  { href: '/places', label: 'Places' },
  { href: '/sources', label: 'Sources' },
  { href: '/entities/trajan', label: 'Entity dossier' },
];

export function SiteShell({
  children,
}: Readonly<{
  children: React.ReactNode;
  title: string;
  subtitle: string;
}>) {
  return (
    <div className="min-h-screen px-4 py-4 md:px-6 md:py-5">
      <header className="mb-5 rounded-[28px] border border-white/10 bg-black/20 px-5 py-4 shadow-[0_30px_80px_rgba(0,0,0,0.28)] backdrop-blur-xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-400/30 bg-cyan-400/10 text-sm font-semibold tracking-[0.18em] text-cyan-200">
              CA
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Historical operations dashboard</div>
              <div className="mt-1 text-lg font-semibold text-white">Civil Atlas</div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {HAS_REMOTE_API ? (
              <a
                className="inline-flex items-center rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-slate-200 transition hover:border-cyan-300/40 hover:text-white"
                href={`${API_BASE_URL}/docs`}
                rel="noreferrer"
                target="_blank"
              >
                API docs
              </a>
            ) : (
              <span className="rounded-full border border-dashed border-white/10 px-4 py-2 text-sm text-slate-500">
                Seed-only demo
              </span>
            )}
            <span className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-400">
              Approximate boundaries labeled
            </span>
          </div>
        </div>
        <nav className="mt-4 flex flex-wrap gap-2">
          {navItems.map((item) => (
            <Link
              className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-slate-300 transition hover:border-cyan-300/40 hover:text-white"
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
