/**
 * MissionRail — Left navigation panel organized under the 5 Architectural Layers:
 * 
 * L1 · CORE RUNTIME
 * L2 · INTELLIGENCE & MODELS (Selecting any model switches middle canvas to ModelDeck)
 * L3 · GOVERNANCE & MCP
 * L4 · EXECUTION & WORKSPACES
 * L5 · TRUST & AIRGAP
 * FUTURE / ENTERPRISE (Roadmap & Specifications)
 */

import {
  Plus,
  CheckCircle2,
  FileText,
  Wrench,
  Code,
  ClipboardCheck,
  BarChart3,
  BookOpen,
  FileStack,
  FolderKanban,
  ChevronLeft,
  ChevronRight,
  Play,
  LogOut,
  Brain,
  Eye,
  Cpu,
  ShieldCheck,
  ShieldAlert,
  Compass,
  Lock,
  FileCheck,
  Layers,
  Sparkles,
} from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { useMissionStore, type Mission } from '@/store/missionStore';
import { useAuth } from '@/features/auth/useAuth';

const missionTypeIcons: Record<string, string> = {
  document: '📄',
  coding: '⌨️',
  vision: '👁️',
  analysis: '📊',
  general: '◈',
};

const statusColors: Record<string, { bg: string; text: string; dot: string }> = {
  planning: { bg: 'var(--color-info-muted)', text: 'var(--color-info)', dot: 'var(--color-info)' },
  executing: { bg: 'var(--color-running-muted)', text: 'var(--color-running)', dot: 'var(--color-running)' },
  verifying: { bg: 'var(--color-amber-muted)', text: 'var(--color-amber-primary)', dot: 'var(--color-amber-primary)' },
  completed: { bg: 'var(--color-verified-muted)', text: 'var(--color-verified)', dot: 'var(--color-verified)' },
  failed: { bg: 'var(--color-error-muted)', text: 'var(--color-error)', dot: 'var(--color-error)' },
};

