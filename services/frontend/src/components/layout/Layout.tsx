import { useState, useEffect, useCallback } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { BottomNav } from './BottomNav';
import { PageTransition } from '../ui/PageTransition';

export function Layout() {
  const location = useLocation();
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
      <Header onMenuToggle={() => setMobileSidebarOpen((prev) => !prev)} />

      <div className="flex">
        <Sidebar isOpen={sidebarOpen} onClose={handleCloseSidebar} />
        <main className="flex-1 min-h-[calc(100vh-4rem)]">
          <div className="w-full max-w-5xl mx-auto px-4 py-6 pb-20 lg:px-8 lg:py-8 lg:pb-8">
            <AnimatePresence mode="wait">
              <PageTransition key={location.pathname}>
                <Outlet />
              </PageTransition>
            </AnimatePresence>
          </div>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
