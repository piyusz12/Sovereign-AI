/**
 * MissionCanvas — The center panel, biggest differentiator
 *
 * Shows the active mission with tabbed views:
 * PIPELINE | EVIDENCE | TRACE | MODEL
 *
 * When no mission is active, shows a "start mission" prompt.
 */

import { useState } from 'react';
import {
  Workflow,
  FileSearch,
  ListChecks,
  Brain,
  Rocket,
  Download,
  Clock,
} from 'lucide-react';
import { useMissionStore } from '@/store/missionStore';
import { useAppStore } from '@/store/appStore';
import { PipelineView } from './PipelineView';
import { EvidencePanel } from './EvidencePanel';
import { MissionTrace } from './MissionTrace';
import { ModelBrain } from './ModelBrain';

type CanvasTab = 'pipeline' | 'evidence' | 'trace' | 'model';

const tabs: Array<{ id: CanvasTab; label: string; icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }> }> = [
  { id: 'pipeline', label: 'PIPELINE', icon: Workflow },
  { id: 'evidence', label: 'EVIDENCE', icon: FileSearch },
  { id: 'trace', label: 'TRACE', icon: ListChecks },
  { id: 'model', label: 'MODEL', icon: Brain },
];

const missionStatusConfig: Record<string, { color: string; bg: string; label: string }> = {
  planning: { color: 'var(--color-info)', bg: 'var(--color-info-muted)', label: 'PLANNING' },
  executing: { color: 'var(--color-running)', bg: 'var(--color-running-muted)', label: 'EXECUTING' },
  verifying: { color: 'var(--color-amber-primary)', bg: 'var(--color-amber-muted)', label: 'VERIFYING' },
  completed: { color: 'var(--color-verified)', bg: 'var(--color-verified-muted)', label: 'COMPLETED' },
  failed: { color: 'var(--color-error)', bg: 'var(--color-error-muted)', label: 'FAILED' },
};

