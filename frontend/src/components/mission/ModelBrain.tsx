/**
 * ModelBrain — Model router visualization
 *
 * Shows the task analysis → model selection decision tree
 * with animated selection indicator.
 */

import { useAppStore } from '@/store/appStore';

export function ModelBrain() {
  const { routing, updateRouting } = useAppStore();

  const models = routing.available_models;
  const selectedModel = routing.selected_model;

  return (
    <div className="px-4 py-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-label" style={{ color: 'var(--color-amber-primary)' }}>NEURAL MODEL ROUTER</h4>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
          SELECTABLE NODES
        </span>
      </div>

      {/* Task Analysis */}
      <div className="flex flex-col items-center">
        <div
          className="px-4 py-2.5 rounded-lg text-center max-w-xs w-full shadow-lg"
          style={{
            backgroundColor: 'var(--color-info-muted)',
            border: '1px solid var(--color-info-border)',
          }}
        >
          <span className="font-label block" style={{ fontSize: '9px', color: 'var(--color-info)' }}>
            TASK ANALYSIS
          </span>
          <span className="font-instrument-lg block mt-1 text-cyan-200">
            {routing.task_type}
          </span>
        </div>

        {/* Connector */}
        <div className="flex flex-col items-center py-2">
          <div className="w-0.5 h-6 bg-gradient-to-b from-cyan-500/40 to-amber-500/40" />
          <div
            className="w-0 h-0"
            style={{
              borderLeft: '4px solid transparent',
              borderRight: '4px solid transparent',
              borderTop: '5px solid var(--color-amber-border)',
            }}
          />
        </div>

        {/* Router node */}
        <div
          className="px-6 py-2 rounded-lg text-center shadow-lg"
          style={{
            backgroundColor: 'var(--color-amber-muted)',
            border: '1px solid var(--color-amber-border)',
          }}
        >
          <span className="font-instrument-lg tracking-wider" style={{ color: 'var(--color-amber-primary)' }}>
            SOVEREIGN ROUTING ARBITER
          </span>
        </div>

        {/* Branch lines */}
        <div className="flex items-start justify-center gap-2 mt-2 w-full max-w-md">
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

                {/* Model card button */}
                <button
                  type="button"
                  onClick={() => {
                    updateRouting({
                      selected_model: model.name,
                      task_type: model.role,
                      reason: `Manually routed to ${model.name} (${model.role}) for sovereign execution`,
                    });
                  }}
                  className={`px-2.5 py-2.5 rounded-lg text-center transition-all duration-300 w-full cursor-pointer transform hover:-translate-y-1 active:scale-95 ${
                    isSelected ? 'ring-2 ring-amber-400/60 shadow-[0_0_20px_rgba(245,158,11,0.25)]' : 'hover:border-cyan-500/40 hover:bg-slate-800/60'
                  }`}
                  style={{
                    backgroundColor: isSelected ? 'var(--color-amber-muted)' : 'var(--color-deck-surface)',
                    border: `1px solid ${isSelected ? 'var(--color-amber-border)' : 'var(--color-deck-border)'}`,
                  }}
                >
                  <span
                    className="font-instrument block font-bold truncate"
                    style={{
                      color: isSelected ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
                      fontSize: '11px',
                    }}
                  >
                    {model.name}
                  </span>
                  <span
                    className="text-[9px] block mt-0.5 uppercase tracking-wider font-mono text-cyan-300/80 truncate"
                  >
                    {model.role}
                  </span>
                  <div className="mt-1 text-[9px] text-slate-400 font-mono">
                    {model.name.includes('14B') ? '14B • 4-bit' : model.name.includes('7B') ? '7B • 4-bit' : '8B • 4-bit'}
                  </div>
                  {isSelected ? (
                    <div className="mt-1.5 flex items-center justify-center gap-1 py-0.5 px-1 rounded-full bg-amber-500/20 border border-amber-500/40">
                      <span
                        className="w-1.5 h-1.5 rounded-full animate-sovereign-pulse"
                        style={{ backgroundColor: 'var(--color-amber-primary)' }}
                      />
                      <span className="text-[8px] font-bold tracking-widest text-amber-300">
                        ROUTED
                      </span>
                    </div>
                  ) : (
                    <div className="mt-1.5 text-[8px] font-mono tracking-wider text-slate-500">
                      SWITCH
                    </div>
                  )}
                </button>
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
