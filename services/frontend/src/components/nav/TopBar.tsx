import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Flame, Home, Bot, Settings, Shield } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useMemo } from 'react';

const BASE_NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/coach', label: 'Coach', icon: Bot },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export function TopBar() {
  const { user } = useAuth();

  const navItems = useMemo(() => {
    if (user?.role === 'admin') {
      return [...BASE_NAV_ITEMS, { to: '/admin', label: 'Admin', icon: Shield }];
    }
    return BASE_NAV_ITEMS;
  }, [user?.role]);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="mx-auto max-w-6xl flex items-center justify-between px-4 lg:px-6 h-16">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-ember to-ember-dark flex items-center justify-center shadow-lg shadow-ember/20">
            <Flame size={20} className="text-white" />
          </div>
          <span className="text-lg font-bold text-chalk hidden sm:block">GRINDLOGGER</span>
        </div>

        {/* Desktop nav */}
        <nav className="hidden lg:flex items-center gap-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className="relative"
            >
              {({ isActive }) => (
                <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  isActive ? 'text-chalk' : 'text-steel hover:text-chalk'
                }`}>
                  <Icon size={16} />
                  {label}
                  {isActive && (
                    <motion.div
                      layoutId="nav-pill"
                      className="absolute inset-0 bg-surface-2 rounded-xl -z-10"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                </div>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Avatar */}
        <div className="flex items-center">
          {user?.picture_url ? (
            <img
              src={user.picture_url}
              alt=""
              className="w-8 h-8 rounded-full ring-2 ring-ember/30"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-ember to-ember-dark flex items-center justify-center text-white text-xs font-bold ring-2 ring-ember/30">
              {user?.name?.[0]?.toUpperCase() || '?'}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
