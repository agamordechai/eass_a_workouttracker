/**
 * Main App component - Workout Tracker Dashboard
 */

import { useState, useEffect, useCallback } from 'react';
import { Metrics, ExerciseList, CreateExerciseForm, EditExerciseModal } from './components';
import {
  listExercises,
  createExercise,
  updateExercise,
  deleteExercise,
} from './api/client';
import type { Exercise, CreateExerciseRequest, UpdateExerciseRequest } from './types/exercise';
import './App.css';

function App() {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingExercise, setEditingExercise] = useState<Exercise | null>(null);

  // Fetch exercises
  const fetchExercises = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listExercises();
      setExercises(data);
    } catch (err) {
      setError(
        `Failed to connect to the API. Is the backend running?\n${
          err instanceof Error ? err.message : 'Unknown error'
        }`
      );
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load and auto-refresh every 30 seconds
  useEffect(() => {
    fetchExercises();
    const interval = setInterval(fetchExercises, 30000);
    return () => clearInterval(interval);
  }, [fetchExercises]);

  // Handle create exercise
  const handleCreate = async (data: CreateExerciseRequest) => {
    await createExercise(data);
    await fetchExercises();
  };

  // Handle update exercise
  const handleUpdate = async (exerciseId: number, data: UpdateExerciseRequest) => {
    await updateExercise(exerciseId, data);
    await fetchExercises();
  };

  // Handle delete exercise
  const handleDelete = async (exerciseId: number) => {
    try {
      await deleteExercise(exerciseId);
      await fetchExercises();
    } catch (err) {
      alert(`Failed to delete: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  if (error) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>🏋️ Workout Tracker Dashboard</h1>
          <p>View, create, and manage your workout exercises</p>
        </header>
        <main className="app-main">
          <div className="error-container">
            <div className="error-message">{error}</div>
            <div className="info-message">
              <p>Make sure the FastAPI server is running:</p>
              <pre>uvicorn services.api.src.api:app --reload</pre>
            </div>
            <button className="btn btn-primary" onClick={fetchExercises}>
              Retry Connection
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🏋️ Workout Tracker Dashboard</h1>
        <p>View, create, and manage your workout exercises</p>
      </header>

      <aside className="sidebar">
        <h2>Actions</h2>
        <button
          className="btn btn-primary full-width"
          onClick={fetchExercises}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh Data'}
        </button>
        <p className="sidebar-tip">Tip: Data refreshes automatically every 30 seconds</p>
      </aside>

      <main className="app-main">
        {loading && exercises.length === 0 ? (
          <div className="loading">Loading exercises...</div>
        ) : (
          <>
            {exercises.length > 0 ? (
              <>
                <Metrics exercises={exercises} />
                <hr className="divider" />
                <ExerciseList
                  exercises={exercises}
                  onEdit={setEditingExercise}
                  onDelete={handleDelete}
                />
              </>
            ) : (
              <div className="info-message">
                No exercises yet. Add your first exercise below!
              </div>
            )}

            <hr className="divider" />

            <CreateExerciseForm onSubmit={handleCreate} />

            {editingExercise && (
              <EditExerciseModal
                exercise={editingExercise}
                onSubmit={handleUpdate}
                onCancel={() => setEditingExercise(null)}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;

