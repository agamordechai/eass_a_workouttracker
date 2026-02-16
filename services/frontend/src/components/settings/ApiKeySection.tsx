import { useState, useEffect } from 'react';
import { Key } from 'lucide-react';
import { GlowButton } from '../ui/GlowButton';

const STORAGE_KEY = 'anthropic_api_key';

function maskKey(key: string): string {
  if (key.length <= 12) return '****';
  return `${key.slice(0, 7)}...${key.slice(-4)}`;
}

export function ApiKeySection() {
  const [key, setKey] = useState('');
  const [savedKey, setSavedKey] = useState<string | null>(null);

  useEffect(() => {
    setSavedKey(localStorage.getItem(STORAGE_KEY));
  }, []);

  const handleSave = () => {
    const trimmed = key.trim();
    if (!trimmed) return;
    localStorage.setItem(STORAGE_KEY, trimmed);
    setSavedKey(trimmed);
    setKey('');
  };

  const handleRemove = () => {
    localStorage.removeItem(STORAGE_KEY);
    setSavedKey(null);
    setKey('');
  };

  return (
    <div className="py-6 border-b border-border">
      <div className="flex items-center gap-2 mb-4">
        <Key size={16} className="text-ember" />
        <h3 className="text-sm font-bold text-chalk">AI Coach API Key</h3>
      </div>

      {savedKey ? (
        <div className="flex items-center gap-3 bg-surface-2 rounded-xl px-3 py-2.5 mb-3">
          <code className="text-sm text-ember flex-1 font-mono">{maskKey(savedKey)}</code>
          <GlowButton variant="danger" size="sm" onClick={handleRemove}>
            Remove
          </GlowButton>
        </div>
      ) : (
        <p className="text-xs text-steel mb-3">No API key set. Required for AI Coach features.</p>
      )}

      <div className="flex gap-2">
        <input
          type="password"
          value={key}
          onChange={e => setKey(e.target.value)}
          placeholder="sk-ant-..."
          className="input flex-1"
        />
        <GlowButton onClick={handleSave} disabled={!key.trim()}>
          {savedKey ? 'Update' : 'Save'}
        </GlowButton>
      </div>
    </div>
  );
}
