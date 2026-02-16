import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Users, Dumbbell, UserPlus, Activity, Trash2, RefreshCw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useAdmin } from '../hooks/useAdmin';
import { PageShell } from '../components/ui/PageShell';
import { GlowButton } from '../components/ui/GlowButton';
import type { AdminUser } from '../types/admin';

function StatCard({ label, value, icon: Icon }: { label: string; value: number; icon: React.ElementType }) {
  return (
    <div className="bg-surface rounded-2xl border border-border p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-steel">{label}</span>
        <Icon size={18} className="text-ember" />
      </div>
      <p className="text-2xl font-bold text-chalk">{value}</p>
    </div>
  );
}

export default function AdminPage() {
  const { user } = useAuth();
  const { users, stats, loading, error, refresh, handleUpdateUser, handleDeleteUser } = useAdmin();
  const [deleteTarget, setDeleteTarget] = useState<AdminUser | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  if (user?.role !== 'admin') {
    return <Navigate to="/" replace />;
  }

  const handleRoleChange = async (userId: number, role: string) => {
    try {
      setActionError(null);
      await handleUpdateUser(userId, { role });
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleToggleDisabled = async (u: AdminUser) => {
    try {
      setActionError(null);
      await handleUpdateUser(u.id, { disabled: !u.disabled });
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      setActionError(null);
      await handleDeleteUser(deleteTarget.id);
      setDeleteTarget(null);
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  if (loading) {
    return (
      <PageShell>
        <div className="flex items-center justify-center py-20">
          <RefreshCw size={24} className="text-steel animate-spin" />
        </div>
      </PageShell>
    );
  }

  if (error) {
    return (
      <PageShell>
        <div className="text-center py-20 text-red-400">{error}</div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-chalk">Admin Dashboard</h1>
          <GlowButton variant="ghost" size="sm" onClick={refresh}>
            <RefreshCw size={16} />
          </GlowButton>
        </div>

        {/* Error banner */}
        {actionError && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-sm"
          >
            {actionError}
          </motion.div>
        )}

        {/* Stats cards */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Total Users" value={stats.total_users} icon={Users} />
            <StatCard label="Total Exercises" value={stats.total_exercises} icon={Dumbbell} />
            <StatCard label="Signups (7d)" value={stats.recent_signups_7d} icon={UserPlus} />
            <StatCard label="Active Users" value={stats.active_users_7d} icon={Activity} />
          </div>
        )}

        {/* Users table */}
        <div className="bg-surface rounded-2xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-steel">
                  <th className="px-4 py-3 font-medium">User</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium hidden sm:table-cell">Exercises</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium hidden md:table-cell">Created</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-border/50 last:border-0">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {u.picture_url ? (
                          <img src={u.picture_url} alt="" className="w-8 h-8 rounded-full" referrerPolicy="no-referrer" />
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-surface-2 flex items-center justify-center text-chalk text-xs font-bold">
                            {u.name[0]?.toUpperCase() || '?'}
                          </div>
                        )}
                        <div className="min-w-0">
                          <p className="text-chalk font-medium truncate">{u.name}</p>
                          <p className="text-steel text-xs truncate">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        className="bg-surface-2 border border-border rounded-lg px-2 py-1 text-chalk text-xs focus:outline-none focus:ring-1 focus:ring-ember"
                      >
                        <option value="admin">admin</option>
                        <option value="user">user</option>
                        <option value="readonly">readonly</option>
                      </select>
                    </td>
                    <td className="px-4 py-3 text-chalk hidden sm:table-cell">{u.exercise_count}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleToggleDisabled(u)}
                        className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                          u.disabled
                            ? 'bg-red-500/15 text-red-400 hover:bg-red-500/25'
                            : 'bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25'
                        }`}
                      >
                        {u.disabled ? 'Disabled' : 'Active'}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-steel text-xs hidden md:table-cell">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setDeleteTarget(u)}
                        disabled={u.id === user?.id}
                        className="p-1.5 rounded-lg text-steel hover:text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        title={u.id === user?.id ? 'Cannot delete yourself' : `Delete ${u.name}`}
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Delete confirmation modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-surface border border-border rounded-2xl p-6 max-w-sm mx-4 w-full shadow-xl"
          >
            <h3 className="text-lg font-bold text-chalk mb-2">Delete User</h3>
            <p className="text-steel text-sm mb-6">
              Are you sure you want to delete <span className="text-chalk font-medium">{deleteTarget.name}</span> ({deleteTarget.email})?
              This will also delete all their exercises. This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <GlowButton variant="ghost" size="sm" onClick={() => setDeleteTarget(null)}>
                Cancel
              </GlowButton>
              <GlowButton variant="danger" size="sm" onClick={confirmDelete}>
                Delete
              </GlowButton>
            </div>
          </motion.div>
        </div>
      )}
    </PageShell>
  );
}
