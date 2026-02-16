import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  index: number;
}

export function ChatMessage({ role, content, index }: ChatMessageProps) {
  const isAssistant = role === 'assistant';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03, duration: 0.2 }}
      className={`flex gap-2.5 ${isAssistant ? '' : 'flex-row-reverse'}`}
    >
      {isAssistant ? (
        <div className="w-8 h-8 rounded-xl bg-surface-2 border border-border flex items-center justify-center shrink-0">
          <Bot size={16} className="text-ember" />
        </div>
      ) : (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-ember to-ember-dark flex items-center justify-center text-white text-xs font-bold shrink-0">
          You
        </div>
      )}
      <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
        isAssistant
          ? 'bg-surface-2 text-chalk border border-border'
          : 'bg-gradient-to-br from-ember to-ember-dark text-white'
      }`}>
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
    </motion.div>
  );
}
