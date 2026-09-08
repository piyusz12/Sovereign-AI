/**
 * TopBar — Sovereign AI branding bar with LOCAL/ZERO EGRESS indicator
 */

import { Shield, PanelRightClose, PanelRightOpen } from 'lucide-react';
import { useAppStore } from '@/store/appStore';

export function TopBar() {
  const { trust, ui, toggleRightPanel, currentUser } = useAppStore();

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

      {/* Right — Status + Controls */}
      <div className="flex items-center gap-4">
        {/* Role Badge */}
        {currentUser && (
          <span className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded font-instrument"
            style={{
              backgroundColor: 'var(--color-deck-elevated)',
              border: '1px solid var(--color-deck-border)',
              color: 'var(--color-text-secondary)',
            }}
          >
            <span style={{ color: 'var(--color-text-muted)' }}>ROLE:</span>
            <span style={{ color: 'var(--color-amber-primary)' }} className="uppercase">
              {currentUser.role}
            </span>
          </span>
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
