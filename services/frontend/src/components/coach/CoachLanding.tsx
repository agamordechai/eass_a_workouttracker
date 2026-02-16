import { motion } from 'framer-motion';
import { MessageCircle, Zap, BarChart3 } from 'lucide-react';

type CoachView = 'landing' | 'chat' | 'workout' | 'progress';

const CARDS: { view: CoachView; title: string; description: string; icon: typeof MessageCircle; gradient: string }[] = [
  {
    view: 'chat',
    title: 'Chat with Coach',
    description: 'Get personalized fitness advice from your AI coach.',
    icon: MessageCircle,
    gradient: 'from-ember/20 to-ember-dark/20',
  },
  {
    view: 'workout',
    title: 'Workout Generator',
    description: 'Generate custom workout plans based on your equipment and goals.',
    icon: Zap,
    gradient: 'from-blue-500/20 to-cyan-500/20',
  },
  {
    view: 'progress',
    title: 'Progress Analysis',
    description: 'AI-powered insights on training balance and improvements.',
    icon: BarChart3,
    gradient: 'from-emerald-500/20 to-green-500/20',
  },
];

interface CoachLandingProps {
  onNavigate: (view: CoachView) => void;
}

export function CoachLanding({ onNavigate }: CoachLandingProps) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-chalk">AI Coach</h1>
        <p className="text-steel text-sm mt-1">Your AI-powered training lab</p>
      </div>

      <div className="grid gap-4">
        {CARDS.map(({ view, title, description, icon: Icon, gradient }, idx) => (
          <motion.button
            key={view}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.08 }}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onNavigate(view)}
            className="card hover:border-ember/30 text-left flex items-center gap-4 p-5"
          >
            <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${gradient} border border-border flex items-center justify-center shrink-0`}>
              <Icon size={24} className="text-chalk" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-bold text-chalk">{title}</h3>
              <p className="text-xs text-steel mt-0.5">{description}</p>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
