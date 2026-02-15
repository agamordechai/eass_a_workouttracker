import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { chatWithCoach } from '../../api/client';
import { ChatBubble } from './ChatBubble';
import type { ChatMessage } from '../../types/aiCoach';

export function CoachChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Hi! I'm your AI fitness coach. Ask me anything about your workout routine, form tips, or training advice. I can see your current exercises and provide personalized recommendations!",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [includeContext, setIncludeContext] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await chatWithCoach(userMessage, includeContext);
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: 'An Anthropic API key is required to use the AI Coach. Please set your key in Settings.' },
        ]);
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: `Sorry, I encountered an error: ${errorMessage}. Please make sure the AI Coach service is running.` },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestedQuestions = [
    "What exercises should I add for balance?",
    "How can I improve my bench press?",
    "Am I doing enough volume for back?",
    "What's a good warm-up routine?",
  ];

  return (
    <div className="card flex flex-col p-0 overflow-hidden" style={{ height: 'calc(100vh - 16rem)' }}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg, idx) => (
          <ChatBubble key={idx} role={msg.role} content={msg.content} index={idx} />
        ))}
        {loading && (
          <div className="flex gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-primary/20 flex items-center justify-center shrink-0">
              <div className="w-3 h-3 rounded-full bg-primary animate-pulse-glow" />
            </div>
            <div className="card px-4 py-3">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 rounded-full bg-text-muted animate-typing" style={{ animationDelay: '0s' }} />
                <span className="w-2 h-2 rounded-full bg-text-muted animate-typing" style={{ animationDelay: '0.2s' }} />
                <span className="w-2 h-2 rounded-full bg-text-muted animate-typing" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested questions */}
      {messages.length === 1 && (
        <div className="px-4 pb-3">
          <p className="text-xs text-text-muted mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-1.5">
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                className="text-xs px-3 py-1.5 rounded-lg bg-primary-muted border border-primary/20 text-primary hover:bg-primary/20 transition-colors"
                onClick={() => setInput(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-border p-4 space-y-2">
        <button
          onClick={() => setIncludeContext(!includeContext)}
          className={`text-xs px-3 py-1 rounded-full border transition-all ${
            includeContext
              ? 'bg-primary-muted border-primary/30 text-primary'
              : 'bg-surface-light border-border text-text-muted'
          }`}
        >
          {includeContext ? 'Workout context: ON' : 'Workout context: OFF'}
        </button>
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask your AI coach anything..."
            disabled={loading}
            rows={2}
            className="input flex-1 resize-none"
          />
          <button
            className="btn btn-primary self-end px-3"
            onClick={handleSend}
            disabled={!input.trim() || loading}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
