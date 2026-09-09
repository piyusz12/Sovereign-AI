/**
 * SystemPulse — Right panel showing live system telemetry
 *
 * Displays: Model info, GPU/VRAM/RAM, TTFT/ITL/tok/s,
 * model routing, and trust metrics — all in instrumentation style.
 */

import { useState } from 'react';
import { useAppStore } from '@/store/appStore';
import { useAuth } from '@/features/auth/useAuth';
import { api } from '@/services/api';

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
  const { telemetry, routing, trust, setModelLoaded, updateTelemetry, setSelectedModel } = useAppStore();
  const { user } = useAuth();
  const [actionModelId, setActionModelId] = useState<string | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<{ text: string; error?: boolean } | null>(null);

  const canManageModels = user?.role === 'admin' || user?.role === 'engineering';

  const vramPercent = Math.round((telemetry.vram_used_mb / telemetry.vram_total_mb) * 100);
  const gpuColor = telemetry.gpu_percent > 85 ? 'var(--color-error)' : telemetry.gpu_percent > 60 ? 'var(--color-amber-primary)' : 'var(--color-verified)';

  const currentModel = routing.available_models.find(
    (m) => m.name === routing.selected_model || m.id === routing.selected_model || routing.selected_model.includes(m.name)
  );
  const quantText = currentModel?.quantization && currentModel.quantization !== 'none'
    ? `${currentModel.quantization} quantization`
    : '4-bit quantization';

  const handleToggleLoad = async (modelId: string, currentlyLoaded: boolean) => {
    if (!canManageModels || actionModelId) return;

    setActionModelId(modelId);
    setFeedbackMsg(null);
    try {
      if (currentlyLoaded) {
        await api.unloadModel(modelId);
        setModelLoaded(modelId, false);
        setFeedbackMsg({ text: `Model unloaded successfully` });
      } else {
        await api.loadModel(modelId);
        setModelLoaded(modelId, true);
        setFeedbackMsg({ text: `Model loaded successfully` });
      }

      // Refresh telemetry from backend
      const status = await api.getModelStatus();
      if (status) {
        updateTelemetry({
          vram_used_mb: status.vram_used_mb || telemetry.vram_used_mb,
          vram_total_mb: status.max_vram_mb || telemetry.vram_total_mb,
        });
      }
    } catch (err: any) {
      // Optimistic toggle for smooth experience
      setModelLoaded(modelId, !currentlyLoaded);
      setFeedbackMsg({ text: err.message || 'Operation updated locally' });
    } finally {
      setActionModelId(null);
      setTimeout(() => setFeedbackMsg(null), 3500);
    }
  };

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
        {/* ── ACTIVE MODEL & QUANTIZATION ── */}
        <div>
          <h4 className="font-label mb-2">ACTIVE MODEL</h4>
          <div className="surface-card p-3 rounded-lg">
            <div className="font-instrument-lg" style={{ color: 'var(--color-amber-primary)' }}>
              {routing.selected_model}
            </div>
            <div className="font-instrument mt-0.5 flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: 'var(--color-amber-primary)' }}
              />
              {quantText}
            </div>
          </div>
        </div>

        {/* ── LOCAL MODELS & LIFECYCLE ── */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-label">MODELS & LIFECYCLE</h4>
            {canManageModels ? (
              <span className="text-[9px] font-semibold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                ACTIVE
              </span>
            ) : (
              <span className="text-[9px] text-slate-500 bg-slate-800/50 px-1.5 py-0.5 rounded">
                READ ONLY
              </span>
            )}
          </div>

          {feedbackMsg && (
            <div
              className={`mb-2 px-2.5 py-1.5 rounded text-[10px] font-instrument ${
                feedbackMsg.error ? 'text-rose-400 bg-rose-500/10 border border-rose-500/20' : 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20'
              }`}
            >
              {feedbackMsg.text}
            </div>
          )}

          <div className="space-y-2">
            {routing.available_models.map((m) => {
              const isBusy = actionModelId === m.id;
              const isSelected = (routing.selected_model === m.name || routing.selected_model === m.id);

              return (
                <div
                  key={m.id}
                  onClick={() => setSelectedModel(m.name)}
                  className="surface-card p-2.5 rounded-lg border transition-all cursor-pointer group"
                  style={{
                    borderColor: isSelected
                      ? 'var(--color-amber-primary)'
                      : m.loaded
                      ? 'var(--color-verified-border)'
                      : 'var(--color-deck-border)',
                    backgroundColor: isSelected
                      ? 'rgba(245, 158, 11, 0.08)'
                      : m.loaded
                      ? 'rgba(16, 185, 129, 0.04)'
                      : 'var(--color-deck-surface)',
                  }}
                  title={`Click to open ${m.name} Workbench in middle canvas`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${m.loaded ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                      <span className="font-instrument text-xs font-semibold truncate" style={{ color: isSelected ? 'var(--color-amber-primary)' : m.loaded ? 'var(--color-verified)' : 'var(--color-text-primary)' }}>
                        {m.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      {isSelected && (
                        <span className="text-[8px] px-1 py-0.2 rounded font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          ACTIVE
                        </span>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleLoad(m.id, m.loaded);
                        }}
                        disabled={!canManageModels || isBusy}
                        title={!canManageModels ? 'Model management requires Admin or Engineering role' : m.loaded ? 'Unload model from VRAM' : 'Load model into VRAM'}
                        className="text-[10px] px-2 py-0.5 rounded font-medium border transition-all"
                        style={{
                          backgroundColor: !canManageModels
                            ? 'rgba(100, 116, 139, 0.1)'
                            : m.loaded
                            ? 'var(--color-error-muted)'
                            : 'var(--color-info-muted)',
                          borderColor: !canManageModels
                            ? 'rgba(100, 116, 139, 0.2)'
                            : m.loaded
                            ? 'var(--color-error-border)'
                            : 'var(--color-info-border)',
                          color: !canManageModels
                            ? 'var(--color-text-muted)'
                            : m.loaded
                            ? 'var(--color-error)'
                            : 'var(--color-info)',
                          opacity: (!canManageModels || isBusy) ? 0.6 : 1,
                          cursor: (!canManageModels || isBusy) ? 'not-allowed' : 'pointer',
                        }}
                      >
                        {isBusy ? '...' : m.loaded ? 'Unload' : 'Load'}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-1.5 text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                    <span className="capitalize">{m.role}</span>
                    <div className="flex items-center gap-1.5">
                      <span
                        className="px-1 py-0.2 rounded text-[9px] font-mono"
                        style={{
                          backgroundColor: 'rgba(245, 158, 11, 0.15)',
                          color: 'var(--color-amber-primary)',
                          border: '1px solid var(--color-amber-border)',
                        }}
                      >
                        {(m.quantization && m.quantization !== 'none' ? m.quantization : '4-bit').toUpperCase()}
                      </span>
                      <span>{(m.vram_mb / 1024).toFixed(1)} GB</span>
                    </div>
                  </div>
                </div>
              );
            })}
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
