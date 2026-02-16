import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Plus, RefreshCw, AlertTriangle } from 'lucide-react';
import { useExercises } from '../hooks/useExercises';
import { useAuth } from '../contexts/AuthContext';
import { PageShell } from '../components/ui/PageShell';
import { GlowButton } from '../components/ui/GlowButton';
import { CardSkeleton } from '../components/ui/Skeleton';
import { StatsRow } from '../components/stats/StatsRow';
import { VolumeChart } from '../components/stats/VolumeChart';
import { SplitDistribution } from '../components/stats/SplitDistribution';
import { DayPills } from '../components/workout/DayPills';
import { SplitCard } from '../components/workout/SplitCard';
import { CreateSheet } from '../components/workout/CreateSheet';
import { EmptyState } from '../components/workout/EmptyState';
import { ALL_DAYS } from '../lib/constants';
import { containerStagger } from '../lib/motion';

export default function DashboardPage() {
  const { exercises, loading, error, fetchExercises, handleCreate, handleUpdate, handleDelete, handleSeed } = useExercises();
  const { user } = useAuth();
  const [selectedDay, setSelectedDay] = useState('All');
  const [showCreate, setShowCreate] = useState(false);
  const [createDefaultDay, setCreateDefaultDay] = useState('A');

  const dayCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const ex of exercises) {
      const day = (!ex.workout_day || ex.workout_day === 'None') ? 'Daily' : ex.workout_day;
      counts[day] = (counts[day] || 0) + 1;
    }
    return counts;
  }, [exercises]);

  const groupedExercises = useMemo(() => {
    const groups: Record<string, typeof exercises> = {};
    const filtered = selectedDay === 'All'
      ? exercises
      : exercises.filter(ex => {
          const mapped = (!ex.workout_day || ex.workout_day === 'None') ? 'Daily' : ex.workout_day;
          return mapped === selectedDay;
        });

    for (const ex of filtered) {
      const day = (!ex.workout_day || ex.workout_day === 'None') ? 'Daily' : ex.workout_day;
      if (!groups[day]) groups[day] = [];
      groups[day].push(ex);
    }

    // Sort: days A-G, Daily, None
    const order = [...ALL_DAYS, 'None'];
    return Object.entries(groups).sort(([a], [b]) => {
      return order.indexOf(a) - order.indexOf(b);
    });
  }, [exercises, selectedDay]);

  const handleAddToDay = (day: string) => {
    setCreateDefaultDay(day);
    setShowCreate(true);
  };

  if (error) {
    return (
      <PageShell>
        <div className="card text-center py-12">
          <div className="w-14 h-14 rounded-2xl bg-danger/10 flex items-center justify-center mx-auto mb-4">
            <AlertTriangle size={24} className="text-danger" />
          </div>
          <h2 className="text-lg font-bold text-chalk mb-2">Connection Error</h2>
          <p className="text-steel text-sm mb-1 whitespace-pre-line max-w-md mx-auto">{error}</p>
          <p className="text-steel/60 text-xs mb-6">
            Make sure the FastAPI server is running.
          </p>
          <GlowButton onClick={fetchExercises}>Retry Connection</GlowButton>
        </div>
      </PageShell>
    );
  }

  if (loading && exercises.length === 0) {
    return (
      <PageShell className="space-y-6">
        <div className="grid grid-cols-3 gap-3">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <CardSkeleton />
        <CardSkeleton />
      </PageShell>
    );
  }

  if (exercises.length === 0) {
    return (
      <PageShell>
        <EmptyState onSeed={handleSeed} onCreateClick={() => setShowCreate(true)} />
        <CreateSheet
          open={showCreate}
          onClose={() => setShowCreate(false)}
          onSubmit={handleCreate}
          defaultDay={createDefaultDay}
        />
      </PageShell>
    );
  }

  const greeting = (() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  })();

  return (
    <PageShell className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-chalk">
            {greeting}{user?.name ? `, ${user.name.split(' ')[0]}` : ''}
          </h1>
          <p className="text-steel text-sm mt-0.5">Your training split at a glance</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchExercises}
            disabled={loading}
            className="w-9 h-9 rounded-xl flex items-center justify-center text-steel hover:text-chalk hover:bg-surface-2 transition-colors"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
          <GlowButton onClick={() => { setCreateDefaultDay('A'); setShowCreate(true); }}>
            <Plus size={16} />
            <span className="hidden sm:inline">Add Exercise</span>
          </GlowButton>
        </div>
      </div>

      {/* Stats */}
      <StatsRow exercises={exercises} />

      {/* Day pills */}
      <DayPills selected={selectedDay} onChange={setSelectedDay} dayCounts={dayCounts} />

      {/* Main content grid: splits + charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Split cards */}
        <motion.div
          variants={containerStagger}
          initial="initial"
          animate="animate"
          className="lg:col-span-2 space-y-4"
        >
          {groupedExercises.map(([day, dayExercises]) => (
            <SplitCard
              key={day}
              day={day}
              exercises={dayExercises}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
              onAddToDay={handleAddToDay}
            />
          ))}
        </motion.div>

        {/* Charts sidebar */}
        <div className="space-y-4">
          <VolumeChart exercises={exercises} />
          <SplitDistribution exercises={exercises} />
        </div>
      </div>

      <CreateSheet
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onSubmit={handleCreate}
        defaultDay={createDefaultDay}
      />
    </PageShell>
  );
}
