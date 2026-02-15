import { Plus, RefreshCw } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface DashboardHeaderProps {
  exerciseCount: number;
  onCreateClick: () => void;
  onRefresh: () => void;
  loading: boolean;
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export function DashboardHeader({ exerciseCount, onCreateClick, onRefresh, loading }: DashboardHeaderProps) {
  const { user } = useAuth();
  const firstName = user?.name?.split(' ')[0] || 'there';

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">
          {getGreeting()}, {firstName}
        </h1>
        <p className="text-text-secondary text-sm mt-1">
          You have {exerciseCount} exercise{exerciseCount !== 1 ? 's' : ''} in your routine
        </p>
      </div>
      <div className="flex items-center gap-2">
        <button
          className="btn btn-secondary btn-sm"
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
        <button className="btn btn-primary" onClick={onCreateClick}>
          <Plus size={16} />
          Add Exercise
        </button>
      </div>
    </div>
  );
}
