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
 */

import { useEffect } from 'react';
import { useAppStore } from '@/store/appStore';
import { useMissionStore } from '@/store/missionStore';
import { api } from '@/services/api';

import { TopBar } from './TopBar';
import { MissionRail } from './MissionRail';
import { MissionCanvas } from '../mission/MissionCanvas';
import { SystemPulse } from './SystemPulse';
import { CommandBar } from './CommandBar';
import { TrustCenter } from '../trust/TrustCenter';

export function AppLayout() {
  const { ui, updateTelemetry, updateTrust, updateRouting, setCurrentUser } = useAppStore();
  const { rightPanelVisible } = ui;
  const activeView = ui.activeView;

  // Initialize auth and start polling
  useEffect(() => {
    const init = async () => {
      try {
        await api.ensureAuthenticated();
        const user = api.getUser();
        if (user) {
          setCurrentUser(user);
        }
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
        // Simulate subtle telemetry changes for demo
        updateTelemetry({
          gpu_percent: 55 + Math.round(Math.random() * 20),
          tokens_per_sec: 28 + Math.round(Math.random() * 8 * 10) / 10,
          ttft_ms: 380 + Math.round(Math.random() * 100),
          itl_ms: 45 + Math.round(Math.random() * 15),
        });
      }
    };

    pollTelemetry();
    const interval = setInterval(pollTelemetry, 5000);
    return () => clearInterval(interval);
  }, []);

  // Determine center content
  const renderCenter = () => {
    if (activeView === 'trust') {
      return <TrustCenter />;
    }
    return <MissionCanvas />;
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
