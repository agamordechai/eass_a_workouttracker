import { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { GlowButton } from '../ui/GlowButton';
import { ALL_DAYS } from '../../lib/constants';
import type { CreateExerciseRequest } from '../../types/exercise';

interface CreateSheetProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: CreateExerciseRequest) => Promise<void>;
  defaultDay?: string;
}

export function CreateSheet({ open, onClose, onSubmit, defaultDay = 'A' }: CreateSheetProps) {
  const [name, setName] = useState('');
  const [sets, setSets] = useState(3);
  const [reps, setReps] = useState(10);
  const [weight, setWeight] = useState(0);
  const [day, setDay] = useState(defaultDay);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) setDay(defaultDay);
  }, [open, defaultDay]);

  const reset = () => {
    setName('');
    setSets(3);
    setReps(10);
    setWeight(0);
    setDay(defaultDay);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      await onSubmit({
        name: name.trim(),
        sets,
        reps,
        weight: weight || null,
        workout_day: day,
      });
      reset();
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add Exercise" description="Create a new exercise for your routine">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-steel mb-1.5">Exercise Name</label>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g. Bench Press"
            className="input"
            autoFocus
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-steel mb-1.5">Sets</label>
            <input type="number" min={1} value={sets} onChange={e => setSets(Number(e.target.value))} className="input font-mono text-center" />
          </div>
          <div>
            <label className="block text-xs font-medium text-steel mb-1.5">Reps</label>
            <input type="number" min={1} value={reps} onChange={e => setReps(Number(e.target.value))} className="input font-mono text-center" />
          </div>
          <div>
            <label className="block text-xs font-medium text-steel mb-1.5">Weight (kg)</label>
            <input type="number" min={0} step={0.5} value={weight} onChange={e => setWeight(Number(e.target.value))} className="input font-mono text-center" />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-steel mb-1.5">Workout Day</label>
          <select value={day} onChange={e => setDay(e.target.value)} className="input">
            {ALL_DAYS.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
            <option value="None">Unassigned</option>
          </select>
        </div>

        <GlowButton type="submit" disabled={saving || !name.trim()} className="w-full">
          {saving ? 'Creating...' : 'Create Exercise'}
        </GlowButton>
      </form>
    </Modal>
  );
}
