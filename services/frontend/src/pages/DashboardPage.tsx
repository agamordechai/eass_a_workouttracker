import { useState } from 'react';
import { Dumbbell, Zap, AlertTriangle } from 'lucide-react';
import { DashboardHeader } from '../components/dashboard/DashboardHeader';
import { MetricsGrid } from '../components/dashboard/MetricsGrid';
import { ExerciseList } from '../components/dashboard/ExerciseList';
import { VolumeChart } from '../components/dashboard/VolumeChart';
import { WorkoutDistribution } from '../components/dashboard/WorkoutDistribution';
import { CreateExerciseModal } from '../components/exercises/CreateExerciseModal';
import { EditExerciseModal } from '../components/exercises/EditExerciseModal';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useExercises } from '../hooks/useExercises';
import type { Exercise } from '../types/exercise';

export default function DashboardPage() {
  const { exercises, loading, error, fetchExercises, handleCreate, handleUpdate, handleDelete, handleSeed } = useExercises();
  const [editingExercise, setEditingExercise] = useState<Exercise | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  if (error) {
    return (
      <div className="card text-center py-12">
        <div className="w-14 h-14 rounded-2xl bg-danger/10 flex items-center justify-center mx-auto mb-4">
          <AlertTriangle size={24} className="text-danger" />
        </div>
        <h2 className="text-lg font-bold text-text-primary mb-2">Connection Error</h2>
        <p className="text-text-secondary text-sm mb-1 whitespace-pre-line max-w-md mx-auto">{error}</p>
        <p className="text-text-muted text-xs mb-6">
          Make sure the FastAPI server is running:<br />
          <code className="text-primary font-mono text-xs">uvicorn services.api.src.api:app --reload</code>
        </p>
        <button className="btn btn-primary" onClick={fetchExercises}>Retry Connection</button>
      </div>
    );
  }

  if (loading && exercises.length === 0) {
    return <LoadingSpinner message="Loading your workouts..." />;
  }

  if (exercises.length === 0) {
    return (
      <div className="space-y-6">
        <div className="card text-center py-16">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-primary/20 flex items-center justify-center mx-auto mb-6">
            <Dumbbell size={28} className="text-primary" />
          </div>
          <h2 className="text-xl font-bold text-text-primary mb-2">Welcome to Workout Tracker</h2>
          <p className="text-text-secondary text-sm mb-8 max-w-sm mx-auto">Start building your routine. Load some samples to explore, or jump right in.</p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button className="btn btn-primary" onClick={handleSeed}>
              <Zap size={16} />
              Load Sample Exercises
            </button>
            <button className="btn btn-secondary" onClick={() => setShowCreateModal(true)}>
              Start From Scratch
            </button>
          </div>
        </div>

        <CreateExerciseModal
          open={showCreateModal}
          onSubmit={handleCreate}
          onClose={() => setShowCreateModal(false)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DashboardHeader
        exerciseCount={exercises.length}
        onCreateClick={() => setShowCreateModal(true)}
        onRefresh={fetchExercises}
        loading={loading}
      />

      <MetricsGrid exercises={exercises} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ExerciseList
            exercises={exercises}
            onEdit={setEditingExercise}
            onCreateClick={() => setShowCreateModal(true)}
          />
        </div>
        <div className="space-y-6">
          <VolumeChart exercises={exercises} />
          <WorkoutDistribution exercises={exercises} />
        </div>
      </div>

      <EditExerciseModal
        exercise={editingExercise}
        open={editingExercise !== null}
        onSubmit={handleUpdate}
        onCancel={() => setEditingExercise(null)}
        onDelete={handleDelete}
      />

      <CreateExerciseModal
        open={showCreateModal}
        onSubmit={handleCreate}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  );
}
