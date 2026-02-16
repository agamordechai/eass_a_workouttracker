import { useState } from 'react';
import type { Exercise, UpdateExerciseRequest } from '../../types/exercise';
import { GlowButton } from '../ui/GlowButton';

interface ExerciseEditorProps {
  exercise: Exercise;
  days: string[];
  onSave: (data: UpdateExerciseRequest) => Promise<void>;
  onCancel: () => void;
}

export function ExerciseEditor({ exercise, days, onSave, onCancel }: ExerciseEditorProps) {
  const [name, setName] = useState(exercise.name);
  const [sets, setSets] = useState(exercise.sets);
  const [reps, setReps] = useState(exercise.reps);
  const [weight, setWeight] = useState(exercise.weight ?? 0);
  const [day, setDay] = useState(exercise.workout_day);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave({
        name: name.trim(),
        sets,
        reps,
        weight: weight || null,
        workout_day: day,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="px-4 pb-3 space-y-3">
      <div>
        <label className="block text-xs font-medium text-steel mb-1">Name</label>
        <input value={name} onChange={e => setName(e.target.value)} className="input" />
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div>
          <label className="block text-xs font-medium text-steel mb-1">Sets</label>
          <input type="number" min={1} value={sets} onChange={e => setSets(Number(e.target.value))} className="input font-mono text-center" />
        </div>
        <div>
          <label className="block text-xs font-medium text-steel mb-1">Reps</label>
          <input type="number" min={1} value={reps} onChange={e => setReps(Number(e.target.value))} className="input font-mono text-center" />
        </div>
        <div>
          <label className="block text-xs font-medium text-steel mb-1">Weight</label>
          <input type="number" min={0} step={0.5} value={weight} onChange={e => setWeight(Number(e.target.value))} className="input font-mono text-center" />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-steel mb-1">Day</label>
        <select value={day} onChange={e => setDay(e.target.value)} className="input">
          {days.map(d => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      <div className="flex gap-2">
        <GlowButton onClick={handleSave} disabled={saving || !name.trim()} className="flex-1">
          {saving ? 'Saving...' : 'Save'}
        </GlowButton>
        <GlowButton variant="secondary" onClick={onCancel} disabled={saving}>
          Cancel
        </GlowButton>
      </div>
    </div>
  );
}
