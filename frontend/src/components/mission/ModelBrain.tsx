/**
 * ModelBrain — Model router visualization
 *
 * Shows the task analysis → model selection decision tree
 * with animated selection indicator.
 */

import { useState } from 'react';
import { useAppStore } from '@/store/appStore';
import { useAuth } from '@/features/auth/useAuth';
import { api } from '@/services/api';

export function ModelBrain() {
  const { routing, setModelLoaded, updateTelemetry, telemetry } = useAppStore();
  const { user } = useAuth();
  const [busyModelId, setBusyModelId] = useState<string | null>(null);

  const canManageModels = user?.role === 'admin' || user?.role === 'engineering';
  const models = routing.available_models;
  const selectedModel = routing.selected_model;

  const handleToggle = async (modelId: string, loaded: boolean) => {
    if (!canManageModels || busyModelId) return;
    setBusyModelId(modelId);
    try {
      if (loaded) {
        await api.unloadModel(modelId);
        setModelLoaded(modelId, false);
      } else {
        await api.loadModel(modelId);
        setModelLoaded(modelId, true);
      }
      const status = await api.getModelStatus();
      if (status) {
        updateTelemetry({
          vram_used_mb: status.vram_used_mb || telemetry.vram_used_mb,
          vram_total_mb: status.max_vram_mb || telemetry.vram_total_mb,
        });
      }
    } catch {
      setModelLoaded(modelId, !loaded);
    } finally {
      setBusyModelId(null);
    }
  };

  return (
    <div className="px-4 py-4">
      <h4 className="font-label mb-4" style={{ color: 'var(--color-amber-primary)' }}>MODEL BRAIN</h4>

      {/* Task Analysis */}
      <div className="flex flex-col items-center">
        <div
          className="px-4 py-2.5 rounded-lg text-center max-w-xs"
          style={{
            backgroundColor: 'var(--color-info-muted)',
            border: '1px solid var(--color-info-border)',
          }}
        >
          <span className="font-label block" style={{ fontSize: '9px', color: 'var(--color-info)' }}>
            TASK ANALYSIS
          </span>
          <span className="font-instrument-lg block mt-1" style={{ color: 'var(--color-text-primary)' }}>
            {routing.task_type}
          </span>
        </div>

        {/* Connector */}
        <div className="flex flex-col items-center py-2">
          <div className="w-0.5 h-6" style={{ backgroundColor: 'var(--color-deck-border)' }} />
          <div
            className="w-0 h-0"
            style={{
              borderLeft: '4px solid transparent',
              borderRight: '4px solid transparent',
              borderTop: '5px solid var(--color-deck-border)',
            }}
          />
        </div>

        {/* Router node */}
        <div
          className="px-6 py-2 rounded-lg text-center"
          style={{
            backgroundColor: 'var(--color-amber-muted)',
            border: '1px solid var(--color-amber-border)',
          }}
        >
          <span className="font-instrument-lg" style={{ color: 'var(--color-amber-primary)' }}>
            MODEL ROUTER
          </span>
        </div>

        {/* Branch lines */}
        <div className="flex items-start justify-center gap-0 mt-2 w-full max-w-sm">
          {models.map((model) => {
            const isSelected = model.name === selectedModel;

            return (
              <div key={model.id} className="flex flex-col items-center flex-1">
                {/* Vertical connector */}
                <div className="flex flex-col items-center">
                  <div
                    className="w-0.5 h-5"
                    style={{
                      backgroundColor: isSelected
                        ? 'var(--color-amber-border)'
                        : 'var(--color-deck-border)',
                    }}
                  />
                </div>

                {/* Model card */}
                <div
                  className={`px-2.5 py-2 rounded-lg text-center transition-all duration-500 w-full mx-1 flex flex-col justify-between ${
                    isSelected ? 'animate-node-verified' : ''
                  }`}
                  style={{
                    backgroundColor: isSelected ? 'var(--color-amber-muted)' : 'var(--color-deck-surface)',
                    border: `1px solid ${isSelected ? 'var(--color-amber-border)' : 'var(--color-deck-border)'}`,
                    boxShadow: isSelected ? '0 0 12px rgba(245, 158, 11, 0.15)' : 'none',
                    minHeight: '110px',
                  }}
                >
                  <div>
                    <span
                      className="font-instrument block font-semibold truncate"
                      style={{
                        color: isSelected ? 'var(--color-amber-primary)' : 'var(--color-text-primary)',
                        fontSize: '10px',
                      }}
                    >
                      {model.name}
                    </span>
                    <span
                      className="text-[9px] block mt-0.5 uppercase tracking-wider"
                      style={{ color: 'var(--color-text-dim)' }}
                    >
                      {model.role}
                    </span>

                    {/* Quantization badge */}
                    <div className="mt-1 flex items-center justify-center">
                      <span
                        className="text-[8px] px-1 py-0.2 rounded font-mono"
                        style={{
                          backgroundColor: 'rgba(245, 158, 11, 0.15)',
                          color: 'var(--color-amber-primary)',
                          border: '1px solid var(--color-amber-border)',
                        }}
                      >
                        {(model.quantization && model.quantization !== 'none' ? model.quantization : '4-BIT').toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {/* Status & Load/Unload Action */}
                  <div className="mt-2 pt-1 border-t" style={{ borderColor: 'var(--color-deck-border)' }}>
                    <button
                      onClick={() => handleToggle(model.id, model.loaded)}
                      disabled={!canManageModels || busyModelId === model.id}
                      className="w-full text-[9px] py-0.5 rounded font-medium border transition-colors cursor-pointer"
                      style={{
                        backgroundColor: !canManageModels
                          ? 'rgba(100, 116, 139, 0.1)'
                          : model.loaded
                          ? 'var(--color-error-muted)'
                          : 'var(--color-info-muted)',
                        borderColor: !canManageModels
                          ? 'rgba(100, 116, 139, 0.2)'
                          : model.loaded
                          ? 'var(--color-error-border)'
                          : 'var(--color-info-border)',
                        color: !canManageModels
                          ? 'var(--color-text-muted)'
                          : model.loaded
                          ? 'var(--color-error)'
                          : 'var(--color-info)',
                        opacity: (!canManageModels || busyModelId === model.id) ? 0.6 : 1,
                        cursor: (!canManageModels || busyModelId === model.id) ? 'not-allowed' : 'pointer',
                      }}
                      title={!canManageModels ? 'Requires Admin or Engineering role' : model.loaded ? 'Unload from VRAM' : 'Load into VRAM'}
                    >
                      {busyModelId === model.id ? '...' : model.loaded ? 'Unload' : 'Load'}
                    </button>

                    {isSelected && (
                      <div className="mt-1 flex items-center justify-center gap-1">
                        <span
                          className="w-1 h-1 rounded-full animate-sovereign-pulse"
                          style={{ backgroundColor: 'var(--color-amber-primary)' }}
                        />
                        <span className="text-[8px] font-bold tracking-widest" style={{ color: 'var(--color-amber-primary)' }}>
                          ROUTED
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Routing reason */}
        <div
          className="mt-4 px-4 py-2.5 rounded-lg max-w-sm w-full"
          style={{
            backgroundColor: 'var(--color-deck-surface)',
            border: '1px solid var(--color-deck-border)',
          }}
        >
          <span className="font-label block" style={{ fontSize: '9px' }}>REASON</span>
          <p className="text-[11px] mt-1 leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
            {routing.reason}
          </p>
        </div>
      </div>
    </div>
  );
}
