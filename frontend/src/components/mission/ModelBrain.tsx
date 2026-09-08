/**
 * ModelBrain — Model router visualization
 *
 * Shows the task analysis → model selection decision tree
 * with animated selection indicator.
 */

import { useAppStore } from '@/store/appStore';

export function ModelBrain() {
  const { routing } = useAppStore();

  const models = routing.available_models;
  const selectedModel = routing.selected_model;

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
          {models.map((model, idx) => {
            const isSelected = model.name === selectedModel;
            const isCenter = idx === Math.floor(models.length / 2);

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
                  className={`px-3 py-2.5 rounded-lg text-center transition-all duration-500 w-full mx-1 ${
                    isSelected ? 'animate-node-verified' : ''
                  }`}
                  style={{
                    backgroundColor: isSelected ? 'var(--color-amber-muted)' : 'var(--color-deck-surface)',
                    border: `1px solid ${isSelected ? 'var(--color-amber-border)' : 'var(--color-deck-border)'}`,
                    boxShadow: isSelected ? '0 0 12px rgba(245, 158, 11, 0.15)' : 'none',
                  }}
                >
                  <span
                    className="font-instrument block"
                    style={{
                      color: isSelected ? 'var(--color-amber-primary)' : 'var(--color-text-muted)',
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
                  {isSelected && (
                    <div className="mt-1.5 flex items-center justify-center gap-1">
                      <span
                        className="w-1.5 h-1.5 rounded-full animate-sovereign-pulse"
                        style={{ backgroundColor: 'var(--color-amber-primary)' }}
                      />
                      <span className="text-[9px] font-bold tracking-widest" style={{ color: 'var(--color-amber-primary)' }}>
                        SELECTED
                      </span>
                    </div>
                  )}
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
