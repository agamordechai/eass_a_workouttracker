import { useState } from 'react';
import { AICoachChat } from '../components/AICoachChat';
import { RecommendationPanel } from '../components/RecommendationPanel';

type View = 'landing' | 'chat' | 'workout' | 'progress';

const CARDS: { view: View; title: string; description: string; icon: JSX.Element }[] = [
  {
    view: 'chat',
    title: 'Chat with Coach',
    description: 'Have a conversation with your AI fitness coach for personalized advice.',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 9.75a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 01.778-.332 48.294 48.294 0 005.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
      </svg>
    ),
  },
  {
    view: 'workout',
    title: 'Workout Generator',
    description: 'Generate a custom workout plan tailored to your equipment and goals.',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
      </svg>
    ),
  },
  {
    view: 'progress',
    title: 'Progress Analysis',
    description: 'Get AI-powered insights on your training balance and improvements.',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
  },
];

export default function CoachPage() {
  const [activeView, setActiveView] = useState<View>('landing');

  if (activeView !== 'landing') {
    return (
      <div className="animate-fadeIn space-y-4">
        <button
          onClick={() => setActiveView('landing')}
          className="flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
          Back to AI Coach
        </button>

        {activeView === 'chat' && <AICoachChat />}
        {activeView === 'workout' && <RecommendationPanel initialTab="recommend" />}
        {activeView === 'progress' && <RecommendationPanel initialTab="analyze" />}
      </div>
    );
  }

  return (
    <div className="animate-fadeIn space-y-4">
      <h2 className="text-lg font-bold text-text-primary">AI Coach</h2>

      <div className="grid gap-3">
        {CARDS.map(({ view, title, description, icon }) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className="card hover:border-primary/40 transition-colors text-left flex items-center gap-4 p-4"
          >
            <div className="w-14 h-14 rounded-xl bg-primary-muted flex items-center justify-center text-primary shrink-0">
              {icon}
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-bold text-text-primary">{title}</h3>
              <p className="text-xs text-text-secondary mt-0.5">{description}</p>
            </div>
            <svg className="w-5 h-5 text-text-muted shrink-0 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </button>
        ))}
      </div>
    </div>
  );
}
