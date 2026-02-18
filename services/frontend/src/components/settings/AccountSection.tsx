import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { GlowButton } from '../ui/GlowButton';
import { useAuth } from '../../contexts/AuthContext';
import { clearExercises } from '../../api/client';

export function AccountSection() {
  const { logout, deleteAccount } = useAuth();

  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [clearError, setClearError] = useState<string | null>(null);

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleClearData = async () => {
    setIsClearing(true);
    setClearError(null);
    try {
      await clearExercises();
      setShowClearConfirm(false);
    } catch (err) {
      setClearError(err instanceof Error ? err.message : 'Failed to clear data');
    } finally {
      setIsClearing(false);
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
    <>
      {/* Sign out */}
      <div className="py-6 border-b border-border">
        <h3 className="text-sm font-bold text-chalk mb-1">Session</h3>
        <p className="text-steel text-xs mb-3">Sign out of your account on this device.</p>
        <GlowButton variant="warning" onClick={logout}>
          Sign Out
        </GlowButton>
      </div>

      {/* Danger Zone */}
      <div className="py-6">
        <div className="flex items-center gap-2 mb-1">
          <AlertTriangle size={14} className="text-danger" />
          <h3 className="text-sm font-bold text-danger">Danger Zone</h3>
        </div>

        {/* Clear data */}
        <div className="mb-4">
          <p className="text-steel text-xs mb-3">
            Delete all your exercises and start fresh. Your account will remain active.
          </p>
          <GlowButton variant="danger" onClick={() => setShowClearConfirm(true)}>
            Clear All Data
          </GlowButton>
        </div>

        {/* Delete account */}
        <div className="border-t border-border/50 pt-4">
          <p className="text-steel text-xs mb-3">
            Permanently delete your account and all associated data. This cannot be undone.
          </p>
          <GlowButton variant="danger" onClick={() => setShowDeleteConfirm(true)}>
            Delete Account
          </GlowButton>
        </div>
      </div>

      {/* Clear data modal */}
      <Modal
        open={showClearConfirm}
        onClose={() => setShowClearConfirm(false)}
        title="Clear All Data"
        description="This will delete all your exercises"
      >
        {clearError && (
          <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded-xl px-3 py-2 mb-4">
            {clearError}
          </div>
        )}
        <p className="text-sm text-steel mb-6">
          All your exercises will be permanently deleted. Your account stays active and you can add new exercises or load a sample split afterwards.
        </p>
        <div className="flex gap-3">
          <GlowButton variant="danger" onClick={handleClearData} disabled={isClearing} className="flex-1">
            {isClearing ? 'Clearing...' : 'Yes, Clear All Data'}
          </GlowButton>
          <GlowButton variant="secondary" onClick={() => setShowClearConfirm(false)} disabled={isClearing}>
            Cancel
          </GlowButton>
        </div>
      </Modal>

      {/* Delete account modal */}
      <Modal
        open={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        title="Delete Account"
        description="This action is permanent and cannot be undone"
      >
        {deleteError && (
          <div className="bg-danger/10 border border-danger/20 text-danger text-xs rounded-xl px-3 py-2 mb-4">
            {deleteError}
          </div>
        )}
        <p className="text-sm text-steel mb-6">
          Are you sure you want to permanently delete your account? All your data, including exercises and settings, will be removed forever.
        </p>
        <div className="flex gap-3">
          <GlowButton variant="danger" onClick={handleDeleteAccount} disabled={isDeleting} className="flex-1">
            {isDeleting ? 'Deleting...' : 'Yes, Delete My Account'}
          </GlowButton>
          <GlowButton variant="secondary" onClick={() => setShowDeleteConfirm(false)} disabled={isDeleting}>
            Cancel
          </GlowButton>
        </div>
      </Modal>
    </>
  );
}
