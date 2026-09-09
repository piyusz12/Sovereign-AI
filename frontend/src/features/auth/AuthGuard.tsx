/**
 * AuthGuard — Checks if user is authenticated before rendering children.
 *
 * If no valid token exists, renders the LoginPage.
 * On mount, validates the token with /auth/me.
 */

import { useEffect, useState, type ReactNode } from 'react';
import { useAppStore } from '@/store/appStore';
import { api } from '@/services/api';
import { LoginPage } from './LoginPage';
import { Shield, Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { currentUser, setCurrentUser, setAvailableWorkflows } = useAppStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const validate = async () => {
      // If we have a stored token, try to validate it
      const storedToken = localStorage.getItem('sovereign_jwt');
      if (!storedToken) {
        setChecking(false);
        return;
      }

      try {
        // Validate token by calling /auth/me
        const res = await fetch('/api/v1/auth/me', {
          headers: { Authorization: `Bearer ${storedToken}` },
        });

        if (res.ok) {
          const userData = await res.json();
          setCurrentUser(userData);
          // Also restore the api client state
          const storedUser = localStorage.getItem('sovereign_user');
          if (!storedUser) {
            localStorage.setItem('sovereign_user', JSON.stringify(userData));
          }

          // Fetch available workflows for this role
          try {
            const wfRes = await fetch('/api/v1/workflows/available', {
              headers: { Authorization: `Bearer ${storedToken}` },
            });
            if (wfRes.ok) {
              const wfData = await wfRes.json();
              setAvailableWorkflows(wfData.workflows || []);
            }
          } catch {
            // Offline — use defaults
          }
        } else {
          // Token invalid — clear everything
          localStorage.removeItem('sovereign_jwt');
          localStorage.removeItem('sovereign_user');
          setCurrentUser(null);
        }
      } catch {
        // Server unreachable — keep token, show app in offline mode
        const storedUser = localStorage.getItem('sovereign_user');
        if (storedUser) {
          try {
            setCurrentUser(JSON.parse(storedUser));
          } catch {
            setCurrentUser(null);
          }
        }
      } finally {
        setChecking(false);
      }
    };

    validate();
  }, []);

  // When user logs in (currentUser changes from null), fetch workflows
  useEffect(() => {
    if (currentUser && !checking) {
      const fetchWorkflows = async () => {
        try {
          const workflows = await api.getAvailableWorkflows();
          setAvailableWorkflows(workflows);
        } catch {
          // Offline
        }
      };
      fetchWorkflows();
    }
  }, [currentUser?.username]);

  if (checking) {
    return (
      <div
        className="h-screen w-full flex flex-col items-center justify-center gap-4"
        style={{ backgroundColor: 'var(--color-deck-void)' }}
      >
        <div
          className="w-14 h-14 rounded-xl flex items-center justify-center"
          style={{
            backgroundColor: 'var(--color-amber-muted)',
            border: '1px solid var(--color-amber-border)',
            boxShadow: '0 0 30px var(--color-amber-glow)',
          }}
        >
          <Shield className="w-7 h-7" style={{ color: 'var(--color-amber-primary)' }} />
        </div>
        <div className="flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-xs tracking-widest font-semibold">VERIFYING SESSION</span>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return <LoginPage />;
  }

  return <>{children}</>;
}
