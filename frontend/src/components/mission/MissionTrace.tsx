/**
 * MissionTrace — Visual agent trace (not logs)
 *
 * Shows timestamped execution events with expandable details.
 * Click any step to see technical internals.
 */

import { useState } from 'react';
import { ChevronRight, ChevronDown } from 'lucide-react';
import type { TraceEntry } from '@/store/missionStore';

interface MissionTraceProps {
  trace: TraceEntry[];
  baseTime?: number;
}

export function MissionTrace({ trace }: MissionTraceProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (!trace || trace.length === 0) {
    return (
      <div className="py-8 text-center">
        <span className="font-instrument" style={{ color: 'var(--color-text-dim)' }}>
          No trace data available
        </span>
      </div>
    );
  }

  const formatOffset = (ms: number): string => {
    const secs = ms / 1000;
    if (secs < 1) return `00:00.${String(Math.round(ms)).padStart(3, '0')}`;
    const minutes = Math.floor(secs / 60);
    const remainingSecs = secs - minutes * 60;
    return `${String(minutes).padStart(2, '0')}:${remainingSecs.toFixed(3).padStart(6, '0')}`;
  };

  return (
    <div className="space-y-0">
      <div className="px-4 py-2 mb-2">
        <h4 className="font-label" style={{ color: 'var(--color-amber-primary)' }}>MISSION TRACE</h4>
      </div>
      {trace.map((entry, idx) => {
        const isExpanded = expandedIdx === idx;
        const isLast = idx === trace.length - 1;

        return (
          <div key={idx}>
            <button
              className="w-full flex items-start gap-3 px-4 py-2 transition-colors text-left hover:bg-[var(--color-deck-surface)]"
              onClick={() => setExpandedIdx(isExpanded ? null : idx)}
            >
              {/* Timeline dot */}
              <div className="flex flex-col items-center mt-1 flex-shrink-0">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor: isLast
                      ? 'var(--color-verified)'
                      : idx === trace.length - 1
                        ? 'var(--color-running)'
                        : 'var(--color-text-muted)',
                  }}
                />
              </div>

              {/* Timestamp */}
              <span
                className="font-instrument flex-shrink-0 w-24 tabular-nums"
                style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}
              >
                {formatOffset(entry.offset_ms)}
              </span>

              {/* Event name */}
              <span className="flex-1 text-xs" style={{ color: 'var(--color-text-primary)' }}>
                {entry.event}
              </span>

              {/* Expand icon */}
              {entry.detail && (
                isExpanded
                  ? <ChevronDown className="w-3 h-3 flex-shrink-0 mt-0.5" style={{ color: 'var(--color-text-dim)' }} />
                  : <ChevronRight className="w-3 h-3 flex-shrink-0 mt-0.5" style={{ color: 'var(--color-text-dim)' }} />
              )}
            </button>

            {/* Detail expansion */}
            {isExpanded && entry.detail && (
              <div className="ml-14 mr-4 mb-2 px-3 py-2 rounded-md" style={{ backgroundColor: 'var(--color-deck-surface)', border: '1px solid var(--color-deck-border)' }}>
                <span className="text-[11px]" style={{ color: 'var(--color-text-secondary)' }}>
                  {entry.detail}
                </span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
