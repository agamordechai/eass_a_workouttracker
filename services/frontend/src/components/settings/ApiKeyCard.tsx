import { useState, useEffect } from 'react';
import { Key } from 'lucide-react';

const STORAGE_KEY = 'anthropic_api_key';

function maskKey(key: string): string {
  if (key.length <= 12) return '****';
  return `${key.slice(0, 7)}...${key.slice(-4)}`;
}

export function ApiKeyCard() {
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
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Key size={16} className="text-primary" />
        <h3 className="text-sm font-bold text-text-primary">AI Coach API Key</h3>
      </div>

      {savedKey ? (
        <div className="flex items-center gap-3 bg-surface-light rounded-lg px-3 py-2.5 mb-3">
          <code className="text-sm text-primary flex-1 font-mono">{maskKey(savedKey)}</code>
          <button className="btn btn-danger btn-sm" onClick={handleRemove}>
            Remove
          </button>
        </div>
      ) : (
        <p className="text-xs text-text-muted mb-3">No API key set. Required for AI Coach features.</p>
      )}

      <div className="flex gap-2">
        <input
          type="password"
          value={key}
          onChange={e => setKey(e.target.value)}
          placeholder="sk-ant-..."
          className="input flex-1"
        />
        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={!key.trim()}
        >
          {savedKey ? 'Update' : 'Save'}
        </button>
      </div>
    </div>
  );
}
