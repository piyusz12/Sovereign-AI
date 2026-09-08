/**
 * TopBar — Sovereign AI branding, navigation tabs, and live telemetry pill
 */

import { Shield, PanelRightClose, PanelRightOpen, Cpu, Sparkles, Activity, Layers, Lock } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { useMissionStore } from '@/store/missionStore';

export function TopBar() {
  const { trust, telemetry, ui, toggleRightPanel, currentUser, setActiveView, routing } = useAppStore();
  const { runDemoMission } = useMissionStore();

  const vramPercent = Math.min(100, Math.round((telemetry.vram_used_mb / (telemetry.vram_total_mb || 8192)) * 100));

  return (
    <header
      className="h-12 flex-shrink-0 flex items-center justify-between px-4 border-b select-none relative z-20"
      style={{
        backgroundColor: 'var(--color-deck-deep)',
        borderColor: 'var(--color-deck-border)',
        backgroundImage: 'linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 100%)',
      }}
    >
      {/* Left — Branding & View Switcher */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => setActiveView('command')}>
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center glow-amber shadow-lg transition-transform hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(245, 158, 11, 0.08) 100%)',
              border: '1px solid var(--color-amber-border)',
            }}
          >
            <Shield className="w-4 h-4" style={{ color: 'var(--color-amber-primary)' }} />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-black tracking-widest bg-gradient-to-r from-amber-400 via-amber-200 to-white bg-clip-text text-transparent">
                SOVEREIGN AI
              </span>
              <span className="text-[9px] px-1 py-0.2 rounded font-mono font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20">
                v1.0
              </span>
            </div>
            <span className="text-[10px] font-mono tracking-wider block -mt-0.5 text-slate-400">
              INDUSTRIAL COMMAND DECK
            </span>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="hidden sm:flex items-center gap-1 p-0.5 rounded-lg bg-black/40 border border-white/5">
          <button
            type="button"
            onClick={() => setActiveView('command')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
              ui.activeView === 'command'
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-sm font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Mission Canvas</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveView('trust')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
              ui.activeView === 'trust'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Trust & Verification</span>
          </button>
        </div>
      </div>

      {/* Right — Telemetry, Quick Actions & Status */}
      <div className="flex items-center gap-3">
        {/* Quick Launch Demo Button */}
        <button
          type="button"
          onClick={runDemoMission}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold tracking-wide bg-gradient-to-r from-amber-500/20 via-amber-400/10 to-amber-500/20 text-amber-300 border border-amber-500/40 hover:border-amber-400 hover:bg-amber-500/30 transition-all active:scale-95 shadow-sm cursor-pointer"
          title="Simulate automated Sovereign AI mission pipeline"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
          <span>RUN DEMO</span>
        </button>

        {/* Real-time VRAM Pill */}
        <div
          onClick={toggleRightPanel}
          className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-md bg-black/40 border border-white/5 text-xs font-mono cursor-pointer hover:border-cyan-500/30 transition-colors"
          title="Toggle System Pulse panel"
        >
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400 text-[11px]">VRAM</span>
          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden border border-white/5">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-amber-400 transition-all duration-500"
              style={{ width: `${vramPercent}%` }}
            />
          </div>
          <span className="text-cyan-300 text-[11px] font-bold">
            {(telemetry.vram_used_mb / 1024).toFixed(1)}G
          </span>
        </div>

        {/* Active Model Pill */}
        <button
          type="button"
          onClick={() => setActiveView('command')}
          className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/20 text-xs font-mono text-purple-300 hover:bg-purple-500/20 cursor-pointer transition-colors"
          title="Active routing model"
        >
          <Activity className="w-3 h-3 text-purple-400" />
          <span className="text-[11px]">{routing.selected_model}</span>
        </button>

        {/* Role Badge */}
        {currentUser && (
          <span className="hidden xl:flex items-center gap-1.5 px-2.5 py-0.5 rounded-md font-mono text-[11px] bg-slate-900 border border-white/10 text-slate-300">
            <span className="text-slate-500">ROLE:</span>
            <span className="text-amber-400 uppercase font-bold">
              {currentUser.role}
            </span>
          </span>
        )}

        {/* LOCAL / ZERO EGRESS Indicator (Clickable to jump to Trust Center) */}
        <button
          onClick={() => setActiveView('trust')}
          className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold tracking-wider transition-all hover:scale-105 active:scale-95 cursor-pointer shadow-md"
          style={{
            backgroundColor: trust.is_local ? 'var(--color-verified-muted)' : 'var(--color-error-muted)',
            border: `1px solid ${trust.is_local ? 'var(--color-verified-border)' : 'var(--color-error-border)'}`,
            color: trust.is_local ? 'var(--color-verified)' : 'var(--color-error)',
          }}
          title="Click to inspect Data Sovereignty & Zero Egress logs"
        >
          <span
            className="w-2 h-2 rounded-full animate-sovereign-pulse"
            style={{
              backgroundColor: trust.is_local ? 'var(--color-verified)' : 'var(--color-error)',
              boxShadow: trust.is_local
                ? '0 0 8px var(--color-verified-glow)'
                : '0 0 8px rgba(239,68,68,0.5)',
            }}
          />
          <span className="font-mono text-[10px]">
            {trust.is_local ? 'AIR-GAPPED / ZERO EGRESS' : 'UNSECURED NETWORK'}
          </span>
        </button>

        {/* Right panel toggle */}
        <button
          onClick={toggleRightPanel}
          className={`p-1.5 rounded-lg border transition-all ${
            ui.rightPanelVisible
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
              : 'bg-white/5 border-white/10 text-slate-400 hover:text-slate-200'
          }`}
          title={ui.rightPanelVisible ? 'Hide System Pulse Drawer' : 'Show System Pulse Drawer'}
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
