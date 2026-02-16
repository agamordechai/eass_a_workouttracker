import { useState, useEffect, useCallback } from 'react';
import {
  getAdminUsers,
  getAdminStats,
  updateAdminUser,
  deleteAdminUser,
} from '../api/client';
import type { AdminUser, AdminStats } from '../types/admin';

export function useAdmin() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [usersData, statsData] = await Promise.all([
        getAdminUsers(),
        getAdminStats(),
      ]);
      setUsers(usersData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load admin data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleUpdateUser = async (userId: number, data: { role?: string; disabled?: boolean }) => {
    await updateAdminUser(userId, data);
    await fetchAll();
  };

  const handleDeleteUser = async (userId: number) => {
    await deleteAdminUser(userId);
    await fetchAll();
  };

  return {
    users,
    stats,
    loading,
    error,
    refresh: fetchAll,
    handleUpdateUser,
    handleDeleteUser,
  };
}
