/**
 * SystemPulse — Right panel showing live system telemetry
 *
 * Displays: Model info, GPU/VRAM/RAM, TTFT/ITL/tok/s,
 * model routing, and trust metrics — all in instrumentation style.
 */

import { useAppStore } from '@/store/appStore';
import { useMissionStore } from '@/store/missionStore';

function TelemetryRow({ label, value, unit, color }: { label: string; value: string | number; unit?: string; color?: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="font-label" style={{ fontSize: '9px' }}>{label}</span>
      <span className="font-instrument-lg" style={{ color: color || 'var(--color-text-primary)' }}>
        {value}
        {unit && <span className="ml-0.5 text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{unit}</span>}
      </span>
    </div>
  );
}

function ProgressBar({ value, max, color }: { value: number; max: number; color: string }) {
  const percent = Math.min(Math.round((value / max) * 100), 100);
  return (
    <div className="h-1.5 w-full rounded-full overflow-hidden mt-1" style={{ backgroundColor: 'var(--color-deck-elevated)' }}>
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${percent}%`, backgroundColor: color }}
      />
    </div>
  );
}

export function SystemPulse() {
  const { telemetry, routing, trust } = useAppStore();
  const activeMission = useMissionStore((s) => s.getActiveMission());

  const vramPercent = Math.round((telemetry.vram_used_mb / telemetry.vram_total_mb) * 100);
  const gpuColor = telemetry.gpu_percent > 85 ? 'var(--color-error)' : telemetry.gpu_percent > 60 ? 'var(--color-amber-primary)' : 'var(--color-verified)';

  return (
    <aside
      className="w-64 flex-shrink-0 flex flex-col border-l overflow-y-auto select-none"
      style={{
        backgroundColor: 'var(--color-deck-deep)',
        borderColor: 'var(--color-deck-border)',
      }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--color-deck-border)' }}>
        <div className="flex items-center gap-2">
          <span
            className="w-1.5 h-1.5 rounded-full animate-sovereign-pulse"
            style={{ backgroundColor: 'var(--color-verified)' }}
          />
          <span className="font-label" style={{ color: 'var(--color-amber-primary)', fontSize: '10px', letterSpacing: '0.15em' }}>
            SYSTEM PULSE
          </span>
        </div>
      </div>

      <div className="flex-1 px-4 py-3 space-y-5">
        {/* ── MODEL ── */}
        <div>
          <h4 className="font-label mb-2">MODEL</h4>
          <div className="surface-card p-3 rounded-lg">
            <div className="font-instrument-lg" style={{ color: 'var(--color-amber-primary)' }}>
              {routing.selected_model}
            </div>
            <div className="font-instrument mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
              4-bit quantization
            </div>
          </div>
        </div>

        {/* ── GPU ── */}
        <div>
          <h4 className="font-label mb-2">GPU</h4>
          <TelemetryRow label="UTILIZATION" value={telemetry.gpu_percent} unit="%" color={gpuColor} />
          <ProgressBar value={telemetry.gpu_percent} max={100} color={gpuColor} />

          <div className="mt-2">
            <TelemetryRow
              label="VRAM"
              value={`${(telemetry.vram_used_mb / 1024).toFixed(1)} / ${(telemetry.vram_total_mb / 1024).toFixed(1)}`}
              unit="GB"
              color={vramPercent > 85 ? 'var(--color-error)' : 'var(--color-text-primary)'}
            />
            <ProgressBar
              value={telemetry.vram_used_mb}
              max={telemetry.vram_total_mb}
              color={vramPercent > 85 ? 'var(--color-error)' : vramPercent > 70 ? 'var(--color-amber-primary)' : 'var(--color-verified)'}
            />
          </div>

          <div className="mt-2">
            <TelemetryRow
              label="RAM"
              value={`${(telemetry.ram_used_mb / 1024).toFixed(1)} / ${(telemetry.ram_total_mb / 1024).toFixed(1)}`}
              unit="GB"
            />
            <ProgressBar value={telemetry.ram_used_mb} max={telemetry.ram_total_mb} color="var(--color-info)" />
          </div>
        </div>

        {/* ── INFERENCE ── */}
        <div>
          <h4 className="font-label mb-2">INFERENCE</h4>
          <TelemetryRow label="TTFT" value={telemetry.ttft_ms} unit="ms" color="var(--color-amber-primary)" />
          <TelemetryRow label="ITL" value={telemetry.itl_ms} unit="ms" />
          <TelemetryRow label="TOKENS" value={telemetry.tokens_per_sec} unit="tok/s" color="var(--color-verified)" />
          <div className="mt-1">
            <TelemetryRow
              label="CONTEXT"
              value={`${(telemetry.context_used / 1024).toFixed(1)}K / ${(telemetry.context_max / 1024).toFixed(0)}K`}
            />
            <ProgressBar value={telemetry.context_used} max={telemetry.context_max} color="var(--color-info)" />
          </div>
        </div>

        {/* ── ROUTING ── */}
        <div>
          <h4 className="font-label mb-2">ROUTING</h4>
          <div className="surface-card p-3 rounded-lg space-y-2">
            <div className="flex justify-between">
              <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Task</span>
              <span className="font-instrument" style={{ color: 'var(--color-text-primary)' }}>
                {routing.task_type}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Selected</span>
              <span className="font-instrument" style={{ color: 'var(--color-amber-primary)' }}>
                {routing.selected_model}
              </span>
            </div>
            <div className="pt-1 border-t" style={{ borderColor: 'var(--color-deck-border)' }}>
              <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Reason</span>
              <p className="text-[11px] mt-0.5" style={{ color: 'var(--color-text-secondary)' }}>
                {routing.reason}
              </p>
            </div>
          </div>
        </div>

        {/* ── TRUST ── */}
        <div>
          <h4 className="font-label mb-2">TRUST</h4>
          <div className="surface-card p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <span
                className="w-2 h-2 rounded-full"
                style={{
                  backgroundColor: trust.is_local ? 'var(--color-verified)' : 'var(--color-error)',
                  boxShadow: trust.is_local ? '0 0 6px var(--color-verified-glow)' : undefined,
                }}
              />
              <span className="font-instrument" style={{ color: trust.is_local ? 'var(--color-verified)' : 'var(--color-error)' }}>
                {trust.is_local ? 'LOCAL' : 'ONLINE'}
              </span>
            </div>
            <div className="space-y-0.5">
              <TelemetryRow label="EGRESS" value={`${trust.data_egress_mb}`} unit="MB" color={trust.data_egress_mb === 0 ? 'var(--color-verified)' : 'var(--color-error)'} />
              <TelemetryRow label="DNS" value={trust.dns_requests} color={trust.dns_requests === 0 ? 'var(--color-verified)' : 'var(--color-error)'} />
              <TelemetryRow label="CLOUD API" value={trust.cloud_api_calls} color={trust.cloud_api_calls === 0 ? 'var(--color-verified)' : 'var(--color-error)'} />
              <TelemetryRow label="EXT CONN" value={trust.external_connections} color={trust.external_connections === 0 ? 'var(--color-verified)' : 'var(--color-error)'} />
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
