import { useMemo } from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, Bot, Settings, Shield } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const BASE_TABS = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/coach', label: 'Coach', icon: Bot },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export function BottomNav() {
  const { user } = useAuth();

  const tabs = useMemo(() => {
    if (user?.role === 'admin') {
      return [...BASE_TABS, { to: '/admin', label: 'Admin', icon: Shield }];
    }
    return BASE_TABS;
  }, [user?.role]);

  return (
    <nav className="lg:hidden fixed bottom-0 inset-x-0 z-50 border-t border-border bg-background/80 backdrop-blur-xl h-16 safe-area-bottom">
      <div className="flex items-center justify-around h-full px-4">
        {tabs.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className="relative flex flex-col items-center gap-1 py-1 px-4"
          >
            {({ isActive }) => (
              <>
                <div className="relative">
                  <Icon size={22} className={isActive ? 'text-ember' : 'text-steel'} />
                  {isActive && (
                    <motion.div
                      layoutId="bottom-nav-dot"
                      className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-ember"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                </div>
                <span className={`text-[10px] font-medium ${isActive ? 'text-ember' : 'text-steel'}`}>
                  {label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
