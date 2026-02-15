import { useState, useMemo } from 'react';
import type { Exercise, FilterType } from '../types/exercise';
import { exportExercisesCSV } from '../api/client';

const SORT_TABS: { key: keyof Exercise; label: string }[] = [
  { key: 'name', label: 'Name' },
  { key: 'sets', label: 'Sets' },
  { key: 'weight', label: 'Weight' },
  { key: 'workout_day', label: 'Day' },
];

const PAGE_SIZE = 10;

interface ExerciseListProps {
  exercises: Exercise[];
  onEdit: (exercise: Exercise) => void;
  onCreateClick: () => void;
}

export function ExerciseList({ exercises, onEdit, onCreateClick }: ExerciseListProps) {
  const [filterType, setFilterType] = useState<FilterType>('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [workoutDayFilter, setWorkoutDayFilter] = useState<string>('All');
  const [sortColumn, setSortColumn] = useState<keyof Exercise | null>(null);
  const [sortDirection, setSortDirection] = useState<'desc' | 'asc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

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

  const sortedExercises = useMemo(() => {
    if (!sortColumn) return filteredExercises;
    return [...filteredExercises].sort((a, b) => {
      const valA = a[sortColumn];
      const valB = b[sortColumn];
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

  const totalPages = Math.max(1, Math.ceil(sortedExercises.length / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const paginatedExercises = sortedExercises.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE
  );

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
    <div>
      {/* Sort bar + filter toggle */}
      <div className="card mb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            {SORT_TABS.map(({ key, label }) => (
              <button
                key={key}
                className={`text-xs px-3 py-1.5 rounded-full font-bold transition-colors ${
                  sortColumn === key
                    ? 'bg-surface-light text-text-primary'
                    : 'text-text-muted hover:text-text-secondary hover:bg-surface-hover'
                }`}
                onClick={() => handleSort(key)}
              >
                {label}
                {sortColumn === key && (
                  <span className="ml-0.5">{sortDirection === 'desc' ? '\u2193' : '\u2191'}</span>
                )}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button
              className="text-xs px-3 py-1.5 rounded-full text-text-muted hover:text-text-secondary hover:bg-surface-hover font-bold transition-colors"
              onClick={() => setShowFilters(!showFilters)}
            >
              {showFilters ? 'Hide Filters' : 'Filters'}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={exportExercisesCSV}>
              Export
            </button>
          </div>
        </div>

        {/* Collapsible filters */}
        {showFilters && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3 pt-3 border-t border-border">
            <div>
              <label htmlFor="filter-type" className="block text-xs font-medium text-text-secondary mb-1">Type</label>
              <select
                id="filter-type"
                value={filterType}
                onChange={(e) => { setFilterType(e.target.value as FilterType); setCurrentPage(1); }}
                className="input"
              >
                <option value="All">All</option>
                <option value="Weighted Only">Weighted Only</option>
                <option value="Bodyweight Only">Bodyweight Only</option>
              </select>
            </div>
            <div>
              <label htmlFor="filter-workout-day" className="block text-xs font-medium text-text-secondary mb-1">Day</label>
              <select
                id="filter-workout-day"
                value={workoutDayFilter}
                onChange={(e) => { setWorkoutDayFilter(e.target.value); setCurrentPage(1); }}
                className="input"
              >
                <option value="All">All Days</option>
                <option value="None">Daily</option>
                <option value="A">Day A</option>
                <option value="B">Day B</option>
                <option value="C">Day C</option>
                <option value="D">Day D</option>
                <option value="E">Day E</option>
                <option value="F">Day F</option>
                <option value="G">Day G</option>
              </select>
            </div>
            <div>
              <label htmlFor="search" className="block text-xs font-medium text-text-secondary mb-1">Search</label>
              <input
                id="search"
                type="text"
                placeholder="Exercise name..."
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
                className="input"
              />
            </div>
          </div>
        )}
      </div>

      {/* Info row */}
      <div className="flex items-center justify-between mb-2 px-1">
        <p className="text-xs text-text-muted">
          Showing {paginatedExercises.length} of {filteredExercises.length} exercises
          {filteredExercises.length !== exercises.length && ` (${exercises.length} total)`}
        </p>
      </div>

      {filteredExercises.length > 0 ? (
        <>
          {/* Exercise cards */}
          <div className="grid gap-3">
            {/* + Create Exercise card */}
            <button
              onClick={onCreateClick}
              className="card hover:border-primary/40 transition-colors text-left flex items-center gap-4 p-4"
            >
              <div className="w-10 h-10 rounded-xl bg-primary-muted flex items-center justify-center text-primary shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-bold text-primary">Create Exercise</h3>
                <p className="text-xs text-text-secondary mt-0.5">Add a new exercise to your routine</p>
              </div>
              <svg className="w-5 h-5 text-text-muted shrink-0 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </button>

            {paginatedExercises.map((exercise) => (
              <button
                key={exercise.id}
                onClick={() => onEdit(exercise)}
                className="card hover:border-primary/40 transition-colors text-left flex items-center gap-4 p-4"
              >
                <div className="w-10 h-10 rounded-xl bg-primary-muted flex items-center justify-center text-primary shrink-0">
                  <span className="text-sm font-bold">{exercise.workout_day === 'None' ? 'D' : exercise.workout_day}</span>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-bold text-text-primary truncate">{exercise.name}</h3>
                  <p className="text-xs text-text-secondary mt-0.5">
                    {exercise.sets} sets &middot; {exercise.reps} reps &middot; {exercise.weight !== null ? `${exercise.weight} kg` : 'Bodyweight'} &middot; {exercise.workout_day === 'None' ? 'Daily' : `Day ${exercise.workout_day}`}
                  </p>
                </div>
                <svg className="w-5 h-5 text-text-muted shrink-0 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </button>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-3">
              <button className="btn btn-secondary btn-sm" disabled={safePage === 1} onClick={() => setCurrentPage(1)}>
                &laquo;
              </button>
              <button className="btn btn-secondary btn-sm" disabled={safePage === 1} onClick={() => setCurrentPage((p) => p - 1)}>
                &lsaquo;
              </button>
              <span className="text-xs text-text-secondary px-2">
                Page {safePage} of {totalPages}
              </span>
              <button className="btn btn-secondary btn-sm" disabled={safePage === totalPages} onClick={() => setCurrentPage((p) => p + 1)}>
                &rsaquo;
              </button>
              <button className="btn btn-secondary btn-sm" disabled={safePage === totalPages} onClick={() => setCurrentPage(totalPages)}>
                &raquo;
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="card text-center py-8 text-text-muted text-sm">
          No exercises match your filters.
        </div>
      )}
    </div>
  );
}