export function MissionCanvas() {
  const [activeTab, setActiveTab] = useState<CanvasTab>('pipeline');
  const mission = useMissionStore((s) => s.getActiveMission());
  const { currentUser, availableWorkflows } = useAppStore();

  // No active mission — show welcome
  if (!mission) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-8" style={{ backgroundColor: 'var(--color-deck-base)' }}>
        <div className="text-center max-w-md animate-fade-in">
          {/* Icon */}
          <div
            className="w-16 h-16 rounded-2xl mx-auto mb-6 flex items-center justify-center"
            style={{
              backgroundColor: 'var(--color-amber-muted)',
              border: '1px solid var(--color-amber-border)',
            }}
          >
            <Rocket className="w-7 h-7" style={{ color: 'var(--color-amber-primary)' }} />
          </div>

          <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
            Sovereign Command Deck
          </h2>
          <p className="text-sm leading-relaxed mb-6" style={{ color: 'var(--color-text-secondary)' }}>
            Mission Control for enterprise knowledge work.
            <br />
            All inference runs locally. Zero data egress.
          </p>

          {/* Available workflows for this role */}
          {currentUser && availableWorkflows.length > 0 && (
            <div
              className="inline-flex flex-wrap items-center justify-center gap-2 px-4 py-3 rounded-lg mb-4"
              style={{
                backgroundColor: 'var(--color-deck-surface)',
                border: '1px solid var(--color-deck-border)',
              }}
            >
              <span className="text-[10px] tracking-widest font-semibold w-full mb-1" style={{ color: 'var(--color-text-muted)' }}>
                YOUR WORKFLOWS
              </span>
              {availableWorkflows.map((wf) => (
                <span
                  key={wf}
                  className="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase"
                  style={{
                    backgroundColor: 'var(--color-amber-muted)',
                    border: '1px solid var(--color-amber-border)',
                    color: 'var(--color-amber-primary)',
                  }}
                >
                  {wf.replace('_', ' ')}
                </span>
              ))}
            </div>
          )}

          <p className="text-[10px] mt-4" style={{ color: 'var(--color-text-dim)' }}>
            Type a command in the bar below to start a new mission
          </p>

          {/* Quick stats */}
          <div className="flex items-center justify-center gap-6 mt-8">
            {[
              { label: 'MODELS', value: '3 LOCAL' },
              { label: 'DOCUMENTS', value: '128 INDEXED' },
              { label: 'EGRESS', value: '0 MB' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <span className="font-instrument-lg block" style={{ color: 'var(--color-text-primary)' }}>
                  {stat.value}
                </span>
                <span className="font-label block mt-0.5" style={{ fontSize: '8px' }}>
                  {stat.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Active mission — show canvas
  const sc = missionStatusConfig[mission.status] || missionStatusConfig.planning;
  const completedSteps = mission.pipeline.filter((s) => s.status === 'verified').length;
  const totalSteps = mission.pipeline.length;
  const progressPercent = Math.round((completedSteps / totalSteps) * 100);

  return (
    <div className="flex-1 flex flex-col overflow-hidden" style={{ backgroundColor: 'var(--color-deck-base)' }}>
      {/* Mission header */}
      <div className="flex-shrink-0 px-5 py-3 border-b" style={{ borderColor: 'var(--color-deck-border)' }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Mission number */}
            <span
              className="font-instrument px-2 py-0.5 rounded"
              style={{
                backgroundColor: 'var(--color-deck-surface)',
                border: '1px solid var(--color-deck-border)',
                color: 'var(--color-text-muted)',
                fontSize: '10px',
              }}
            >
              MISSION #{String(mission.number).padStart(3, '0')}
            </span>
            {/* Title */}
            <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              {mission.title}
            </h3>
          </div>

          <div className="flex items-center gap-3">
            {/* Duration */}
            {mission.total_duration_ms && (
              <span className="flex items-center gap-1 font-instrument" style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>
                <Clock className="w-3 h-3" />
                {(mission.total_duration_ms / 1000).toFixed(1)}s
              </span>
            )}

            {/* Status badge */}
            <span
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider ${
                mission.status === 'executing' ? 'animate-sovereign-pulse' : ''
              }`}
              style={{ backgroundColor: sc.bg, color: sc.color, border: `1px solid ${sc.color}30` }}
            >
              <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: sc.color }} />
              {sc.label}
            </span>

            {/* Output download */}
            {mission.output && (
              <button
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold tracking-wider transition-all"
                style={{
                  backgroundColor: 'var(--color-verified-muted)',
                  border: '1px solid var(--color-verified-border)',
                  color: 'var(--color-verified)',
                }}
              >
                <Download className="w-3 h-3" />
                {mission.output.filename || mission.output.type}
              </button>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-2 flex items-center gap-3">
          <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-deck-elevated)' }}>
            <div
              className={`h-full rounded-full transition-all duration-700 ${mission.status === 'executing' ? 'progress-striped' : ''}`}
              style={{
                width: `${progressPercent}%`,
                backgroundColor: progressPercent === 100 ? 'var(--color-verified)' : 'var(--color-amber-primary)',
              }}
            />
          </div>
          <span className="font-instrument flex-shrink-0" style={{ color: 'var(--color-text-muted)', fontSize: '10px' }}>
            {progressPercent}%
          </span>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex-shrink-0 flex items-center gap-0 px-5 border-b" style={{ borderColor: 'var(--color-deck-border)' }}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex items-center gap-1.5 px-4 py-2.5 text-[10px] font-bold tracking-wider transition-colors relative"
              style={{
                color: isActive ? 'var(--color-amber-primary)' : 'var(--color-text-muted)',
              }}
            >
              <Icon
                className="w-3.5 h-3.5"
                style={{ color: isActive ? 'var(--color-amber-primary)' : 'var(--color-text-dim)' }}
              />
              {tab.label}
              {/* Active tab indicator */}
              {isActive && (
                <span
                  className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full"
                  style={{ backgroundColor: 'var(--color-amber-primary)' }}
                />
              )}
              {/* Badge for evidence count */}
              {tab.id === 'evidence' && mission.evidence.length > 0 && (
                <span
                  className="ml-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold"
                  style={{
                    backgroundColor: 'var(--color-amber-muted)',
                    color: 'var(--color-amber-primary)',
                  }}
                >
                  {mission.evidence.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'pipeline' && <PipelineView steps={mission.pipeline} />}
        {activeTab === 'evidence' && <EvidencePanel evidence={mission.evidence} />}
        {activeTab === 'trace' && <MissionTrace trace={mission.trace} baseTime={mission.createdAt} />}
        {activeTab === 'model' && <ModelBrain />}
      </div>
    </div>
  );
}
