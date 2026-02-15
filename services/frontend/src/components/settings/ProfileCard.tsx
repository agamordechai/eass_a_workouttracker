import { useState } from 'react';
import { Pencil } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

export function ProfileCard() {
  const { user, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(user?.name || '');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEdit = () => {
    setEditName(user?.name || '');
    setIsEditing(true);
    setError(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditName(user?.name || '');
    setError(null);
  };

  const handleSave = async () => {
    const trimmedName = editName.trim();
    if (!trimmedName) {
      setError('Name cannot be empty');
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await updateProfile({ name: trimmedName });
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-text-primary">Profile</h3>
        {!isEditing && (
          <button
            onClick={handleEdit}
            className="btn btn-ghost btn-sm"
          >
            <Pencil size={14} />
            Edit
          </button>
        )}
      </div>

      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded-lg px-3 py-2 mb-3">
          {error}
        </div>
      )}

      <div className="flex items-center gap-4">
        {user?.picture_url ? (
          <img
            src={user.picture_url}
            alt=""
            className="w-14 h-14 rounded-2xl ring-2 ring-primary/20"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-lg font-bold ring-2 ring-primary/20">
            {user?.name?.[0]?.toUpperCase() || '?'}
          </div>
        )}
        <div className="flex-1">
          {isEditing ? (
            <div className="space-y-2">
              <div>
                <label htmlFor="edit-name" className="block text-xs font-medium text-text-secondary mb-1">
                  Name
                </label>
                <input
                  id="edit-name"
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="input"
                  disabled={isSaving}
                />
              </div>
              <div className="flex gap-2">
                <button onClick={handleSave} className="btn btn-primary btn-sm" disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
                <button onClick={handleCancel} className="btn btn-secondary btn-sm" disabled={isSaving}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="text-text-primary text-sm font-semibold">{user?.name}</p>
              <p className="text-text-muted text-xs mt-0.5">{user?.email}</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
