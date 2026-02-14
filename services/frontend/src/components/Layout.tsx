import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { BottomTabs } from './BottomTabs';

export function Layout() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 h-12 bg-surface/70 backdrop-blur-xl border-b border-border/80">
        <div className="flex items-center justify-center h-full px-4 lg:px-6 relative">
          <span className="text-[17px] font-semibold text-text-primary tracking-tight">Workout Tracker</span>
        </div>
      </header>

      {/* Body */}
      <div className="flex">
        <Sidebar />
        <main className="flex-1 min-h-[calc(100vh-3rem)]">
          <div className="max-w-5xl mx-auto px-4 py-4 pb-32 lg:px-6 lg:py-6 lg:pb-6">
            <Outlet />
          </div>
        </main>
      </div>

      <BottomTabs />
    </div>
  );
}
