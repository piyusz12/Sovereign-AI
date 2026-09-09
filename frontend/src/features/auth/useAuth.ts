/**
 * useAuth — Custom hook for authentication state and actions.
 *
 * Provides login, logout, and workflow availability helpers.
 */

import { useCallback } from 'react';
import { useAppStore } from '@/store/appStore';
import { api } from '@/services/api';

export function useAuth() {
  const {
    currentUser,
    availableWorkflows,
    setCurrentUser,
    setAvailableWorkflows,
  } = useAppStore();

  const isAuthenticated = !!currentUser;

  const login = useCallback(async (username: string, password: string) => {
    const user = await api.login(username, password);
    setCurrentUser(user);

    // Fetch available workflows after login
    try {
      const workflows = await api.getAvailableWorkflows();
      setAvailableWorkflows(workflows);
    } catch {
      // Offline
    }

    return user;
  }, [setCurrentUser, setAvailableWorkflows]);

  const logout = useCallback(() => {
    api.logout();
    setCurrentUser(null);
    setAvailableWorkflows([]);
  }, [setCurrentUser, setAvailableWorkflows]);

  const canAccessWorkflow = useCallback(
    (workflowName: string): boolean => {
      if (!currentUser) return false;
      if (currentUser.role === 'admin') return true;
      return availableWorkflows.includes(workflowName);
    },
    [currentUser, availableWorkflows],
  );

  const hasPermission = useCallback(
    (permission: string): boolean => {
      if (!currentUser) return false;
      if (currentUser.role === 'admin') return true;

      // Simplified client-side permission check
      const rolePermissions: Record<string, string[]> = {
        engineering: ['ai.chat', 'agent.execute_code', 'agent.run', 'document.read', 'document.upload', 'rag.search', 'report.create'],
        finance: ['ai.chat', 'ai.vision', 'document.read', 'rag.search', 'report.create'],
        procurement: ['ai.chat', 'document.read', 'document.upload', 'rag.search', 'report.create'],
        hr: ['ai.chat', 'document.read', 'rag.search'],
        operations: ['ai.chat', 'ai.vision', 'document.read', 'document.upload', 'rag.search', 'agent.execute_code', 'report.create'],
      };

      const perms = rolePermissions[currentUser.role] || [];
      return perms.includes(permission);
    },
    [currentUser],
  );

  return {
    isAuthenticated,
    user: currentUser,
    availableWorkflows,
    login,
    logout,
    canAccessWorkflow,
    hasPermission,
  };
}
