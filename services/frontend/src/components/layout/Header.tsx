import { Dumbbell, Menu } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface HeaderProps {
  onMenuToggle: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-40 h-16 glass border-b border-border">
      <div className="flex items-center justify-between h-full px-4 lg:px-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuToggle}
            className="w-9 h-9 lg:hidden flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-light hover:text-text-primary transition-colors"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
              <Dumbbell size={18} className="text-white" />
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
              Workout Tracker
            </span>
          </div>
        </div>
        {user && (
          <div className="flex items-center">
            {user.picture_url ? (
              <img src={user.picture_url} alt="" className="w-8 h-8 rounded-full ring-2 ring-violet-500/30" referrerPolicy="no-referrer" />
            ) : (
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                {user.name?.[0]?.toUpperCase() || '?'}
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
