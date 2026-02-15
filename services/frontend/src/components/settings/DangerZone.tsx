import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { useAuth } from '../../contexts/AuthContext';

export function DangerZone() {
  const { logout, deleteAccount } = useAuth();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

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
    <>
      {/* Sign out */}
      <div className="card">
        <h3 className="text-sm font-bold text-text-primary mb-1">Account</h3>
        <p className="text-text-muted text-xs mb-3">Sign out of your account on this device.</p>
        <button className="btn btn-warning" onClick={logout}>
          Sign Out
        </button>
      </div>

      {/* Delete */}
      <div className="card border-danger/20">
        <div className="flex items-center gap-2 mb-1">
          <AlertTriangle size={14} className="text-danger" />
          <h3 className="text-sm font-bold text-danger">Danger Zone</h3>
        </div>
        <p className="text-text-muted text-xs mb-3">
          Permanently delete your account and all associated data. This action cannot be undone.
        </p>
        <button className="btn btn-danger" onClick={() => setShowDeleteConfirm(true)}>
          Delete Account
        </button>
      </div>

      <Modal
        open={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        title="Delete Account"
        description="This action is permanent and cannot be undone"
      >
        {deleteError && (
          <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded-lg px-3 py-2 mb-4">
            {deleteError}
          </div>
        )}

        <p className="text-sm text-text-secondary mb-6">
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
      </Modal>
    </>
  );
}
