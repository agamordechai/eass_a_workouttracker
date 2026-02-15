import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  index: number;
}

export function ChatBubble({ role, content, index }: ChatBubbleProps) {
  const isAssistant = role === 'assistant';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.2 }}
      className={`flex gap-2.5 ${isAssistant ? '' : 'flex-row-reverse'}`}
    >
      {isAssistant ? (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-primary/20 flex items-center justify-center shrink-0">
          <Bot size={16} className="text-primary" />
        </div>
      ) : (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
          You
        </div>
      )}
      <div className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
        isAssistant
          ? 'card'
          : 'bg-gradient-to-br from-violet-500 to-purple-600 text-white'
      }`}>
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
    </motion.div>
  );
}
