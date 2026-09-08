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
        onClick={() => step.metrics && setExpanded(!expanded)}
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
                  className="font-instrument-lg block"
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
                <span className="font-instrument" style={{ color: 'var(--color-text-secondary)' }}>
                  {step.duration_ms}ms
                </span>
              )}
              <span
                className="text-[9px] font-bold tracking-widest px-1.5 py-0.5 rounded"
                style={{
                  color: config.color,
                  backgroundColor: step.status !== 'queued' ? config.bg : 'transparent',
                }}
              >
                {config.label}
              </span>
              {step.metrics && (
                expanded
                  ? <ChevronUp className="w-3 h-3" style={{ color: 'var(--color-text-muted)' }} />
                  : <ChevronDown className="w-3 h-3" style={{ color: 'var(--color-text-muted)' }} />
              )}
            </div>
          </div>

          {/* Running progress bar */}
          {isRunning && (
            <div className="mt-2.5 h-1 w-full rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-deck-elevated)' }}>
              <div
                className="h-full rounded-full progress-striped"
                style={{
                  width: '70%',
                  backgroundColor: 'var(--color-running)',
                  transition: 'width 1s ease',
                }}
              />
            </div>
          )}

          {/* Expanded metrics */}
          {expanded && step.metrics && (
            <div className="mt-3 pt-2 border-t space-y-1" style={{ borderColor: 'var(--color-deck-border)' }}>
              {Object.entries(step.metrics).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="font-instrument" style={{ color: 'var(--color-text-primary)' }}>
                    {String(value)}
                  </span>
                </div>
              ))}
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
