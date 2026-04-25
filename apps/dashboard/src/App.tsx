import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Shell from '@/components/layout/Shell';

const OverviewPage = lazy(() => import('@/pages/OverviewPage'));
const TrendsPage = lazy(() => import('@/pages/TrendsPage'));
const TrendDetailPage = lazy(() => import('@/pages/TrendDetailPage'));
const AdminPage = lazy(() => import('@/pages/AdminPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: true,
    },
  },
});

function PageFallback() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Shell />}>
            <Route
              index
              element={
                <Suspense fallback={<PageFallback />}>
                  <OverviewPage />
                </Suspense>
              }
            />
            <Route
              path="trends"
              element={
                <Suspense fallback={<PageFallback />}>
                  <TrendsPage />
                </Suspense>
              }
            />
            <Route
              path="trends/:query"
              element={
                <Suspense fallback={<PageFallback />}>
                  <TrendDetailPage />
                </Suspense>
              }
            />
            <Route
              path="admin"
              element={
                <Suspense fallback={<PageFallback />}>
                  <AdminPage />
                </Suspense>
              }
            />
            <Route
              path="*"
              element={
                <Suspense fallback={<PageFallback />}>
                  <NotFoundPage />
                </Suspense>
              }
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
