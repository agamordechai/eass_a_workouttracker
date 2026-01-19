/**
 * Exercise list/table component with filtering capabilities.
 */

import { useState } from 'react';
import type { Exercise, FilterType } from '../types/exercise';

interface ExerciseListProps {
  exercises: Exercise[];
  onEdit: (exercise: Exercise) => void;
  onDelete: (exerciseId: number) => void;
}

export function ExerciseList({ exercises, onEdit, onDelete }: ExerciseListProps) {
  const [filterType, setFilterType] = useState<FilterType>('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [workoutDayFilter, setWorkoutDayFilter] = useState<string>('All');

  // Apply filters
  let filteredExercises = exercises;

  if (filterType === 'Weighted Only') {
    filteredExercises = filteredExercises.filter((ex) => ex.weight !== null);
  } else if (filterType === 'Bodyweight Only') {
    filteredExercises = filteredExercises.filter((ex) => ex.weight === null);
  }

  if (workoutDayFilter !== 'All') {
    filteredExercises = filteredExercises.filter((ex) => ex.workout_day === workoutDayFilter);
  }

  if (searchTerm) {
    filteredExercises = filteredExercises.filter((ex) =>
      ex.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }

  return (
    <div className="exercise-list-section">
      <h2>Exercise List</h2>

      <div className="filters-container">
        <div className="filter-group">
          <label htmlFor="filter-type">Filter by type</label>
          <select
            id="filter-type"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as FilterType)}
          >
            <option value="All">All</option>
            <option value="Weighted Only">Weighted Only</option>
            <option value="Bodyweight Only">Bodyweight Only</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-workout-day">Filter by workout day</label>
          <select
            id="filter-workout-day"
            value={workoutDayFilter}
            onChange={(e) => setWorkoutDayFilter(e.target.value)}
          >
            <option value="All">All Days</option>
            <option value="None">Daily (Every Day)</option>
            <option value="A">Day A</option>
            <option value="B">Day B</option>
            <option value="C">Day C</option>
            <option value="D">Day D</option>
            <option value="E">Day E</option>
            <option value="F">Day F</option>
            <option value="G">Day G</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="search">Search exercises</label>
          <input
            id="search"
            type="text"
            placeholder="Type exercise name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <p className="filter-info">
        Showing {filteredExercises.length} of {exercises.length} exercises
      </p>

      {filteredExercises.length > 0 ? (
        <table className="exercise-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Exercise</th>
              <th>Sets</th>
              <th>Reps</th>
              <th>Weight</th>
              <th>Day</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredExercises.map((exercise) => (
              <tr key={exercise.id}>
                <td>{exercise.id}</td>
                <td>{exercise.name}</td>
                <td>{exercise.sets}</td>
                <td>{exercise.reps}</td>
                <td>{exercise.weight !== null ? `${exercise.weight} kg` : 'Bodyweight'}</td>
                <td><span className="workout-day-badge">{exercise.workout_day === 'None' ? 'Daily' : `Day ${exercise.workout_day}`}</span></td>
                <td className="action-buttons">
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => onEdit(exercise)}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => {
                      if (window.confirm(`Delete "${exercise.name}"?`)) {
                        onDelete(exercise.id);
                      }
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="info-message">No exercises match your filters.</div>
      )}
    </div>
  );
}

