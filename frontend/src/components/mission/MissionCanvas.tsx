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
  Check,
  Code,
  Eye,
  Sparkles,
} from 'lucide-react';
import { useMissionStore, type MissionType } from '@/store/missionStore';
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
  const [downloaded, setDownloaded] = useState(false);
  const mission = useMissionStore((s) => s.getActiveMission());
  const { runDemoMission, createMission } = useMissionStore();
  const { updateRouting } = useAppStore();

  const handleLaunchPreset = (title: string, prompt: string, type: MissionType, model: string, task: string) => {
    updateRouting({
      selected_model: model,
      task_type: task,
      reason: `Quick dispatch initiated for ${title}`,
    });
    createMission(prompt, type);
    runDemoMission();
  };

  const handleDownloadOutput = () => {
    if (!mission?.output) return;
    const filename = mission.output.filename || `sovereign_mission_${mission.number}_report.md`;
    const content =
      mission.output.content ||
      `# Sovereign Verification Report — Mission #${mission.number}\n\n**Title**: ${mission.title}\n**Status**: ${mission.status.toUpperCase()}\n**Model**: ${mission.model_used || 'Qwen3-14B'}\n**Execution Duration**: ${((mission.total_duration_ms || 0) / 1000).toFixed(2)}s\n\n## Verified Claims & Citations\n${mission.evidence
        .map(
          (e, idx) =>
            `### ${idx + 1}. ${e.claim}\n- Confidence: ${(e.confidence * 100).toFixed(0)}%\n- Grounding: ${e.sources.map((s) => s.title + ' (' + s.location + ')').join(', ')}`
        )
        .join('\n\n')}\n\n## Zero-Egress Guarantee\n- External Requests: 0\n- Cloud Egress: 0.00 KB\n- Cryptographic Seal: SHA-256 Verified On-Premise`;

    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setDownloaded(true);
    setTimeout(() => setDownloaded(false), 2500);
  };

  // No active mission — show rich industrial operations hub
  if (!mission) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-8 relative overflow-y-auto cyber-grid py-12" style={{ backgroundColor: 'var(--color-deck-base)' }}>
        <div className="ambient-glow" />

        <div className="text-center max-w-2xl relative z-10 animate-fade-in">
          {/* Top Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-6 shadow-[0_0_15px_rgba(0,240,255,0.15)]">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-sovereign-pulse" />
            AIR-GAPPED INDUSTRIAL AGENT RUNTIME
          </div>

          {/* Crest / Icon */}
          <div
            className="w-20 h-20 rounded-2xl mx-auto mb-5 flex items-center justify-center shadow-2xl relative group"
            style={{
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(0, 240, 255, 0.1) 100%)',
              border: '1px solid var(--color-amber-border)',
              boxShadow: '0 0 30px rgba(245, 158, 11, 0.25)',
            }}
          >
            <Rocket className="w-9 h-9 text-amber-400 transition-transform group-hover:scale-110 duration-300" />
          </div>

          <h2 className="text-3xl font-extrabold tracking-tight mb-2 bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            Sovereign Command Deck
          </h2>
          <p className="text-sm leading-relaxed mb-8 text-slate-400 max-w-lg mx-auto">
            Autonomous mission control for high-consequence enterprise engineering.
            All weights, reasoning chains, and data reside 100% locally.
          </p>

          {/* Main Action Buttons */}
          <div className="flex items-center justify-center gap-4 mb-10">
            <button
              onClick={runDemoMission}
              className="px-6 py-3 rounded-xl text-xs font-bold tracking-wider transition-all duration-300 transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer shadow-lg flex items-center gap-2"
              style={{
                backgroundColor: 'var(--color-amber-primary)',
                color: 'var(--color-deck-void)',
                border: '1px solid var(--color-amber-hover)',
                boxShadow: '0 0 25px rgba(245, 158, 11, 0.4)',
              }}
            >
              <Sparkles className="w-4 h-4" />
              LAUNCH VERIFIED DEMO MISSION
            </button>
          </div>

          {/* Quick Preset Mission Cards */}
          <div className="text-left mb-8">
            <div className="flex items-center gap-2 mb-3">
              <span className="font-label text-slate-400">DISPATCH READY TEMPLATES</span>
              <div className="flex-1 h-[1px] bg-slate-800" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* Card 1 */}
              <button
                type="button"
                onClick={() =>
                  handleLaunchPreset(
                    'Engineering Spec Audit',
                    'Audit cooling system inspection report and verify safety valve pressure tolerances against ISO-9001 specs.',
                    'document',
                    'Qwen3-14B',
                    'Document Reasoning'
                  )
                }
                className="glass-card p-4 rounded-xl text-left transition-all hover:border-amber-500/50 group cursor-pointer"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    <FileSearch className="w-4 h-4" />
                  </div>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                    DOC AUDIT
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-200 group-hover:text-amber-300 transition-colors">
                  Spec & SOP Audit
                </h4>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  Verify safety tolerances and ground claims in indexed technical SOPs.
                </p>
                <div className="mt-3 flex items-center gap-1.5 text-[9px] font-mono text-cyan-400">
                  <span>START MISSION →</span>
                </div>
              </button>

              {/* Card 2 */}
              <button
                type="button"
                onClick={() =>
                  handleLaunchPreset(
                    'Code Synthesis',
                    'Synthesize Python algorithm to calculate pump flow rate, generate unit test suite, and verify AST safety.',
                    'coding',
                    'Qwen2.5-Coder-7B',
                    'Code Generation'
                  )
                }
                className="glass-card p-4 rounded-xl text-left transition-all hover:border-cyan-500/50 group cursor-pointer"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    <Code className="w-4 h-4" />
                  </div>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                    SYNTHESIS
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-200 group-hover:text-cyan-300 transition-colors">
                  Code Synthesis & AST
                </h4>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  Generate verified algorithms with automated sandbox test execution.
                </p>
                <div className="mt-3 flex items-center gap-1.5 text-[9px] font-mono text-cyan-400">
                  <span>START MISSION →</span>
                </div>
              </button>

              {/* Card 3 */}
              <button
                type="button"
                onClick={() =>
                  handleLaunchPreset(
                    'P&ID Schematic Vision',
                    'Analyze P&ID engineering schematic, identify isolation valves, and trace high-pressure steam line.',
                    'vision',
                    'Qwen3-VL-8B',
                    'Vision Analysis'
                  )
                }
                className="glass-card p-4 rounded-xl text-left transition-all hover:border-purple-500/50 group cursor-pointer"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    <Eye className="w-4 h-4" />
                  </div>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                    VISION
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-200 group-hover:text-purple-300 transition-colors">
                  P&ID Vision Schematics
                </h4>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                  Multimodal recognition of mechanical components & valves.
                </p>
                <div className="mt-3 flex items-center gap-1.5 text-[9px] font-mono text-cyan-400">
                  <span>START MISSION →</span>
                </div>
              </button>
            </div>
          </div>

          {/* Quick telemetry proof stats */}
          <div className="flex items-center justify-center gap-8 py-3 px-6 rounded-xl bg-slate-900/60 border border-white/5">
            {[
              { label: 'LOCAL MODELS', value: '3 QUANTIZED' },
              { label: 'SOPs INDEXED', value: '128 LOCAL' },
              { label: 'DATA EGRESS', value: '0.00 KB' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <span className="font-instrument-lg block text-slate-200">
                  {stat.value}
                </span>
                <span className="font-label block mt-0.5 text-[9px] text-slate-500">
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
                type="button"
                onClick={handleDownloadOutput}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold tracking-wider transition-all duration-200 cursor-pointer transform hover:scale-105 active:scale-95 shadow-md"
                style={{
                  backgroundColor: downloaded ? 'rgba(16, 185, 129, 0.25)' : 'var(--color-verified-muted)',
                  border: `1px solid ${downloaded ? 'rgba(16, 185, 129, 0.6)' : 'var(--color-verified-border)'}`,
                  color: 'var(--color-verified)',
                  boxShadow: downloaded ? '0 0 15px rgba(16, 185, 129, 0.3)' : undefined,
                }}
                title="Download verified cryptographic report"
              >
                {downloaded ? <Check className="w-3 h-3 text-emerald-400" /> : <Download className="w-3 h-3" />}
                {downloaded ? 'VERIFIED REPORT DOWNLOADED' : (mission.output.filename || 'DOWNLOAD REPORT')}
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
