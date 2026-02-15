import { useState } from 'react';
import { ApiKeySettings } from '../components/ApiKeySettings';
import { useAuth } from '../contexts/AuthContext';

export default function SettingsPage() {
  const { user, logout, updateProfile, deleteAccount } = useAuth();
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editName, setEditName] = useState(user?.name || '');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleEditProfile = () => {
    setEditName(user?.name || '');
    setIsEditingProfile(true);
    setError(null);
  };

  const handleCancelEdit = () => {
    setIsEditingProfile(false);
    setEditName(user?.name || '');
    setError(null);
  };

  const handleSaveProfile = async () => {
    const trimmedName = editName.trim();
    if (!trimmedName) {
      setError('Name cannot be empty');
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await updateProfile({ name: trimmedName });
      setIsEditingProfile(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteAccount();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete account');
      setIsDeleting(false);
    }
  };

  return (
    <div className="animate-fadeIn space-y-4">
      <div>
        <h2 className="text-lg font-bold text-text-primary">Settings</h2>
        <p className="text-text-secondary text-sm mt-0.5">Manage your account and preferences</p>
      </div>

      {/* Profile */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-text-primary">Profile</h3>
          {!isEditingProfile && (
            <button
              onClick={handleEditProfile}
              className="text-xs text-primary hover:text-primary/80 font-medium"
            >
              Edit
            </button>
          )}
        </div>

        {error && (
          <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded px-3 py-2 mb-3">
            {error}
          </div>
        )}

        <div className="flex items-center gap-3">
          {user?.picture_url ? (
            <img
              src={user.picture_url}
              alt=""
              className="w-10 h-10 rounded-full"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-surface-light border border-border flex items-center justify-center text-text-secondary text-sm font-bold">
              {user?.name?.[0]?.toUpperCase() || '?'}
            </div>
          )}
          <div className="flex-1">
            {isEditingProfile ? (
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
                  <button
                    onClick={handleSaveProfile}
                    className="btn btn-primary btn-sm"
                    disabled={isSaving}
                  >
                    {isSaving ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="btn btn-secondary btn-sm"
                    disabled={isSaving}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <p className="text-text-primary text-sm font-medium">{user?.name}</p>
                <p className="text-text-secondary text-xs">{user?.email}</p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* API Key */}
      <div className="card">
        <h3 className="text-sm font-bold text-text-primary mb-3">AI Coach API Key</h3>
        <ApiKeySettings />
      </div>

      {/* Sign out */}
      <div className="card">
        <h3 className="text-sm font-bold text-text-primary mb-1">Account</h3>
        <p className="text-text-secondary text-xs mb-3">Sign out of your account on this device.</p>
        <button className="btn btn-warning" onClick={logout}>
          Sign Out
        </button>
      </div>

      {/* Delete Account */}
      <div className="card border-danger/30">
        <h3 className="text-sm font-bold text-danger mb-1">Danger Zone</h3>
        <p className="text-text-secondary text-xs mb-3">
          Permanently delete your account and all associated data. This action cannot be undone.
        </p>
        <button className="btn btn-danger" onClick={() => setShowDeleteConfirm(true)}>
          Delete Account
        </button>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => setShowDeleteConfirm(false)}>
          <div className="card w-full max-w-md animate-fadeIn" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-danger/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-bold text-text-primary">Delete Account</h3>
                <p className="text-xs text-text-secondary">This action is permanent</p>
              </div>
            </div>

            {deleteError && (
              <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded px-3 py-2 mb-3">
                {deleteError}
              </div>
            )}

            <p className="text-sm text-text-secondary mb-4">
              Are you sure you want to permanently delete your account? All your data, including exercises and settings, will be removed forever.
            </p>

            <div className="flex gap-3">
              <button
                onClick={handleDeleteAccount}
                className="btn btn-danger flex-1"
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Yes, Delete My Account'}
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="btn btn-secondary"
                disabled={isDeleting}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
