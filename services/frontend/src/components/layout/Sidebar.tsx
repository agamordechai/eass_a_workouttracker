import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bot, Settings } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/coach', label: 'AI Coach', icon: Bot },
  { to: '/settings', label: 'Settings', icon: Settings },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user } = useAuth();

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed top-16 left-0 z-50 h-[calc(100vh-4rem)] w-64 glass border-r border-border flex flex-col
          transition-transform duration-300 ease-out
          lg:sticky lg:z-auto
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <nav className="flex-1 flex flex-col gap-1 p-4 pt-6">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'text-text-primary bg-primary-muted'
                    : 'text-text-muted hover:bg-surface-light hover:text-text-secondary'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 bg-primary-muted rounded-xl border border-primary/20"
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}
                  <Icon size={20} className="relative z-10" />
                  <span className="relative z-10">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {user && (
          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-3 px-2">
              {user.picture_url ? (
                <img src={user.picture_url} alt="" className="w-9 h-9 rounded-full ring-2 ring-violet-500/20" referrerPolicy="no-referrer" />
              ) : (
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                  {user.name?.[0]?.toUpperCase() || '?'}
                </div>
              )}
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-text-primary truncate">{user.name}</p>
                <p className="text-xs text-text-muted truncate">{user.email}</p>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
