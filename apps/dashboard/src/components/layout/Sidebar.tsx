import { NavLink } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, Settings, Film } from 'lucide-react';
import clsx from 'clsx';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/trends', label: 'Trends', icon: TrendingUp, end: false },
  { to: '/admin', label: 'Admin', icon: Settings, end: false },
] as const;

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col gap-1 bg-white/5 backdrop-blur-xl border-r border-white/10 p-4 md:flex">
      <div className="mb-6 flex items-center gap-2 px-2 pt-2">
        <Film size={22} className="text-indigo-400" strokeWidth={1.75} />
        <span className="text-lg font-bold tracking-tight text-indigo-400">YB Trends</span>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
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
  );
}
