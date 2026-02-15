import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bot, Settings } from 'lucide-react';

const TABS = [
  { to: '/', label: 'Home', icon: LayoutDashboard },
  { to: '/coach', label: 'Coach', icon: Bot },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export function BottomNav() {
  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 glass border-t border-border pb-[env(safe-area-inset-bottom)]">
      <div className="flex items-center justify-around h-14">
        {TABS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-5 py-1.5 transition-colors ${
                isActive ? 'text-primary' : 'text-text-muted'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={20} />
                <span className="text-[10px] font-medium">{label}</span>
                {isActive && (
                  <div className="absolute bottom-1.5 w-1 h-1 rounded-full bg-primary" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
