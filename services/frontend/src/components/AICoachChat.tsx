import { useState, useRef, useEffect } from 'react';
import { chatWithCoach } from '../api/client';
import type { ChatMessage } from '../types/aiCoach';

export function AICoachChat() {
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
    <div className="card flex flex-col" style={{ height: 'calc(100vh - 16rem)' }}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-3">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0
              ${msg.role === 'assistant' ? 'bg-primary-muted text-primary' : 'bg-surface-light text-text-secondary border border-border'}`}>
              {msg.role === 'assistant' ? 'AI' : 'You'}
            </div>
            <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm leading-relaxed
              ${msg.role === 'assistant'
                ? 'bg-surface-light text-text-primary border border-border'
                : 'bg-primary text-white'}`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2.5">
            <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold bg-primary-muted text-primary shrink-0">AI</div>
            <div className="bg-surface-light border border-border rounded-lg px-3 py-2.5">
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
        <div className="mb-3">
          <p className="text-xs text-text-muted mb-2">Try asking:</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                className="text-left text-xs px-3 py-2 rounded-lg bg-surface-light border border-border text-text-secondary hover:bg-surface-hover hover:text-text-primary transition-colors"
                onClick={() => setInput(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-border pt-3 space-y-2">
        <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
          <input
            type="checkbox"
            checked={includeContext}
            onChange={e => setIncludeContext(e.target.checked)}
            className="rounded border-border"
          />
          Include my workout data
        </label>
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
            className="btn btn-primary self-end"
            onClick={handleSend}
            disabled={!input.trim() || loading}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
