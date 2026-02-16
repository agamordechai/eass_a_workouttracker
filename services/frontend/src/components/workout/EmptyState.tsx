import { motion } from 'framer-motion';
import { Flame, Zap } from 'lucide-react';
import { GlowButton } from '../ui/GlowButton';

interface EmptyStateProps {
  onSeed: () => void;
  onCreateClick: () => void;
}

export function EmptyState({ onSeed, onCreateClick }: EmptyStateProps) {
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
        Your training split starts here. Load sample exercises to explore, or start building from scratch.
      </p>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <GlowButton onClick={onSeed}>
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
