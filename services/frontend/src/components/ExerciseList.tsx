/**
 * Exercise list/table component with filtering, sorting, and pagination.
 */

import { useState, useMemo } from 'react';
import type { Exercise, FilterType } from '../types/exercise';
import { exportExercisesCSV } from '../api/client';

const COLUMN_HEADERS: { key: keyof Exercise; label: string }[] = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Exercise' },
  { key: 'sets', label: 'Sets' },
  { key: 'reps', label: 'Reps' },
  { key: 'weight', label: 'Weight' },
  { key: 'workout_day', label: 'Day' },
];

const PAGE_SIZE = 10;

interface ExerciseListProps {
  exercises: Exercise[];
  onEdit: (exercise: Exercise) => void;
  onDelete: (exerciseId: number) => void;
}

export function ExerciseList({ exercises, onEdit, onDelete }: ExerciseListProps) {
  const [filterType, setFilterType] = useState<FilterType>('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [workoutDayFilter, setWorkoutDayFilter] = useState<string>('All');
  const [sortColumn, setSortColumn] = useState<keyof Exercise | null>(null);
  const [sortDirection, setSortDirection] = useState<'desc' | 'asc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);

  // ── filters ──────────────────────────────────────────────
  const filteredExercises = useMemo(() => {
    let result = exercises;

    if (filterType === 'Weighted Only') {
      result = result.filter((ex) => ex.weight !== null);
    } else if (filterType === 'Bodyweight Only') {
      result = result.filter((ex) => ex.weight === null);
    }

    if (workoutDayFilter !== 'All') {
      result = result.filter((ex) => ex.workout_day === workoutDayFilter);
    }

    if (searchTerm) {
      result = result.filter((ex) =>
        ex.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return result;
  }, [exercises, filterType, workoutDayFilter, searchTerm]);

  // ── sort ─────────────────────────────────────────────────
  const sortedExercises = useMemo(() => {
    if (!sortColumn) return filteredExercises;

    return [...filteredExercises].sort((a, b) => {
      const valA = a[sortColumn];
      const valB = b[sortColumn];

      // nulls (bodyweight) always sink to the bottom
      if (valA === null && valB === null) return 0;
      if (valA === null) return 1;
      if (valB === null) return -1;

      const cmp =
        typeof valA === 'string' && typeof valB === 'string'
          ? valA.localeCompare(valB)
          : (valA as number) - (valB as number);

      return sortDirection === 'desc' ? -cmp : cmp;
    });
  }, [filteredExercises, sortColumn, sortDirection]);

  // ── pagination ───────────────────────────────────────────
  const totalPages = Math.max(1, Math.ceil(sortedExercises.length / PAGE_SIZE));
  // clamp so the page stays valid if filters shrink the result set
  const safePage = Math.min(currentPage, totalPages);
  const paginatedExercises = sortedExercises.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE
  );

  // first click on a new column → desc; subsequent clicks toggle
  const handleSort = (column: keyof Exercise) => {
    if (sortColumn === column) {
      setSortDirection((prev) => (prev === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
    setCurrentPage(1);
  };

  return (
    <div className="exercise-list-section">
      <h2>Exercise List</h2>

      <div className="filters-container">
        <div className="filter-group">
          <label htmlFor="filter-type">Filter by type</label>
          <select
            id="filter-type"
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value as FilterType);
              setCurrentPage(1);
            }}
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
            onChange={(e) => {
              setWorkoutDayFilter(e.target.value);
              setCurrentPage(1);
            }}
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
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
          />
        </div>
      </div>

      <div className="filter-info-row">
        <p className="filter-info">
          Showing {paginatedExercises.length} of {filteredExercises.length} exercises
          {filteredExercises.length !== exercises.length && ` (${exercises.length} total)`}
        </p>
        <button className="btn btn-sm btn-secondary" onClick={exportExercisesCSV}>
          Export CSV
        </button>
      </div>

      {filteredExercises.length > 0 ? (
        <>
          <table className="exercise-table">
            <thead>
              <tr>
                {COLUMN_HEADERS.map(({ key, label }) => (
                  <th
                    key={key}
                    className={`sortable${sortColumn === key ? ' sort-active' : ''}`}
                    onClick={() => handleSort(key)}
                  >
                    {label}
                    {sortColumn === key && (
                      <span className="sort-indicator">
                        {sortDirection === 'desc' ? '↓' : '↑'}
                      </span>
                    )}
                  </th>
                ))}
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedExercises.map((exercise) => (
                <tr key={exercise.id}>
                  <td>{exercise.id}</td>
                  <td>{exercise.name}</td>
                  <td>{exercise.sets}</td>
                  <td>{exercise.reps}</td>
                  <td>{exercise.weight !== null ? `${exercise.weight} kg` : 'Bodyweight'}</td>
                  <td>
                    <span className="workout-day-badge">
                      {exercise.workout_day === 'None' ? 'Daily' : `Day ${exercise.workout_day}`}
                    </span>
                  </td>
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

          {totalPages > 1 && (
            <div className="pagination-controls">
              <button
                className="btn btn-sm btn-secondary"
                disabled={safePage === 1}
                onClick={() => setCurrentPage(1)}
              >
                «
              </button>
              <button
                className="btn btn-sm btn-secondary"
                disabled={safePage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
              >
                ‹
              </button>
              <span className="page-info">Page {safePage} of {totalPages}</span>
              <button
                className="btn btn-sm btn-secondary"
                disabled={safePage === totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
              >
                ›
              </button>
              <button
                className="btn btn-sm btn-secondary"
                disabled={safePage === totalPages}
                onClick={() => setCurrentPage(totalPages)}
              >
                »
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="info-message">No exercises match your filters.</div>
      )}
    </div>
  );
}
