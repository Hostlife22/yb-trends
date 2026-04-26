import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Menu, X, LayoutDashboard, TrendingUp, Settings, Film } from 'lucide-react';
import clsx from 'clsx';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/trends', label: 'Trends', icon: TrendingUp, end: false },
  { to: '/admin', label: 'Admin', icon: Settings, end: false },
] as const;

export default function MobileNav() {
  const [open, setOpen] = useState(false);

  const close = () => setOpen(false);

  return (
    <>
      <button
        type="button"
        aria-label="Open navigation"
        onClick={() => setOpen(true)}
        className="fixed left-3 top-3 z-30 flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-slate-900/80 text-gray-300 backdrop-blur-md hover:bg-white/10 hover:text-white transition-colors md:hidden"
      >
        <Menu size={20} />
      </button>

      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm md:hidden"
          onClick={close}
          aria-hidden="true"
        />
      )}

      {/* Slide-in drawer */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-[70] flex w-64 flex-col gap-1 bg-slate-950 border-r border-white/10 p-4 shadow-2xl transition-transform duration-300 ease-in-out md:hidden',
          open ? 'translate-x-0' : '-translate-x-full pointer-events-none',
        )}
      >
        <div className="mb-6 flex items-center justify-between px-2 pt-2">
          <div className="flex items-center gap-2">
            <Film size={20} className="text-indigo-400" strokeWidth={1.75} />
            <span className="text-lg font-bold tracking-tight text-indigo-400">YB Trends</span>
          </div>
          <button
            type="button"
            aria-label="Close navigation"
            onClick={close}
            className="flex items-center justify-center rounded-xl p-1.5 text-gray-400 hover:bg-white/5 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={close}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'border-l-2 border-indigo-400 bg-indigo-500/10 pl-[10px] text-white'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white',
                )
              }
            >
              <Icon size={18} strokeWidth={1.75} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}
