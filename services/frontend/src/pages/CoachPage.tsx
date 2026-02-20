import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { PageShell } from '../components/ui/PageShell';
import { CoachLanding } from '../components/coach/CoachLanding';
import { ChatView } from '../components/coach/ChatView';
import { WorkoutGenerator } from '../components/coach/WorkoutGenerator';
import { AnalysisReport } from '../components/coach/AnalysisReport';
import { useSessionStorage } from '../hooks/useSessionStorage';

type View = 'landing' | 'chat' | 'workout' | 'progress';

export default function CoachPage() {
  const [activeView, setActiveView] = useSessionStorage<View>('coach_active_view', 'landing');

  return (
    <PageShell>
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
              className="flex items-center gap-1.5 text-sm text-steel hover:text-chalk transition-colors"
            >
              <ArrowLeft size={16} />
              Back to AI Coach
            </button>

            {activeView === 'chat' && <ChatView />}
            {activeView === 'workout' && <WorkoutGenerator />}
            {activeView === 'progress' && <AnalysisReport />}
          </motion.div>
        ) : (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <CoachLanding onNavigate={setActiveView} />
          </motion.div>
        )}
      </AnimatePresence>
    </PageShell>
  );
}
