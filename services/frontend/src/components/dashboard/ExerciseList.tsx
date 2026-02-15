import { useState, useMemo } from 'react';
import { Search, SlidersHorizontal, Download } from 'lucide-react';
import { ExerciseCard } from './ExerciseCard';
import { WorkoutDayTabs } from './WorkoutDayTabs';
import { exportExercisesCSV } from '../../api/client';
import type { Exercise, FilterType } from '../../types/exercise';

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
  onCreateClick?: () => void;
}

export function ExerciseList({ exercises, onEdit }: ExerciseListProps) {
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

  const handleDayChange = (day: string) => {
    setWorkoutDayFilter(day);
    setCurrentPage(1);
  };

  return (
    <div className="space-y-4">
      {/* Day filter tabs */}
      <WorkoutDayTabs
        exercises={exercises}
        activeDay={workoutDayFilter}
        onDayChange={handleDayChange}
      />

      {/* Toolbar */}
      <div className="card p-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1 overflow-x-auto">
            {SORT_TABS.map(({ key, label }) => (
              <button
                key={key}
                className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  sortColumn === key
                    ? 'bg-primary-muted text-primary'
                    : 'text-text-muted hover:text-text-secondary hover:bg-surface-light'
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
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <SlidersHorizontal size={14} />
            </button>
            <button className="btn btn-ghost btn-sm" onClick={exportExercisesCSV}>
              <Download size={14} />
            </button>
          </div>
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3 pt-3 border-t border-border">
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
              <label htmlFor="search" className="block text-xs font-medium text-text-secondary mb-1">Search</label>
              <div className="relative">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  id="search"
                  type="text"
                  placeholder="Exercise name..."
                  value={searchTerm}
                  onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
                  className="input pl-8"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Info */}
      <p className="text-xs text-text-muted px-1">
        Showing {paginatedExercises.length} of {filteredExercises.length} exercises
        {filteredExercises.length !== exercises.length && ` (${exercises.length} total)`}
      </p>

      {filteredExercises.length > 0 ? (
        <>
          <div className="space-y-2">
            {paginatedExercises.map((exercise, idx) => (
              <ExerciseCard
                key={exercise.id}
                exercise={exercise}
                onClick={() => onEdit(exercise)}
                index={idx}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <button className="btn btn-secondary btn-sm" disabled={safePage === 1} onClick={() => setCurrentPage(1)}>
                &laquo;
              </button>
              <button className="btn btn-secondary btn-sm" disabled={safePage === 1} onClick={() => setCurrentPage((p) => p - 1)}>
                &lsaquo;
              </button>
              <span className="text-xs text-text-secondary px-3">
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
        <div className="card text-center py-12 text-text-muted text-sm">
          No exercises match your filters.
        </div>
      )}
    </div>
  );
}
