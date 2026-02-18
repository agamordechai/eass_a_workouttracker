import { useState } from 'react';
import { motion } from 'framer-motion';
import { Flame, Zap } from 'lucide-react';
import { GlowButton } from '../ui/GlowButton';

type SplitType = 'ppl' | 'ab' | 'fullbody';

interface SplitOption {
  id: SplitType;
  label: string;
  subtitle: string;
  days: string[];
}

const SPLITS: SplitOption[] = [
  {
    id: 'fullbody',
    label: 'Full Body',
    subtitle: 'Train everything every session',
    days: ['Day A — Full Body'],
  },
  {
    id: 'ab',
    label: 'A/B Split',
    subtitle: 'Upper & lower alternating days',
    days: ['Day A — Upper', 'Day B — Lower'],
  },
  {
    id: 'ppl',
    label: 'Push / Pull / Legs',
    subtitle: 'Classic 3-day muscle group split',
    days: ['Day A — Push', 'Day B — Pull', 'Day C — Legs'],
  },
];

interface EmptyStateProps {
  onSeed: (split: SplitType) => void;
  onCreateClick: () => void;
}

export function EmptyState({ onSeed, onCreateClick }: EmptyStateProps) {
  const [selected, setSelected] = useState<SplitType>('ppl');

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card text-center py-16"
    >
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-ember to-ember-dark flex items-center justify-center mx-auto mb-6 shadow-lg shadow-ember/20">
        <Flame size={28} className="text-white" />
      </div>
      <h2 className="text-xl font-bold text-chalk mb-2">Welcome to the Forge</h2>
      <p className="text-steel text-sm mb-8 max-w-sm mx-auto">
        Pick a sample training split to get started, or build your own from scratch.
      </p>

      <div className="flex flex-col sm:flex-row items-stretch justify-center gap-3 mb-8 max-w-2xl mx-auto px-4">
        {SPLITS.map((split) => {
          const isSelected = selected === split.id;
          return (
            <button
              key={split.id}
              onClick={() => setSelected(split.id)}
              className={`flex-1 rounded-xl border p-4 text-left transition-all duration-200 cursor-pointer ${
                isSelected
                  ? 'border-ember bg-ember/10 shadow-md shadow-ember/20'
                  : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/8'
              }`}
            >
              <div className={`text-sm font-semibold mb-1 ${isSelected ? 'text-ember' : 'text-chalk'}`}>
                {split.label}
              </div>
              <div className="text-xs text-steel mb-3">{split.subtitle}</div>
              <div className="flex flex-col gap-1">
                {split.days.map((day) => (
                  <span key={day} className="text-xs text-steel/70 font-mono">
                    {day}
                  </span>
                ))}
                <span className="text-xs text-steel/70 font-mono">Daily — Core & Cardio</span>
              </div>
            </button>
          );
        })}
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <GlowButton onClick={() => onSeed(selected)}>
          <Zap size={16} />
          Load Sample Exercises
        </GlowButton>
        <GlowButton variant="secondary" onClick={onCreateClick}>
          Start From Scratch
        </GlowButton>
      </div>
    </motion.div>
  );
}