export function MissionRail() {
  const { ui, toggleLeftPanel, setActiveView, routing, setSelectedModel } = useAppStore();
  const { missions, activeMissionId, setActiveMission } = useMissionStore();
  const { canAccessWorkflow, logout } = useAuth();
  const { leftPanelCollapsed } = ui;

  const activeMissions = missions.filter((m) => m.status !== 'completed' && m.status !== 'failed');
  const completedMissions = missions.filter((m) => m.status === 'completed' || m.status === 'failed');

  const handleNewMission = () => {
    setActiveMission(null);
    setActiveView('command');
  };

  const handleMissionClick = (mission: Mission) => {
    setActiveMission(mission.id);
    setActiveView('command');
  };

  const handleSelectModel = (modelName: string) => {
    setSelectedModel(modelName);
    const selected = routing.available_models.find((model) => model.name === modelName || model.id === modelName);
    const viewByRole: Record<string, 'reasoning' | 'coding' | 'vision'> = {
      reasoning: 'reasoning',
      coding: 'coding',
      vision: 'vision',
    };
    const modelView = selected ? viewByRole[selected.role] : undefined;
    if (modelView) setActiveView(modelView);
  };

  if (leftPanelCollapsed) {
    return (
      <aside
        className="w-12 flex-shrink-0 flex flex-col items-center pt-3 pb-3 border-r"
        style={{
          backgroundColor: 'var(--color-deck-deep)',
          borderColor: 'var(--color-deck-border)',
        }}
      >
        <button
          onClick={toggleLeftPanel}
          className="p-1.5 rounded mb-3 transition-colors hover:bg-[var(--color-deck-elevated)]"
          style={{ color: 'var(--color-text-muted)' }}
          title="Expand Navigation Rail"
        >
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={handleNewMission}
          className="p-2 rounded-lg mb-3 transition-colors"
          style={{
            backgroundColor: 'var(--color-amber-muted)',
            border: '1px solid var(--color-amber-border)',
            color: 'var(--color-amber-primary)',
          }}
          title="New Mission"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>

        {/* Quick Nav Icons */}
        <div className="flex flex-col items-center gap-2 mb-3">
          <button
            onClick={() => setActiveView('system')}
            className={`p-2 rounded-md text-xs transition-colors ${ui.activeView === 'system' ? 'bg-amber-500/20 text-amber-400' : 'text-slate-400 hover:text-white'}`}
            title="Models & VRAM (Center Panel)"
          >
            <Cpu className="w-4 h-4" />
          </button>
          <button
            onClick={() => setActiveView('trust')}
            className={`p-2 rounded-md text-xs transition-colors ${ui.activeView === 'trust' ? 'bg-emerald-500/20 text-emerald-400' : 'text-slate-400 hover:text-white'}`}
            title="Sovereign Trust Layer"
          >
            <ShieldCheck className="w-4 h-4" />
          </button>
          <button
            onClick={() => setActiveView('rag')}
            className={`p-2 rounded-md text-xs transition-colors ${ui.activeView === 'rag' ? 'bg-amber-500/20 text-amber-400' : 'text-slate-400 hover:text-white'}`}
            title="Verifiable RAG & Gate"
          >
            <FileCheck className="w-4 h-4" />
          </button>
        </div>

        {/* Mission dots */}
        <div className="flex-1 flex flex-col items-center gap-2 mt-1 overflow-y-auto">
          {activeMissions.map((m) => (
            <button
              key={m.id}
              onClick={() => handleMissionClick(m)}
              className={`w-7 h-7 rounded-md flex items-center justify-center text-xs font-bold transition-all ${
                activeMissionId === m.id ? 'ring-1' : ''
              }`}
              style={{
                backgroundColor: activeMissionId === m.id ? 'var(--color-amber-muted)' : 'var(--color-deck-surface)',
                border: `1px solid ${activeMissionId === m.id ? 'var(--color-amber-border)' : 'var(--color-deck-border)'}`,
                color: activeMissionId === m.id ? 'var(--color-amber-primary)' : 'var(--color-text-muted)',
              }}
              title={m.title}
            >
              {String(m.number).padStart(2, '0')}
            </button>
          ))}
        </div>
      </aside>
    );
  }

  return (
    <aside
      className="w-64 flex-shrink-0 flex flex-col border-r select-none overflow-hidden"
      style={{
        backgroundColor: 'var(--color-deck-deep)',
        borderColor: 'var(--color-deck-border)',
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: 'var(--color-deck-border)' }}
      >
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-amber-500" />
          <span className="font-label text-[10px] tracking-wider" style={{ color: 'var(--color-text-muted)' }}>
            SOVEREIGN ARCHITECTURE
          </span>
        </div>
        <button
          onClick={toggleLeftPanel}
          className="p-1 rounded transition-colors hover:bg-[var(--color-deck-elevated)]"
          style={{ color: 'var(--color-text-muted)' }}
          title="Collapse Navigation Rail"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Scrollable content with the 5 Sovereign Layers */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {/* Top: New Mission Action */}
        <button
          onClick={handleNewMission}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-bold tracking-wider uppercase transition-all hover:scale-[1.01] cursor-pointer"
          style={{
            backgroundColor: 'var(--color-amber-muted)',
            border: '1px solid var(--color-amber-border)',
            color: 'var(--color-amber-primary)',
          }}
        >
          <Plus className="w-3.5 h-3.5" />
          NEW MISSION
        </button>

        {/* ═══════════════════════════════════════════════════════════
            LAYER 1 · CORE RUNTIME
            ═══════════════════════════════════════════════════════════ */}
        <div>
          <div className="flex items-center justify-between px-1 mb-1.5">
            <span className="font-label text-[10px] tracking-wider text-slate-400 font-bold flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
              L1 · CORE RUNTIME
            </span>
            <span className="text-[9px] font-mono px-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
              8GB VRAM
            </span>
          </div>
          <div className="space-y-0.5">
            <button
              onClick={() => setActiveView('system')}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors group cursor-pointer"
              style={{
                backgroundColor: ui.activeView === 'system' ? 'var(--color-deck-surface)' : 'transparent',
                border: ui.activeView === 'system' ? '1px solid var(--color-amber-border)' : '1px solid transparent',
                color: ui.activeView === 'system' ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
              }}
              onMouseEnter={(e) => {
                if (ui.activeView !== 'system') e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
              }}
              onMouseLeave={(e) => {
                if (ui.activeView !== 'system') e.currentTarget.style.backgroundColor = 'transparent';
              }}
              title="Open Models & VRAM Command Center"
            >
              <div className="flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5" style={{ color: ui.activeView === 'system' ? 'var(--color-amber-primary)' : 'var(--color-text-muted)' }} />
                <span>Memory & VRAM Deck</span>
              </div>
              <span className="text-[9px] px-1 rounded font-mono bg-slate-800 text-slate-300">
                DISCIPLINE
              </span>
            </button>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            LAYER 2 · INTELLIGENCE & MODELS
            ═══════════════════════════════════════════════════════════ */}
        <div>
          <div className="flex items-center justify-between px-1 mb-1.5">
            <span className="font-label text-[10px] tracking-wider text-amber-400 font-bold flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-amber-400" />
              L2 · INTELLIGENCE & MODELS
            </span>
            <span className="text-[9px] font-mono px-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              MESH
            </span>
          </div>

          {/* Model Mesh Items — Selecting any model opens it directly in center panel! */}
          <div className="space-y-1 mb-2 bg-black/20 p-1.5 rounded-lg border border-slate-800/60">
            <div className="text-[9px] font-mono uppercase text-slate-500 px-1 mb-1">
              Select model for workbench:
            </div>
            {routing.available_models.map((m) => {
              const isSelected = (routing.selected_model === m.name || routing.selected_model === m.id) && ui.activeView === 'system';
              return (
                <button
                  key={m.id}
                  onClick={() => handleSelectModel(m.name)}
                  className="w-full flex items-center justify-between px-2 py-1.5 rounded-md text-xs transition-all cursor-pointer group"
                  style={{
                    backgroundColor: isSelected ? 'rgba(245, 158, 11, 0.12)' : 'transparent',
                    border: isSelected ? '1px solid var(--color-amber-border)' : '1px solid transparent',
                    color: isSelected ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                  title={`Click to open ${m.name} Workbench in middle canvas`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                        m.loaded ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
                      }`}
                    />
                    <span className="font-medium truncate text-left">{m.name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {isSelected && (
                      <span className="text-[8px] px-1 py-0.2 rounded font-mono bg-amber-500/20 text-amber-300">
                        ACTIVE
                      </span>
                    )}
                    <span className="text-[9px] px-1 py-0.2 rounded font-mono bg-slate-800 text-slate-400">
                      {(m.vram_mb / 1024).toFixed(1)}G
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Verifiable RAG & Knowledge */}
          <div className="space-y-0.5">
            <button
              onClick={() => setActiveView('rag')}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors group cursor-pointer"
              style={{
                backgroundColor: ui.activeView === 'rag' ? 'var(--color-deck-surface)' : 'transparent',
                border: ui.activeView === 'rag' ? '1px solid var(--color-amber-border)' : '1px solid transparent',
                color: ui.activeView === 'rag' ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
              }}
              onMouseEnter={(e) => {
                if (ui.activeView !== 'rag') e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
              }}
              onMouseLeave={(e) => {
                if (ui.activeView !== 'rag') e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <div className="flex items-center gap-2">
                <FileCheck className="w-3.5 h-3.5" style={{ color: ui.activeView === 'rag' ? 'var(--color-amber-primary)' : 'var(--color-text-muted)' }} />
                <span>Verifiable RAG & Gate</span>
              </div>
              <span className="text-[9px] px-1 rounded font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
                EVIDENCE
              </span>
            </button>

            <button
              onClick={() => setActiveView('command')}
              className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-colors group cursor-pointer text-slate-400 hover:text-slate-200"
            >
              <BookOpen className="w-3.5 h-3.5 text-slate-500" />
              <span>Knowledge Base & SOPs</span>
            </button>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            LAYER 3 · GOVERNANCE & IDENTITY
            ═══════════════════════════════════════════════════════════ */}
        <div>
          <div className="flex items-center justify-between px-1 mb-1.5">
            <span className="font-label text-[10px] tracking-wider text-rose-400 font-bold flex items-center gap-1.5">
              <ShieldAlert className="w-3 h-3 text-rose-400" />
              L3 · GOVERNANCE & MCP
            </span>
            <span className="text-[9px] font-mono px-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
              RBAC
            </span>
          </div>
          <div className="space-y-0.5">
            <button
              onClick={() => setActiveView('mcp')}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors group cursor-pointer"
              style={{
                backgroundColor: ui.activeView === 'mcp' ? 'var(--color-deck-surface)' : 'transparent',
                border: ui.activeView === 'mcp' ? '1px solid var(--color-amber-border)' : '1px solid transparent',
                color: ui.activeView === 'mcp' ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
              }}
              onMouseEnter={(e) => {
                if (ui.activeView !== 'mcp') e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
              }}
              onMouseLeave={(e) => {
                if (ui.activeView !== 'mcp') e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                <span>MCP Firewall & ZKP</span>
              </div>
              <span className="text-[9px] px-1 rounded font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20">
                GUARD
              </span>
            </button>

            <button
              onClick={() => setActiveView('cyberscan')}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors group cursor-pointer"
              style={{
                backgroundColor: ui.activeView === 'cyberscan' ? 'var(--color-deck-surface)' : 'transparent',
                border: ui.activeView === 'cyberscan' ? '1px solid var(--color-amber-border)' : '1px solid transparent',
                color: ui.activeView === 'cyberscan' ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
              }}
              onMouseEnter={(e) => {
                if (ui.activeView !== 'cyberscan') e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
              }}
              onMouseLeave={(e) => {
                if (ui.activeView !== 'cyberscan') e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <div className="flex items-center gap-2">
                <Lock className="w-3.5 h-3.5 text-amber-400" />
                <span>CyberScan & Audit</span>
              </div>
              <span className="text-[9px] px-1 rounded font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
                MERKLE
              </span>
            </button>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            LAYER 4 · EXECUTION & MISSIONS
            ═══════════════════════════════════════════════════════════ */}
        <div>
          <div className="flex items-center justify-between px-1 mb-1.5">
            <span className="font-label text-[10px] tracking-wider text-blue-400 font-bold flex items-center gap-1.5">
              <Code className="w-3 h-3 text-blue-400" />
              L4 · EXECUTION & MISSIONS
            </span>
            <span className="text-[9px] font-mono px-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              SANDBOX
            </span>
          </div>

          {/* Active Missions */}
          <div className="space-y-1 mb-2">
            {activeMissions.length === 0 && (
              <div className="px-2.5 py-1.5 text-xs text-slate-500 italic">
                No active missions
              </div>
            )}
            {activeMissions.map((m) => {
              const isActive = activeMissionId === m.id && ui.activeView === 'command';
              const sc = statusColors[m.status] || statusColors.planning;
              return (
                <button
                  key={m.id}
                  onClick={() => handleMissionClick(m)}
                  className="w-full flex items-start gap-2 px-2.5 py-1.5 rounded-lg text-left transition-all text-xs group cursor-pointer"
                  style={{
                    backgroundColor: isActive ? 'var(--color-deck-surface)' : 'transparent',
                    border: isActive ? '1px solid var(--color-amber-border)' : '1px solid transparent',
                  }}
                >
                  <span className="mt-0.5 text-xs">{missionTypeIcons[m.type] || '◈'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate" style={{ color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>
                      {m.title}
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span
                        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${m.status === 'executing' ? 'animate-sovereign-pulse' : ''}`}
                        style={{ backgroundColor: sc.dot }}
                      />
                      <span className="font-instrument uppercase text-[9px]" style={{ color: sc.text }}>
                        {m.status}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Completed Missions summary */}
          {completedMissions.length > 0 && (
            <div className="mb-2">
              <div className="text-[9px] font-mono uppercase text-slate-500 px-1 mb-1">
                Completed ({completedMissions.length})
              </div>
              {completedMissions.slice(0, 3).map((m) => (
                <button
                  key={m.id}
                  onClick={() => handleMissionClick(m)}
                  className="w-full flex items-center gap-2 px-2 py-1 rounded text-left text-xs transition-colors text-slate-400 hover:text-slate-200"
                >
                  <CheckCircle2 className="w-3 h-3 flex-shrink-0 text-emerald-400" />
                  <span className="truncate">{m.title}</span>
                </button>
              ))}
            </div>
          )}

          {/* Dedicated Workspaces */}
          <div className="space-y-0.5">
            {[
              { icon: Brain, label: 'Reasoning Studio', view: 'reasoning', color: 'var(--color-amber-primary)' },
              { icon: Code, label: 'Coding Sandbox', view: 'coding', color: 'var(--color-info)' },
              { icon: Eye, label: 'Vision Inspection', view: 'vision', color: '#c084fc' },
            ].map(({ icon: Icon, label, view, color }) => {
              const active = ui.activeView === view;
              return (
                <button
                  key={label}
                  onClick={() => setActiveView(view as any)}
                  className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors group cursor-pointer"
                  style={{
                    backgroundColor: active ? 'var(--color-deck-surface)' : 'transparent',
                    border: active ? `1px solid ${color}55` : '1px solid transparent',
                    color: active ? color : 'var(--color-text-secondary)',
                  }}
                >
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5" style={{ color: active ? color : 'var(--color-text-muted)' }} />
                    <span>{label}</span>
                  </div>
                  <span className="text-[9px] px-1 rounded font-mono" style={{ color, backgroundColor: `${color}18`, border: `1px solid ${color}35` }}>
                    LANE
                  </span>
                </button>
              );
            })}
          </div>

          {/* Role-Specific Work Tools */}
          <div className="mt-1.5 space-y-0.5">
            {[
              { icon: FileText, label: 'Documents', workflow: null },
              { icon: Wrench, label: 'Engineering Inspections', workflow: 'inspection' },
              { icon: ClipboardCheck, label: 'Approvals Gate', workflow: null },
              { icon: BarChart3, label: 'Analysis & Telemetry', workflow: null },
            ]
              .filter(({ workflow }) => !workflow || canAccessWorkflow(workflow))
              .map(({ icon: Icon, label }) => (
                <button
                  key={label}
                  onClick={() => setActiveView('command')}
                  className="w-full flex items-center gap-2 px-2.5 py-1 rounded text-xs transition-colors text-slate-400 hover:text-slate-200"
                >
                  <Icon className="w-3.5 h-3.5 text-slate-500" />
                  <span>{label}</span>
                </button>
              ))}
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            LAYER 5 · TRUST & SOVEREIGNTY
            ═══════════════════════════════════════════════════════════ */}
        <div>
          <div className="flex items-center justify-between px-1 mb-1.5">
            <span className="font-label text-[10px] tracking-wider text-emerald-400 font-bold flex items-center gap-1.5">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              L5 · TRUST & AIRGAP
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              0 EGRESS
            </span>
          </div>

          <div className="space-y-0.5">
            <button
              onClick={() => setActiveView('trust')}
              className="w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs transition-colors group cursor-pointer"
              style={{
                backgroundColor: ui.activeView === 'trust' ? 'var(--color-amber-muted)' : 'rgba(16, 185, 129, 0.05)',
                border: ui.activeView === 'trust' ? '1px solid var(--color-amber-border)' : '1px solid rgba(16, 185, 129, 0.2)',
                color: ui.activeView === 'trust' ? 'var(--color-amber-primary)' : 'var(--color-verified)',
              }}
              onMouseEnter={(e) => {
                if (ui.activeView !== 'trust') e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
              }}
              onMouseLeave={(e) => {
                if (ui.activeView !== 'trust') e.currentTarget.style.backgroundColor = 'rgba(16, 185, 129, 0.05)';
              }}
            >
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="font-bold">Trust Layer (Unified)</span>
              </div>
              <span className="text-[9px] px-1 rounded font-mono bg-emerald-500/20 text-emerald-300">
                ACTIVE
              </span>
            </button>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            KNOWLEDGE REPOSITORY
            ═══════════════════════════════════════════════════════════ */}
        <div>
          <h3 className="font-label mb-2 px-1 text-slate-400">KNOWLEDGE REPOSITORY</h3>
          <div className="space-y-1">
            {[
              { icon: BookOpen, label: 'SOPs & Standards', count: '48' },
              { icon: FileStack, label: 'Technical Manuals', count: '32' },
              { icon: FileText, label: 'Audit Reports', count: '29' },
              { icon: FolderKanban, label: 'Plant Schematics', count: '19' },
            ].map(({ icon: Icon, label, count }) => (
              <button
                key={label}
                type="button"
                onClick={() => {
                  setActiveView('trust');
                }}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs transition-all text-slate-300 hover:bg-slate-800/80 hover:text-amber-300 cursor-pointer group"
                title={`Open ${label} in Trust Center`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-3.5 h-3.5 text-slate-400 group-hover:text-amber-400 transition-colors" />
                  <span>{label}</span>
                </div>
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 group-hover:text-amber-300 border border-white/5">
                  {count}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════
            FUTURE / ENTERPRISE ROADMAP
            ═══════════════════════════════════════════════════════════ */}
        <div>
          <div className="flex items-center justify-between px-1 mb-1.5">
            <span className="font-label text-[10px] tracking-wider text-slate-500 font-bold flex items-center gap-1.5">
              <Compass className="w-3 h-3 text-slate-500" />
              FUTURE · ENTERPRISE
            </span>
            <span className="text-[9px] font-mono px-1 rounded bg-slate-800 text-slate-500 border border-slate-700">
              SPECS
            </span>
          </div>

          <div className="space-y-0.5">
            <button
              onClick={() => setActiveView('attestation')}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors group cursor-pointer"
              style={{
                backgroundColor: ui.activeView === 'attestation' ? 'var(--color-deck-surface)' : 'transparent',
                border: ui.activeView === 'attestation' ? '1px solid var(--color-amber-border)' : '1px solid transparent',
                color: ui.activeView === 'attestation' ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
              }}
              onMouseEnter={(e) => {
                if (ui.activeView !== 'attestation') e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
              }}
              onMouseLeave={(e) => {
                if (ui.activeView !== 'attestation') e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
                <span>TEE Remote Attestation</span>
              </div>
              <span className="text-[9px] px-1 rounded font-mono bg-slate-800 text-slate-400">
                SEV-SNP
              </span>
            </button>

            <button
              onClick={() => setActiveView('mantic')}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors group cursor-pointer"
              style={{
                backgroundColor: ui.activeView === 'mantic' ? 'var(--color-deck-surface)' : 'transparent',
                border: ui.activeView === 'mantic' ? '1px solid var(--color-amber-border)' : '1px solid transparent',
                color: ui.activeView === 'mantic' ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
              }}
              onMouseEnter={(e) => {
                if (ui.activeView !== 'mantic') e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
              }}
              onMouseLeave={(e) => {
                if (ui.activeView !== 'mantic') e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <div className="flex items-center gap-2">
                <Compass className="w-3.5 h-3.5 text-slate-400" />
                <span>Mantic Scaffold Engine</span>
              </div>
              <span className="text-[9px] px-1 rounded font-mono bg-slate-800 text-slate-400">
                ZKP
              </span>
            </button>
          </div>
        </div>
      </nav>

      {/* Footer — Engine Ready + Logout */}
      <div className="px-4 py-3 border-t" style={{ borderColor: 'var(--color-deck-border)' }}>
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center gap-1.5 font-instrument" style={{ color: 'var(--color-text-muted)' }}>
            <Play className="w-3 h-3" style={{ color: 'var(--color-verified)' }} />
            ENGINE READY
          </span>
          <span className="font-instrument text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            {activeMissions.length} ACTIVE
          </span>
        </div>
        {/* Mobile logout */}
        <button
          onClick={logout}
          className="md:hidden w-full flex items-center justify-center gap-1.5 mt-2 px-3 py-1.5 rounded text-xs font-semibold tracking-wider transition-colors"
          style={{
            color: 'var(--color-text-muted)',
            border: '1px solid var(--color-deck-border)',
          }}
        >
          <LogOut className="w-3 h-3" />
          SIGN OUT
        </button>
      </div>
    </aside>
  );
}
