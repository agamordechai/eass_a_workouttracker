import { useState, useEffect, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useAuth } from '../contexts/AuthContext';

export function Layout() {
  const { user } = useAuth();
  const [isDesktop, setIsDesktop] = useState(() =>
    window.matchMedia('(min-width: 1024px)').matches
  );
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia('(min-width: 1024px)');
    const handler = (e: MediaQueryListEvent) => {
      setIsDesktop(e.matches);
      if (e.matches) setMobileSidebarOpen(false);
    };
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);

  const sidebarOpen = isDesktop || mobileSidebarOpen;
  const handleCloseSidebar = useCallback(() => {
    if (!isDesktop) setMobileSidebarOpen(false);
  }, [isDesktop]);

  return (
    <div className="min-h-screen bg-background">
      {/* Reddit-style top navbar */}
      <header className="sticky top-0 z-40 h-12 bg-surface border-b border-border">
        <div className="flex items-center justify-between h-full px-4 lg:px-5">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMobileSidebarOpen((prev) => !prev)}
              className="w-8 h-8 lg:hidden flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-hover hover:text-text-primary transition-colors"
              aria-label="Toggle sidebar"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </button>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
            </div>
            <span className="text-base font-bold text-text-primary">Workout Tracker</span>
          </div>
          {user && (
            <div className="flex items-center gap-2">
              {user.picture_url ? (
                <img src={user.picture_url} alt="" className="w-8 h-8 rounded-full" referrerPolicy="no-referrer" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-surface-light border border-border flex items-center justify-center text-text-secondary text-xs font-bold">
                  {user.name?.[0]?.toUpperCase() || '?'}
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Body */}
      <div className="flex">
        <Sidebar isOpen={sidebarOpen} onClose={handleCloseSidebar} />
        <main className="flex-1 min-h-[calc(100vh-3rem)]">
          <div className="max-w-2xl mx-auto px-4 py-4 pb-5 lg:px-5 lg:py-5">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
