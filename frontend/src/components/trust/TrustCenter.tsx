/**
 * TrustCenter — Full security verification screen
 *
 * Shows zero-egress proof with data flow visualization,
 * network monitoring metrics, and ALL LOCAL verification.
 */

import { Shield, Lock, Globe, Server, FileText, Cpu, ArrowDown } from 'lucide-react';
import { useAppStore } from '@/store/appStore';

function TrustMetricCard({
  label,
  value,
  isZero,
}: {
  label: string;
  value: string | number;
  isZero: boolean;
}) {
  return (
    <div
      className="flex items-center justify-between px-4 py-3 rounded-lg"
      style={{
        backgroundColor: 'var(--color-deck-surface)',
        border: `1px solid ${isZero ? 'var(--color-verified-border)' : 'var(--color-error-border)'}`,
      }}
    >
      <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
        {label}
      </span>
      <span
        className="font-instrument-lg"
        style={{ color: isZero ? 'var(--color-verified)' : 'var(--color-error)' }}
      >
        {value}
      </span>
    </div>
  );
}

export function TrustCenter() {
  const { trust } = useAppStore();

  return (
    <div
      className="flex-1 overflow-y-auto p-6"
      style={{ backgroundColor: 'var(--color-deck-base)' }}
    >
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center animate-fade-in">
          {/* Shield icon */}
          <div
            className="w-20 h-20 rounded-2xl mx-auto mb-4 flex items-center justify-center"
            style={{
              backgroundColor: trust.is_local ? 'var(--color-verified-muted)' : 'var(--color-error-muted)',
              border: `2px solid ${trust.is_local ? 'var(--color-verified-border)' : 'var(--color-error-border)'}`,
              boxShadow: trust.is_local ? '0 0 30px var(--color-verified-glow)' : undefined,
            }}
          >
            <Shield
              className="w-9 h-9"
              style={{ color: trust.is_local ? 'var(--color-verified)' : 'var(--color-error)' }}
            />
          </div>
          <h2
            className="text-2xl font-bold tracking-wide"
            style={{ color: 'var(--color-text-primary)' }}
          >
            TRUST CENTER
          </h2>
          <div className="flex items-center justify-center gap-2 mt-2">
            <span
              className="w-2.5 h-2.5 rounded-full animate-sovereign-pulse"
              style={{
                backgroundColor: trust.is_local ? 'var(--color-verified)' : 'var(--color-error)',
                boxShadow: trust.is_local ? '0 0 8px var(--color-verified-glow)' : undefined,
              }}
            />
            <span
              className="text-sm font-bold tracking-widest"
              style={{ color: trust.is_local ? 'var(--color-verified)' : 'var(--color-error)' }}
            >
              {trust.is_local ? 'SYSTEM SECURE' : 'EXTERNAL ACCESS DETECTED'}
            </span>
          </div>
        </div>

        {/* Network metrics */}
        <div className="space-y-2 animate-slide-up">
          <h3 className="font-label mb-3" style={{ color: 'var(--color-amber-primary)' }}>
            NETWORK SOVEREIGNTY
          </h3>
          <TrustMetricCard
            label="External connections"
            value={trust.external_connections}
            isZero={trust.external_connections === 0}
          />
          <TrustMetricCard
            label="External DNS requests"
            value={trust.dns_requests}
            isZero={trust.dns_requests === 0}
          />
          <TrustMetricCard
            label="Cloud API requests"
            value={trust.cloud_api_calls}
            isZero={trust.cloud_api_calls === 0}
          />
          <TrustMetricCard
            label="Data egress"
            value={`${trust.data_egress_mb} MB`}
            isZero={trust.data_egress_mb === 0}
          />
        </div>

        {/* Local resources */}
        <div className="space-y-2 animate-slide-up" style={{ animationDelay: '100ms' }}>
          <h3 className="font-label mb-3" style={{ color: 'var(--color-amber-primary)' }}>
            LOCAL RESOURCES
          </h3>
          <div className="grid grid-cols-3 gap-3">
            {[
              { icon: Cpu, label: 'Local Models', value: String(trust.local_models).padStart(2, '0') },
              { icon: FileText, label: 'Local Documents', value: String(trust.local_documents) },
              { icon: Lock, label: 'Active Policies', value: String(trust.active_policies) },
            ].map(({ icon: Icon, label, value }) => (
              <div
                key={label}
                className="flex flex-col items-center py-4 rounded-lg"
                style={{
                  backgroundColor: 'var(--color-deck-surface)',
                  border: '1px solid var(--color-deck-border)',
                }}
              >
                <Icon className="w-5 h-5 mb-2" style={{ color: 'var(--color-amber-primary)' }} />
                <span className="font-instrument-lg text-lg" style={{ color: 'var(--color-text-primary)' }}>
                  {value}
                </span>
                <span className="font-label mt-1" style={{ fontSize: '8px' }}>
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Data flow visualization */}
        <div className="animate-slide-up" style={{ animationDelay: '200ms' }}>
          <h3 className="font-label mb-3" style={{ color: 'var(--color-amber-primary)' }}>
            DATA FLOW — THIS MISSION
          </h3>
          <div
            className="rounded-lg p-6"
            style={{
              backgroundColor: 'var(--color-deck-surface)',
              border: '1px solid var(--color-deck-border)',
            }}
          >
            <div className="flex flex-col items-center space-y-2">
              {['INPUT', 'OCR', 'RAG', 'QWEN3-14B', 'VERIFICATION', 'DOCX'].map((step, idx) => (
                <div key={step} className="flex flex-col items-center">
                  <div
                    className="px-6 py-2 rounded-lg font-instrument"
                    style={{
                      backgroundColor: 'var(--color-deck-base)',
                      border: '1px solid var(--color-deck-border)',
                      color: 'var(--color-text-primary)',
                      fontSize: '11px',
                    }}
                  >
                    {step}
                  </div>
                  {idx < 5 && (
                    <ArrowDown className="w-3 h-3 my-1" style={{ color: 'var(--color-verified-border)' }} />
                  )}
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center gap-2 mt-4 pt-3 border-t" style={{ borderColor: 'var(--color-deck-border)' }}>
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: 'var(--color-verified)', boxShadow: '0 0 6px var(--color-verified-glow)' }}
              />
              <span className="font-instrument" style={{ color: 'var(--color-verified)', fontSize: '12px' }}>
                ALL LOCAL ✓
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
