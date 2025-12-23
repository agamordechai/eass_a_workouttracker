/**
 * Metrics display component showing summary statistics.
 */

import type { Exercise } from '../types/exercise';

interface MetricsProps {
  exercises: Exercise[];
}

export function Metrics({ exercises }: MetricsProps) {
  const totalExercises = exercises.length;
  const totalSets = exercises.reduce((sum, ex) => sum + ex.sets, 0);
  const totalVolume = exercises.reduce((sum, ex) => {
    if (ex.weight !== null) {
      return sum + ex.sets * ex.reps * ex.weight;
    }
    return sum;
  }, 0);
  const weightedExercises = exercises.filter((ex) => ex.weight !== null).length;

  return (
    <div className="metrics-container">
      <div className="metric-card">
        <div className="metric-value">{totalExercises}</div>
        <div className="metric-label">Total Exercises</div>
      </div>
      <div className="metric-card">
        <div className="metric-value">{totalSets}</div>
        <div className="metric-label">Total Sets</div>
      </div>
      <div className="metric-card">
        <div className="metric-value">{totalVolume.toFixed(1)} kg</div>
        <div className="metric-label">Total Volume</div>
      </div>
      <div className="metric-card">
        <div className="metric-value">{weightedExercises}</div>
        <div className="metric-label">Weighted Exercises</div>
      </div>
    </div>
  );
}

