import { useState } from 'react';
import { Metrics } from '../components/Metrics';
import { ExerciseList } from '../components/ExerciseList';
import { CreateExerciseModal } from '../components/CreateExerciseForm';
import { EditExerciseModal } from '../components/EditExerciseModal';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useExercises } from '../hooks/useExercises';
import type { Exercise } from '../types/exercise';

export default function DashboardPage() {
  const { exercises, loading, error, fetchExercises, handleCreate, handleUpdate, handleDelete, handleSeed } = useExercises();
  const [editingExercise, setEditingExercise] = useState<Exercise | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  if (error) {
    return (
      <div className="animate-fadeIn">
        <div className="card text-center py-10">
          <div className="w-12 h-12 rounded-full bg-danger/10 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-text-primary mb-1">Connection Error</h2>
          <p className="text-text-secondary text-sm mb-1 whitespace-pre-line max-w-md mx-auto">{error}</p>
          <p className="text-text-muted text-xs mb-4">
            Make sure the FastAPI server is running:<br />
            <code className="text-primary font-mono text-xs">uvicorn services.api.src.api:app --reload</code>
          </p>
          <button className="btn btn-primary" onClick={fetchExercises}>Retry Connection</button>
        </div>
      </div>
    );
  }

  if (loading && exercises.length === 0) {
    return <LoadingSpinner message="Loading your workouts..." />;
  }

  // Empty state
  if (exercises.length === 0) {
    return (
      <div className="animate-fadeIn space-y-4">
        <div className="card text-center py-10">
          <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-text-primary mb-1">Welcome to Workout Tracker</h2>
          <p className="text-text-secondary text-sm mb-6 max-w-sm mx-auto">Start building your routine. Load some samples to explore, or jump right in.</p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button className="btn btn-primary" onClick={handleSeed}>
              Load Sample Exercises
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setShowCreateModal(true)}
            >
              Start From Scratch
            </button>
          </div>
        </div>

        {showCreateModal && (
          <CreateExerciseModal onSubmit={handleCreate} onClose={() => setShowCreateModal(false)} />
        )}
      </div>
    );
  }

  return (
    <div className="animate-fadeIn space-y-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-text-primary">Dashboard</h2>
        <button
          className="btn btn-secondary btn-sm"
          onClick={fetchExercises}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Metrics bar */}
      <Metrics exercises={exercises} />

      {/* Exercise feed */}
      <ExerciseList
        exercises={exercises}
        onEdit={setEditingExercise}
        onCreateClick={() => setShowCreateModal(true)}
      />

      {/* Edit Modal */}
      {editingExercise && (
        <EditExerciseModal
          exercise={editingExercise}
          onSubmit={handleUpdate}
          onCancel={() => setEditingExercise(null)}
          onDelete={handleDelete}
        />
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateExerciseModal onSubmit={handleCreate} onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}
