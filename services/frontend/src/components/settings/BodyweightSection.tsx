import { useState, useEffect } from 'react';
import { PersonStanding } from 'lucide-react';
import { GlowButton } from '../ui/GlowButton';
import { getBodyweightKg, setBodyweightKg } from '../../hooks/useBodyweight';

export function BodyweightSection() {
  const [input, setInput] = useState('');
  const [saved, setSaved] = useState<number | null>(null);

  useEffect(() => {
    setSaved(getBodyweightKg());
  }, []);

  const handleSave = () => {
    const val = parseFloat(input);
    if (!input.trim() || isNaN(val) || val <= 0) return;
    setBodyweightKg(val);
    setSaved(val);
    setInput('');
  };

  const handleRemove = () => {
    setBodyweightKg(null);
    setSaved(null);
    setInput('');
  };

  return (
    <div className="py-6 border-b border-border">
      <div className="flex items-center gap-2 mb-1">
        <PersonStanding size={16} className="text-ember" />
        <h3 className="text-sm font-bold text-chalk">Bodyweight</h3>
      </div>
      <p className="text-xs text-steel mb-4">
        Used to calculate volume for bodyweight exercises in analytics.
      </p>

      {saved !== null && (
        <div className="flex items-center gap-3 bg-surface-2 rounded-xl px-3 py-2.5 mb-3">
          <span className="text-sm text-ember flex-1 font-mono">{saved} kg</span>
          <GlowButton variant="danger" size="sm" onClick={handleRemove}>
            Remove
          </GlowButton>
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="number"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="e.g. 75"
          min={1}
          max={300}
          step={0.5}
          className="input flex-1"
        />
        <GlowButton onClick={handleSave} disabled={!input.trim() || isNaN(parseFloat(input)) || parseFloat(input) <= 0}>
          {saved !== null ? 'Update' : 'Save'}
        </GlowButton>
      </div>
    </div>
  );
}
