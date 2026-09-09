/**
 * TopBar — Sovereign AI branding bar with LOCAL/ZERO EGRESS indicator
 *
 * Shows current user, role badge, and logout button.
 */

import { Shield, PanelRightClose, PanelRightOpen, LogOut, User, Cpu, Trash2 } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { useAuth } from '@/features/auth/useAuth';

export function TopBar() {
  const { trust, ui, toggleRightPanel, currentUser, routing, setActiveView } = useAppStore();
  const { logout } = useAuth();
  const isAdmin = currentUser?.role === 'admin';

  const handleDeleteSavedCredential = () => {
    if (!isAdmin) return;
    if (!window.confirm('Delete all saved login credentials from this browser?')) return;
    localStorage.removeItem('sovereign_remembered_user');
    window.dispatchEvent(new CustomEvent('sovereign-credentials-cleared'));
  };

  return (
    <header className="h-11 flex-shrink-0 flex items-center justify-between px-5 border-b select-none"
      style={{
        backgroundColor: 'var(--color-deck-deep)',
        borderColor: 'var(--color-deck-border)',
      }}
    >
      {/* Left — Branding */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded flex items-center justify-center"
            style={{ backgroundColor: 'var(--color-amber-muted)', border: '1px solid var(--color-amber-border)' }}
          >
            <Shield className="w-3 h-3" style={{ color: 'var(--color-amber-primary)' }} />
          </div>
          <span className="text-sm font-bold tracking-widest" style={{ color: 'var(--color-text-primary)' }}>
            SOVEREIGN AI
          </span>
        </div>
        <span className="hidden sm:block text-xs font-medium tracking-wider" style={{ color: 'var(--color-text-muted)' }}>
          COMMAND DECK
        </span>
      </div>

      {/* Center — Active Model Focus */}
      <button
        onClick={() => setActiveView('system')}
        className="hidden md:flex items-center gap-2 px-3 py-1 rounded-lg text-xs transition-all hover:border-amber-500/50 cursor-pointer"
        style={{
          backgroundColor: ui.activeView === 'system' ? 'rgba(245, 158, 11, 0.12)' : 'var(--color-deck-elevated)',
          border: ui.activeView === 'system' ? '1px solid var(--color-amber-border)' : '1px solid var(--color-deck-border)',
          color: ui.activeView === 'system' ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
        }}
        title="Click to open Active Model Workbench in center panel"
      >
        <Cpu className="w-3.5 h-3.5 text-amber-500" />
        <span className="font-instrument font-semibold">MODEL: {routing.selected_model}</span>
        <span className="text-[9px] px-1 py-0.2 rounded font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
          RTX 4060
        </span>
      </button>

      {/* Right — Status + Controls */}
      <div className="flex items-center gap-4">
        {/* User & Role Badge */}
        {currentUser && (
          <div className="hidden md:flex items-center gap-3">
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded font-instrument"
              style={{
                backgroundColor: 'var(--color-deck-elevated)',
                border: '1px solid var(--color-deck-border)',
                color: 'var(--color-text-secondary)',
              }}
            >
              <User className="w-3 h-3" style={{ color: 'var(--color-text-muted)' }} />
              <span style={{ color: 'var(--color-text-secondary)' }}>{currentUser.username}</span>
              <span className="mx-0.5" style={{ color: 'var(--color-deck-border)' }}>|</span>
              <span style={{ color: 'var(--color-amber-primary)' }} className="uppercase">
                {currentUser.role}
              </span>
            </span>

            {isAdmin && (
              <button
                onClick={handleDeleteSavedCredential}
                className="flex items-center gap-1.5 px-2 py-1 rounded text-xs font-semibold tracking-wider transition-all"
                style={{ color: 'var(--color-text-muted)', border: '1px solid transparent' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-error-muted)';
                  e.currentTarget.style.borderColor = 'var(--color-error-border)';
                  e.currentTarget.style.color = 'var(--color-error)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.borderColor = 'transparent';
                  e.currentTarget.style.color = 'var(--color-text-muted)';
                }}
                title="Admin only: delete saved login credentials"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span className="hidden lg:inline">DELETE CREDENTIAL</span>
              </button>
            )}

            {/* Logout button */}
            <button
              onClick={logout}
              className="flex items-center gap-1.5 px-2 py-1 rounded text-xs font-semibold tracking-wider transition-all"
              style={{
                color: 'var(--color-text-muted)',
                border: '1px solid transparent',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--color-error-muted)';
                e.currentTarget.style.borderColor = 'var(--color-error-border)';
                e.currentTarget.style.color = 'var(--color-error)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.borderColor = 'transparent';
                e.currentTarget.style.color = 'var(--color-text-muted)';
              }}
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">SIGN OUT</span>
            </button>
          </div>
        )}

        {/* LOCAL / ZERO EGRESS indicator */}
        <button
          className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold tracking-wide transition-all hover:scale-[1.02] cursor-pointer"
          style={{
            backgroundColor: trust.is_local ? 'var(--color-verified-muted)' : 'var(--color-error-muted)',
            border: `1px solid ${trust.is_local ? 'var(--color-verified-border)' : 'var(--color-error-border)'}`,
            color: trust.is_local ? 'var(--color-verified)' : 'var(--color-error)',
          }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full animate-sovereign-pulse"
            style={{
              backgroundColor: trust.is_local ? 'var(--color-verified)' : 'var(--color-error)',
              boxShadow: trust.is_local
                ? '0 0 6px var(--color-verified-glow)'
                : '0 0 6px rgba(239,68,68,0.4)',
            }}
          />
          {trust.is_local ? 'LOCAL / ZERO EGRESS' : 'ONLINE'}
        </button>

        {/* Right panel toggle */}
        <button
          onClick={toggleRightPanel}
          className="p-1.5 rounded transition-colors hover:bg-[var(--color-deck-elevated)]"
          style={{ color: 'var(--color-text-muted)' }}
          title={ui.rightPanelVisible ? 'Hide System Pulse' : 'Show System Pulse'}
        >
          {ui.rightPanelVisible
            ? <PanelRightClose className="w-4 h-4" />
            : <PanelRightOpen className="w-4 h-4" />
          }
        </button>
      </div>
    </header>
  );
}
