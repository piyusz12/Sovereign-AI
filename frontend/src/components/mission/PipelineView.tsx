/**
 * PipelineView — Visual agent workflow pipeline
 *
 * Vertical chain of PipelineNode components showing the full
 * execution flow from USER REQUEST → OUTPUT
 */

import type { PipelineStep } from '@/store/missionStore';
import { PipelineNode } from './PipelineNode';

interface PipelineViewProps {
  steps: PipelineStep[];
}

export function PipelineView({ steps }: PipelineViewProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <span className="font-instrument" style={{ color: 'var(--color-text-dim)' }}>
          No pipeline steps defined
        </span>
      </div>
    );
  }

  // Calculate progress
  const completed = steps.filter((s) => s.status === 'verified').length;
  const running = steps.filter((s) => s.status === 'running').length;
  const total = steps.length;
  const progressPercent = Math.round(((completed + running * 0.5) / total) * 100);

  return (
    <div className="flex flex-col items-center py-4 px-4">
      {/* Progress summary */}
      <div className="w-full max-w-md mb-4 px-1">
        <div className="flex items-center justify-between mb-1.5">
          <span className="font-label">PIPELINE PROGRESS</span>
          <span className="font-instrument" style={{ color: 'var(--color-amber-primary)' }}>
            {progressPercent}%
          </span>
        </div>
        <div className="h-1 w-full rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-deck-elevated)' }}>
          <div
            className={`h-full rounded-full transition-all duration-700 ${running > 0 ? 'progress-striped' : ''}`}
            style={{
              width: `${progressPercent}%`,
              backgroundColor: progressPercent === 100 ? 'var(--color-verified)' : 'var(--color-amber-primary)',
            }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-[10px]" style={{ color: 'var(--color-text-dim)' }}>
            {completed} of {total} steps verified
          </span>
          {running > 0 && (
            <span className="text-[10px] animate-sovereign-pulse" style={{ color: 'var(--color-running)' }}>
              {running} running
            </span>
          )}
        </div>
      </div>

      {/* USER REQUEST marker */}
      <div className="mb-2">
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-semibold tracking-wider"
          style={{
            backgroundColor: 'var(--color-info-muted)',
            border: '1px solid var(--color-info-border)',
            color: 'var(--color-info)',
          }}
        >
          USER REQUEST
        </span>
      </div>

      {/* Connector from request to first node */}
      <div className="flex flex-col items-center py-1">
        <div className="w-0.5 h-4 rounded-full" style={{ backgroundColor: 'var(--color-deck-border)' }} />
        <div
          className="w-0 h-0"
          style={{
            borderLeft: '4px solid transparent',
            borderRight: '4px solid transparent',
            borderTop: '5px solid var(--color-deck-border)',
          }}
        />
      </div>

      {/* Pipeline Nodes */}
      <div className="w-full max-w-md space-y-0">
        {steps.map((step, index) => (
          <div key={step.id} className="animate-slide-up" style={{ animationDelay: `${index * 50}ms` }}>
            <PipelineNode step={step} isLast={index === steps.length - 1} />
          </div>
        ))}
      </div>

      {/* OUTPUT marker */}
      <div className="flex flex-col items-center mt-1">
        <div className="flex flex-col items-center py-1">
          <div
            className="w-0.5 h-4 rounded-full"
            style={{
              backgroundColor: completed === total ? 'var(--color-verified-border)' : 'var(--color-deck-border)',
            }}
          />
          <div
            className="w-0 h-0"
            style={{
              borderLeft: '4px solid transparent',
              borderRight: '4px solid transparent',
              borderTop: `5px solid ${completed === total ? 'var(--color-verified-border)' : 'var(--color-deck-border)'}`,
            }}
          />
        </div>
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-semibold tracking-wider ${
            completed === total ? 'glow-green' : ''
          }`}
          style={{
            backgroundColor: completed === total ? 'var(--color-verified-muted)' : 'var(--color-deck-elevated)',
            border: `1px solid ${completed === total ? 'var(--color-verified-border)' : 'var(--color-deck-border)'}`,
            color: completed === total ? 'var(--color-verified)' : 'var(--color-text-dim)',
          }}
        >
          {completed === total ? '✓ OUTPUT READY' : 'OUTPUT'}
        </span>
      </div>
    </div>
  );
}
