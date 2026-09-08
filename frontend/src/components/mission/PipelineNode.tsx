/**
 * PipelineNode — Individual pipeline step card
 *
 * States: ○ queued → ● running (amber pulse) → ◉ verified (green) → ✗ failed (red)
 * Shows: name, status indicator, metrics, timing, progress bar
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { PipelineStep, StepStatus } from '@/store/missionStore';

const statusConfig: Record<StepStatus, { symbol: string; color: string; bg: string; border: string; glow: string; label: string }> = {
  queued: {
    symbol: '○',
    color: 'var(--color-queued)',
    bg: 'var(--color-queued-muted)',
    border: 'var(--color-deck-border)',
    glow: '',
    label: 'QUEUED',
  },
  running: {
    symbol: '●',
    color: 'var(--color-running)',
    bg: 'var(--color-running-muted)',
    border: 'var(--color-running-border)',
    glow: '0 0 12px rgba(245, 158, 11, 0.2)',
    label: 'RUNNING',
  },
  verified: {
    symbol: '◉',
    color: 'var(--color-verified)',
    bg: 'var(--color-verified-muted)',
    border: 'var(--color-verified-border)',
    glow: '',
    label: 'VERIFIED',
  },
  failed: {
    symbol: '✗',
    color: 'var(--color-error)',
    bg: 'var(--color-error-muted)',
    border: 'var(--color-error-border)',
    glow: '0 0 12px rgba(239, 68, 68, 0.15)',
    label: 'FAILED',
  },
  skipped: {
    symbol: '—',
    color: 'var(--color-text-dim)',
    bg: 'transparent',
    border: 'var(--color-deck-border)',
    glow: '',
    label: 'SKIPPED',
  },
};

interface PipelineNodeProps {
  step: PipelineStep;
  isLast: boolean;
}

export function PipelineNode({ step, isLast }: PipelineNodeProps) {
  const [expanded, setExpanded] = useState(false);
  const config = statusConfig[step.status];
  const isRunning = step.status === 'running';

  return (
    <div className="flex flex-col items-center">
      {/* Node Card */}
      <div
        className={`w-full max-w-md rounded-lg transition-all duration-300 cursor-pointer ${isRunning ? 'animate-node-running' : ''}`}
        style={{
          backgroundColor: config.bg,
          border: `1px solid ${config.border}`,
          boxShadow: config.glow || undefined,
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="px-4 py-3">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Status indicator */}
              <span
                className={`text-lg leading-none ${isRunning ? 'animate-sovereign-pulse' : ''}`}
                style={{ color: config.color }}
              >
                {config.symbol}
              </span>
              {/* Name */}
              <div>
                <span
                  className="font-instrument-lg block group-hover:text-cyan-300 transition-colors"
                  style={{ color: step.status === 'queued' ? 'var(--color-text-muted)' : 'var(--color-text-primary)' }}
                >
                  {step.name}
                </span>
                <span className="text-[10px] block mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                  {step.description}
                </span>
              </div>
            </div>

            {/* Right side */}
            <div className="flex items-center gap-2">
              {step.duration_ms && (
                <span className="font-instrument px-1.5 py-0.5 rounded bg-black/30 border border-white/5" style={{ color: 'var(--color-text-secondary)' }}>
                  {step.duration_ms}ms
                </span>
              )}
              <span
                className="text-[9px] font-bold tracking-widest px-2 py-0.5 rounded-full border"
                style={{
                  color: config.color,
                  backgroundColor: step.status !== 'queued' ? config.bg : 'transparent',
                  borderColor: config.border,
                }}
              >
                {config.label}
              </span>
              <button
                type="button"
                className="p-1 rounded hover:bg-white/5 transition-colors"
                aria-label={expanded ? 'Collapse step' : 'Expand step'}
              >
                {expanded ? (
                  <ChevronUp className="w-3.5 h-3.5 text-cyan-400" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                )}
              </button>
            </div>
          </div>

          {/* Running progress bar */}
          {isRunning && (
            <div className="mt-2.5 h-1.5 w-full rounded-full overflow-hidden bg-slate-950/80 border border-amber-500/20">
              <div
                className="h-full rounded-full progress-striped"
                style={{
                  width: '85%',
                  backgroundColor: 'var(--color-running)',
                  transition: 'width 1s ease',
                  boxShadow: '0 0 10px rgba(245, 158, 11, 0.5)',
                }}
              />
            </div>
          )}

          {/* Expanded details & metrics */}
          {expanded && (
            <div className="mt-3 pt-2.5 border-t border-white/10 space-y-2 animate-fade-in text-xs">
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>STAGE LOGS & METRICS</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    navigator.clipboard?.writeText(
                      JSON.stringify({ step: step.name, status: step.status, metrics: step.metrics, duration: step.duration_ms }, null, 2)
                    );
                  }}
                  className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition-all active:scale-95"
                  title="Copy step telemetry"
                >
                  COPY JSON
                </button>
              </div>

              {step.metrics && Object.keys(step.metrics).length > 0 ? (
                <div className="space-y-1 bg-black/40 p-2 rounded border border-white/5">
                  {Object.entries(step.metrics).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-[10px] uppercase tracking-wider text-slate-400">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className="font-instrument text-cyan-200">
                        {String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-[11px] text-slate-500 italic bg-black/20 p-2 rounded">
                  {step.status === 'queued' ? 'Awaiting execution slot...' : 'Step completed cleanly with zero telemetry warnings.'}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Connector line to next node */}
      {!isLast && (
        <div className="flex flex-col items-center py-1">
          <div
            className={`w-0.5 h-6 rounded-full ${isRunning ? 'pipeline-connector-active' : ''}`}
            style={{
              backgroundColor: step.status === 'verified'
                ? 'var(--color-verified-border)'
                : step.status === 'running'
                  ? 'var(--color-amber-border)'
                  : 'var(--color-deck-border)',
            }}
          />
          <div
            className="w-0 h-0"
            style={{
              borderLeft: '4px solid transparent',
              borderRight: '4px solid transparent',
              borderTop: `5px solid ${
                step.status === 'verified'
                  ? 'var(--color-verified-border)'
                  : 'var(--color-deck-border)'
              }`,
            }}
          />
        </div>
      )}
    </div>
  );
}
