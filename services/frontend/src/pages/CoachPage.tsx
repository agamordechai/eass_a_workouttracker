import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, MessageCircle, Zap, BarChart3 } from 'lucide-react';
import { CoachChat } from '../components/coach/CoachChat';
import { RecommendationPanel } from '../components/coach/RecommendationPanel';

type View = 'landing' | 'chat' | 'workout' | 'progress';

const CARDS: { view: View; title: string; description: string; icon: typeof MessageCircle; gradient: string }[] = [
  {
    view: 'chat',
    title: 'Chat with Coach',
    description: 'Have a conversation with your AI fitness coach for personalized advice.',
    icon: MessageCircle,
    gradient: 'from-violet-500/20 to-purple-500/20',
  },
  {
    view: 'workout',
    title: 'Workout Generator',
    description: 'Generate a custom workout plan tailored to your equipment and goals.',
    icon: Zap,
    gradient: 'from-orange-500/20 to-amber-500/20',
  },
  {
    view: 'progress',
    title: 'Progress Analysis',
    description: 'Get AI-powered insights on your training balance and improvements.',
    icon: BarChart3,
    gradient: 'from-blue-500/20 to-cyan-500/20',
  },
];

export default function CoachPage() {
  const [activeView, setActiveView] = useState<View>('landing');

  return (
    <AnimatePresence mode="wait">
      {activeView !== 'landing' ? (
        <motion.div
          key={activeView}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
          className="space-y-4"
        >
          <button
            onClick={() => setActiveView('landing')}
            className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            <ArrowLeft size={16} />
            Back to AI Coach
          </button>

          {activeView === 'chat' && <CoachChat />}
          {activeView === 'workout' && <RecommendationPanel initialTab="recommend" />}
          {activeView === 'progress' && <RecommendationPanel initialTab="analyze" />}
        </motion.div>
      ) : (
        <motion.div
          key="landing"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="space-y-6"
        >
          <div>
            <h1 className="text-2xl font-bold text-text-primary">AI Coach</h1>
            <p className="text-text-secondary text-sm mt-1">Your personal AI-powered fitness assistant</p>
          </div>

          <div className="grid gap-4">
            {CARDS.map(({ view, title, description, icon: Icon, gradient }, idx) => (
              <motion.button
                key={view}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveView(view)}
                className="card hover:border-primary/30 text-left flex items-center gap-4 p-5"
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${gradient} border border-white/5 flex items-center justify-center shrink-0`}>
                  <Icon size={24} className="text-text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-bold text-text-primary">{title}</h3>
                  <p className="text-xs text-text-secondary mt-0.5">{description}</p>
                </div>
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
