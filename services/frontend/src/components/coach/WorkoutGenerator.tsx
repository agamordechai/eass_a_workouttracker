import { useState } from 'react';
import { Dumbbell } from 'lucide-react';
import { GlowButton } from '../ui/GlowButton';
import { Badge } from '../ui/Badge';
import { getWorkoutRecommendation } from '../../api/client';
import { MUSCLE_GROUPS, EQUIPMENT_OPTIONS } from '../../lib/constants';
import type { WorkoutRecommendation, MuscleGroup, RecommendationRequest } from '../../types/aiCoach';

export function WorkoutGenerator() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [focusArea, setFocusArea] = useState<MuscleGroup | ''>('');
  const [duration, setDuration] = useState(45);
  const [equipment, setEquipment] = useState<string[]>(['barbell', 'dumbbells', 'cables', 'bodyweight']);
  const [recommendation, setRecommendation] = useState<WorkoutRecommendation | null>(null);

  const handleEquipmentToggle = (item: string) => {
    setEquipment(prev =>
      prev.includes(item) ? prev.filter(e => e !== item) : [...prev, item]
    );
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setRecommendation(null);
    try {
      const request: RecommendationRequest = {
        session_duration_minutes: duration,
        equipment_available: equipment,
      };
      if (focusArea) request.focus_area = focusArea;
      const result = await getWorkoutRecommendation(request);
      setRecommendation(result);
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setError('Anthropic API key required. Please set your key in Settings.');
      } else {
        setError(err instanceof Error ? err.message : 'Failed to get recommendation');
      }
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return (
      <div className="card">
        <div className="bg-danger/10 border border-danger/20 text-danger text-sm rounded-xl px-4 py-3 mb-4">
          {error}
        </div>
        <GlowButton variant="secondary" onClick={() => setError(null)}>Try Again</GlowButton>
      </div>
    );
  }

  if (recommendation) {
    return (
      <div className="card space-y-5">
        <div>
          <h3 className="text-lg font-bold text-chalk">{recommendation.title}</h3>
          <div className="flex items-center gap-2 mt-2">
            <Badge day={recommendation.difficulty} size="md" />
            <span className="text-xs text-steel font-mono">
              {recommendation.estimated_duration_minutes} min
            </span>
          </div>
        </div>

        <p className="text-sm text-steel">{recommendation.description}</p>

        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-chalk">Exercises</h4>
          {recommendation.exercises.map((ex, idx) => (
            <div key={idx} className="bg-surface-2 rounded-xl p-3 border border-border">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-chalk flex items-center gap-2">
                  <Dumbbell size={14} className="text-ember" />
                  {ex.name}
                </span>
              </div>
              <p className="text-xs text-steel font-mono">
                {ex.sets} sets &times; {ex.reps}
                {ex.weight_suggestion && <span className="text-ember ml-1">@ {ex.weight_suggestion}</span>}
              </p>
              {ex.notes && <p className="text-xs text-steel/60 mt-1">{ex.notes}</p>}
            </div>
          ))}
        </div>

        {recommendation.tips.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-chalk mb-2">Tips</h4>
            <ul className="space-y-1">
              {recommendation.tips.map((tip, idx) => (
                <li key={idx} className="text-xs text-steel flex gap-2">
                  <span className="text-ember shrink-0">-</span>
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        )}

        <GlowButton variant="secondary" onClick={() => setRecommendation(null)} className="w-full">
          Generate Another
        </GlowButton>
      </div>
    );
  }

  return (
    <div className="card space-y-5">
      <div>
        <label className="block text-xs font-medium text-steel mb-1.5">Focus Area</label>
        <select value={focusArea} onChange={e => setFocusArea(e.target.value as MuscleGroup | '')} className="input">
          {MUSCLE_GROUPS.map(mg => (
            <option key={mg.value} value={mg.value}>{mg.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-steel mb-1.5">
          Duration: <span className="text-ember font-semibold font-mono">{duration} min</span>
        </label>
        <input
          type="range"
          min={15}
          max={120}
          step={5}
          value={duration}
          onChange={e => setDuration(Number(e.target.value))}
          className="w-full accent-[#F97316]"
        />
        <div className="flex justify-between text-[10px] text-steel/60 mt-1">
          <span>15 min</span>
          <span>120 min</span>
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-steel mb-2">Available Equipment</label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {EQUIPMENT_OPTIONS.map(item => (
            <button
              key={item}
              type="button"
              onClick={() => handleEquipmentToggle(item)}
              className={`text-xs px-3 py-2 rounded-xl font-medium transition-all border ${
                equipment.includes(item)
                  ? 'bg-ember/10 border-ember/30 text-ember'
                  : 'bg-surface-2 border-border text-steel hover:border-steel/40'
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <GlowButton
        onClick={handleGenerate}
        disabled={loading || equipment.length === 0}
        className="w-full"
      >
        {loading ? 'Generating...' : 'Generate Workout'}
      </GlowButton>
    </div>
  );
}
