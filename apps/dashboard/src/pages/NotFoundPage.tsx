import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-gray-100">
      <h1 className="text-6xl font-bold text-accent-400">404</h1>
      <p className="text-xl text-gray-400">Page not found</p>
      <Link
        to="/"
        className="mt-2 px-4 py-2 rounded-lg bg-accent-600 hover:bg-accent-500 transition-colors text-white text-sm"
      >
        Back to Overview
      </Link>
    </div>
  );
}
