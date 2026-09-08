/**
 * MissionRail — Left navigation panel
 *
 * Not a conventional sidebar. Organized by:
 * COMMAND → MISSIONS → WORK → KNOWLEDGE
 */

import {
  Plus,
  Target,
  CheckCircle2,
  Archive,
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
} from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { useMissionStore, type Mission } from '@/store/missionStore';

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
  const { ui, toggleLeftPanel, setActiveView } = useAppStore();
  const { missions, activeMissionId, setActiveMission } = useMissionStore();
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
          className="p-1.5 rounded mb-4 transition-colors hover:bg-[var(--color-deck-elevated)]"
          style={{ color: 'var(--color-text-muted)' }}
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

        {/* Mission dots */}
        <div className="flex-1 flex flex-col items-center gap-2 mt-2 overflow-y-auto">
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
                ringColor: 'var(--color-amber-border)',
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
      className="w-60 flex-shrink-0 flex flex-col border-r select-none overflow-hidden"
      style={{
        backgroundColor: 'var(--color-deck-deep)',
        borderColor: 'var(--color-deck-border)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: 'var(--color-deck-border)' }}
      >
        <span className="font-label" style={{ color: 'var(--color-text-muted)', fontSize: '10px' }}>
          NAVIGATION
        </span>
        <button
          onClick={toggleLeftPanel}
          className="p-1 rounded transition-colors hover:bg-[var(--color-deck-elevated)]"
          style={{ color: 'var(--color-text-muted)' }}
        >
          <ChevronLeft className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Scrollable content */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {/* New Mission Button */}
        <button
          onClick={handleNewMission}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all hover:scale-[1.01]"
          style={{
            backgroundColor: 'var(--color-amber-muted)',
            border: '1px solid var(--color-amber-border)',
            color: 'var(--color-amber-primary)',
          }}
        >
          <Plus className="w-4 h-4" />
          New Mission
        </button>

        {/* MISSIONS */}
        <div>
          <h3 className="font-label mb-2 px-1">MISSIONS</h3>
          <div className="space-y-1">
            {activeMissions.length === 0 && (
              <div className="px-3 py-2 text-xs" style={{ color: 'var(--color-text-dim)' }}>
                No active missions
              </div>
            )}
            {activeMissions.map((m) => {
              const isActive = activeMissionId === m.id;
              const sc = statusColors[m.status] || statusColors.planning;
              return (
                <button
                  key={m.id}
                  onClick={() => handleMissionClick(m)}
                  className={`w-full flex items-start gap-2.5 px-3 py-2 rounded-lg text-left transition-all text-xs group`}
                  style={{
                    backgroundColor: isActive ? 'var(--color-deck-surface)' : 'transparent',
                    border: isActive ? '1px solid var(--color-amber-border)' : '1px solid transparent',
                  }}
                >
                  <span className="mt-0.5 text-sm">{missionTypeIcons[m.type] || '◈'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate" style={{ color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>
                      {m.title}
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span
                        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${m.status === 'executing' ? 'animate-sovereign-pulse' : ''}`}
                        style={{ backgroundColor: sc.dot }}
                      />
                      <span className="font-instrument uppercase" style={{ color: sc.text, fontSize: '9px' }}>
                        {m.status}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}

            {/* Completed section */}
            {completedMissions.length > 0 && (
              <div className="mt-3">
                <h4 className="font-label mb-1.5 px-1" style={{ fontSize: '9px' }}>COMPLETED</h4>
                {completedMissions.slice(0, 5).map((m) => (
                  <button
                    key={m.id}
                    onClick={() => handleMissionClick(m)}
                    className="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-left text-xs transition-colors"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    <CheckCircle2 className="w-3 h-3 flex-shrink-0" style={{ color: 'var(--color-verified)' }} />
                    <span className="truncate">{m.title}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* WORK */}
        <div>
          <h3 className="font-label mb-2 px-1">WORK</h3>
          <div className="space-y-0.5">
            {[
              { icon: FileText, label: 'Documents' },
              { icon: Wrench, label: 'Engineering' },
              { icon: Code, label: 'Coding' },
              { icon: ClipboardCheck, label: 'Approvals' },
              { icon: BarChart3, label: 'Analysis' },
            ].map(({ icon: Icon, label }) => (
              <button
                key={label}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-colors group"
                style={{ color: 'var(--color-text-secondary)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <Icon className="w-3.5 h-3.5" style={{ color: 'var(--color-text-muted)' }} />
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* KNOWLEDGE */}
        <div>
          <h3 className="font-label mb-2 px-1">KNOWLEDGE</h3>
          <div className="space-y-0.5">
            {[
              { icon: BookOpen, label: 'SOPs' },
              { icon: FileStack, label: 'Manuals' },
              { icon: FileText, label: 'Reports' },
              { icon: FolderKanban, label: 'Projects' },
            ].map(({ icon: Icon, label }) => (
              <button
                key={label}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-colors"
                style={{ color: 'var(--color-text-secondary)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-deck-surface)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <Icon className="w-3.5 h-3.5" style={{ color: 'var(--color-text-muted)' }} />
                {label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Footer — Quick stats */}
      <div className="px-4 py-3 border-t" style={{ borderColor: 'var(--color-deck-border)' }}>
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center gap-1.5 font-instrument" style={{ color: 'var(--color-text-muted)' }}>
            <Play className="w-3 h-3" style={{ color: 'var(--color-verified)' }} />
            ENGINE READY
          </span>
          <span className="font-instrument" style={{ color: 'var(--color-verified)' }}>
            {activeMissions.length} ACTIVE
          </span>
        </div>
      </div>
    </aside>
  );
}
