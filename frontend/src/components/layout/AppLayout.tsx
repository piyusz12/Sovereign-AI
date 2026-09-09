/**
 * AppLayout — Three-panel Sovereign Command Deck architecture
 *
 * ┌──────────────────────────────────────────────────────────────┐
 * │ TOP BAR — SOVEREIGN AI              ● LOCAL / ZERO EGRESS   │
 * ├───────────────┬───────────────────────────┬──────────────────┤
 * │ MISSION RAIL  │    MISSION CANVAS         │  SYSTEM PULSE    │
 * │ (LEFT)        │    (CENTER)               │  (RIGHT)         │
 * ├───────────────┴───────────────────────────┴──────────────────┤
 * │ COMMAND BAR                                                  │
 * └──────────────────────────────────────────────────────────────┘
 *
 * Wrapped in AuthGuard — renders login page if not authenticated.
 */

import { useEffect } from 'react';
import { useAppStore } from '@/store/appStore';
import { useMissionStore } from '@/store/missionStore';
import { api } from '@/services/api';

import { AuthGuard } from '@/features/auth/AuthGuard';
import { TopBar } from './TopBar';
import { MissionRail } from './MissionRail';
import { SystemPulse } from './SystemPulse';
import { CommandBar } from './CommandBar';
import { TrustLayerDeck } from '@/features/trust/TrustLayerDeck';
import { ModelDeck } from '@/features/models/ModelDeck';
import { AttestationDeck } from '@/features/attestation/AttestationDeck';
import { McpGovernanceDeck } from '@/features/mcp/McpGovernanceDeck';
import { ManticScaffoldDeck } from '@/features/mantic/ManticScaffoldDeck';
import { CyberScanDeck } from '@/features/security/CyberScanDeck';
import { VerifiableRagDeck } from '@/features/rag/VerifiableRagDeck';
import { ModelWorkspaces } from '@/features/models/ModelWorkspaces';
import { MissionCanvas } from '../mission/MissionCanvas';

function AppContent() {
  const { ui, updateTelemetry, updateTrust } = useAppStore();
  const { rightPanelVisible } = ui;
  const activeView = ui.activeView;
  const activeMission = useMissionStore((state) => state.getActiveMission());

  // Start polling after authentication
  useEffect(() => {
    const init = async () => {
      try {
        const health = await api.getHealth();
        if (health) {
          updateTrust({ is_local: health.sovereign });
        }
      } catch {
        // Offline mode — use defaults
      }
    };
    init();

    // Poll telemetry
    const pollTelemetry = async () => {
      try {
        const status = await api.getModelStatus();
        if (status) {
          updateTelemetry({
            vram_used_mb: status.vram_used_mb || 6348,
            vram_total_mb: status.max_vram_mb || 8192,
            gpu_percent: status.gpu_percent || 61,
          });
        }
      } catch {
        // Backend unreachable — keep last known values
      }
    };

    pollTelemetry();
    const interval = setInterval(pollTelemetry, 5000);
    return () => clearInterval(interval);
  }, []);

  // Determine center content
  const renderCenter = () => {
    if (activeView === 'trust') {
      return <TrustLayerDeck />;
    }
    if (activeView === 'system') {
      return <ModelDeck />;
    }
    if (activeView === 'attestation') {
      return <AttestationDeck />;
    }
    if (activeView === 'mcp') {
      return <McpGovernanceDeck />;
    }
    if (activeView === 'mantic') {
      return <ManticScaffoldDeck />;
    }
    if (activeView === 'cyberscan') {
      return <CyberScanDeck />;
    }
    if (activeView === 'rag') {
      return <VerifiableRagDeck />;
    }
    if (activeView === 'reasoning' || activeView === 'coding' || activeView === 'vision') {
      return <ModelWorkspaces activePanel={activeView} />;
    }
    return activeMission ? <MissionCanvas /> : <ModelWorkspaces />;
  };

  return (
    <div
      className="flex flex-col h-screen w-full overflow-hidden"
      style={{ backgroundColor: 'var(--color-deck-void)' }}
    >
      {/* Top Bar */}
      <TopBar />

      {/* Main three-panel area */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT — Mission Rail */}
        <MissionRail />

        {/* CENTER — Mission Canvas */}
        {renderCenter()}

        {/* RIGHT — System Pulse */}
        {rightPanelVisible && <SystemPulse />}
      </div>

      {/* Bottom — Command Bar */}
      <CommandBar />
    </div>
  );
}

export function AppLayout() {
  return (
    <AuthGuard>
      <AppContent />
    </AuthGuard>
  );
}
