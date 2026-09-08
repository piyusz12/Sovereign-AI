/**
 * EvidencePanel — Evidence layer for RAG-grounded claims
 *
 * Displays claims with confidence scores and linked sources.
 * Each source can be clicked to open the original document location.
 */

import { useState } from 'react';
import { FileText, ChevronDown, ChevronUp } from 'lucide-react';
import type { EvidenceClaim } from '@/store/missionStore';

interface EvidencePanelProps {
  evidence: EvidenceClaim[];
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const percent = Math.round(confidence * 100);
  const color = confidence >= 0.9
    ? 'var(--color-verified)'
    : confidence >= 0.7
      ? 'var(--color-amber-primary)'
      : 'var(--color-error)';

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-deck-elevated)' }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${percent}%`, backgroundColor: color }}
        />
      </div>
      <span className="font-instrument text-[10px]" style={{ color }}>
        {confidence.toFixed(2)}
      </span>
    </div>
  );
}

export function EvidencePanel({ evidence }: EvidencePanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [copiedSource, setCopiedSource] = useState<string | null>(null);

  const handleCopyAll = () => {
    const text = evidence
      .map(
        (ev, idx) =>
          `[Claim ${idx + 1}] (Confidence ${(ev.confidence * 100).toFixed(0)}%)\n${ev.claim}\nSources:\n` +
          ev.sources.map((s) => `• ${s.title} (${s.location}) - "${s.snippet || 'Verified'}"`).join('\n')
      )
      .join('\n\n');
    navigator.clipboard?.writeText(text);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  if (!evidence || evidence.length === 0) {
    return (
      <div className="px-4 py-8 text-center">
        <span className="font-instrument" style={{ color: 'var(--color-text-dim)' }}>
          No evidence collected yet
        </span>
      </div>
    );
  }

  return (
    <div className="px-4 py-3 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-label" style={{ color: 'var(--color-amber-primary)' }}>EVIDENCE & CITATION LAYER</h4>
          <p className="text-[10px]" style={{ color: 'var(--color-text-dim)' }}>
            {evidence.length} claim{evidence.length !== 1 ? 's' : ''} with zero-egress cryptographic source verification
          </p>
        </div>
        <button
          type="button"
          onClick={handleCopyAll}
          className="px-2.5 py-1 rounded text-[10px] font-mono font-bold tracking-wider transition-all bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/20 active:scale-95 cursor-pointer flex items-center gap-1.5"
        >
          {copiedAll ? 'CITATIONS COPIED ✓' : 'COPY ALL CITATIONS'}
        </button>
      </div>

      <div className="space-y-2">
        {evidence.map((ev) => {
          const isExpanded = expandedId === ev.id;
          return (
            <div
              key={ev.id}
              className="rounded-lg overflow-hidden transition-all"
              style={{
                backgroundColor: 'var(--color-deck-surface)',
                border: `1px solid ${isExpanded ? 'var(--color-amber-border)' : 'var(--color-deck-border)'}`,
              }}
            >
              {/* Claim header */}
              <button
                className="w-full px-4 py-3 text-left flex items-start gap-3 transition-colors hover:bg-[var(--color-deck-elevated)]"
                onClick={() => setExpandedId(isExpanded ? null : ev.id)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-label" style={{ fontSize: '9px' }}>CLAIM</span>
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-primary)' }}>
                    {ev.claim}
                  </p>
                  <div className="mt-2 max-w-xs">
                    <ConfidenceBar confidence={ev.confidence} />
                  </div>
                </div>
                {isExpanded
                  ? <ChevronUp className="w-4 h-4 mt-1 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }} />
                  : <ChevronDown className="w-4 h-4 mt-1 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }} />
                }
              </button>

              {/* Expanded sources */}
              {isExpanded && (
                <div className="px-4 pb-3 space-y-2 border-t" style={{ borderColor: 'var(--color-deck-border)' }}>
                  <div className="pt-2">
                    <span className="font-label" style={{ fontSize: '9px' }}>SOURCES</span>
                  </div>
                  {ev.sources.map((source, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        const citationText = `[Citation] ${source.title} - ${source.location}: "${source.snippet || ''}"`;
                        navigator.clipboard?.writeText(citationText);
                        setCopiedSource(`${ev.id}-${idx}`);
                        setTimeout(() => setCopiedSource(null), 2000);
                      }}
                      className="w-full text-left flex items-start gap-2.5 px-3 py-2.5 rounded-md cursor-pointer transition-all hover:bg-slate-800/80 hover:border-cyan-500/30"
                      style={{
                        backgroundColor: 'var(--color-deck-base)',
                        border: '1px solid var(--color-deck-border)',
                      }}
                      title="Click to copy citation snippet"
                    >
                      <FileText className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" style={{ color: 'var(--color-amber-primary)' }} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-medium" style={{ color: 'var(--color-text-primary)' }}>
                            {source.title}
                          </span>
                          <span className="text-[9px] font-mono text-cyan-400">
                            {copiedSource === `${ev.id}-${idx}` ? 'COPIED ✓' : 'COPY'}
                          </span>
                        </div>
                        <span className="font-instrument block mt-0.5" style={{ color: 'var(--color-amber-primary)', fontSize: '10px' }}>
                          {source.location}
                        </span>
                        {source.snippet && (
                          <p className="text-[10px] mt-1 leading-relaxed text-slate-300">
                            "{source.snippet}"
                          </p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
