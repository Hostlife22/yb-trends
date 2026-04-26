import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import MobileNav from './MobileNav';

export default function Shell() {
  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-950 via-gray-950 to-slate-900">
      <Sidebar />
      <MobileNav />

      <div className="flex flex-1 flex-col md:ml-64">
        <TopBar />

        <main className="flex-1 overflow-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
