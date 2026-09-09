import { useRef, useState } from 'react';
import { Brain, Code2, Eye, ImagePlus, Loader2, Play, Send, Sparkles } from 'lucide-react';
import { api } from '@/services/api';

type PanelState = { input: string; output: string; busy: boolean; error: string };
const initialPanelState: PanelState = { input: '', output: '', busy: false, error: '' };

export function ModelWorkspaces({ activePanel }: { activePanel?: 'reasoning' | 'coding' | 'vision' }) {
  const [reasoning, setReasoning] = useState<PanelState>({ ...initialPanelState, input: 'Summarize the current system health and suggest the next diagnostic step.' });
  const [coding, setCoding] = useState<PanelState>({ ...initialPanelState, input: 'Write a Python function that validates an equipment tag format.' });
  const [vision, setVision] = useState<PanelState>({ ...initialPanelState, input: 'Inspect this image. Extract visible labels and flag anomalies.' });
  const [image, setImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const showAll = !activePanel;

  const runReasoning = async () => {
    if (!reasoning.input.trim() || reasoning.busy) return;
    setReasoning((state) => ({ ...state, busy: true, error: '' }));
    try {
      const result = await api.chat(reasoning.input, 'Qwen3:8b', 'reasoning');
      setReasoning((state) => ({ ...state, busy: false, output: result.response }));
    } catch (error) {
      setReasoning((state) => ({ ...state, busy: false, error: error instanceof Error ? error.message : 'Reasoning request failed' }));
    }
  };

  const runCoding = async () => {
    if (!coding.input.trim() || coding.busy) return;
    setCoding((state) => ({ ...state, busy: true, error: '' }));
    try {
      const result = await api.generateCode(coding.input, 'python');
      const output = result.code_blocks?.length
        ? result.code_blocks.map((block: { language: string; code: string }) => `\`\`${block.language}\n${block.code}\n\`\``).join('\n\n')
        : result.raw_response || 'The coding model returned no output.';
      setCoding((state) => ({ ...state, busy: false, output }));
    } catch (error) {
      setCoding((state) => ({ ...state, busy: false, error: error instanceof Error ? error.message : 'Coding request failed' }));
    }
  };

  const runVision = async () => {
    if (!vision.input.trim() || vision.busy || !image) return;
    setVision((state) => ({ ...state, busy: true, error: '' }));
    try {
      const base64 = image.includes(',') ? image.split(',')[1] : image;
      const result = await api.analyzeVision(vision.input, [base64]);
      setVision((state) => ({ ...state, busy: false, output: result.content || 'Vision analysis complete.' }));
    } catch (error) {
      setVision((state) => ({ ...state, busy: false, error: error instanceof Error ? error.message : 'Vision request failed' }));
    }
  };

  const handleImage = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setImage(reader.result as string);
    reader.readAsDataURL(file);
  };

  return (
    <main className="flex-1 min-w-0 overflow-y-auto p-5" style={{ backgroundColor: 'var(--color-deck-base)' }}>
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1"><Sparkles className="w-4 h-4" style={{ color: 'var(--color-amber-primary)' }} /><span className="font-label">MODEL WORKSPACES</span></div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>One task, one model panel</h1>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>Run reasoning, code, and visual analysis independently with explicit local model routing.</p>
        </div>
        <span className="hidden sm:inline-flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[10px] font-instrument" style={{ color: 'var(--color-verified)', backgroundColor: 'var(--color-verified-muted)', border: '1px solid var(--color-verified-border)' }}><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> ZERO EGRESS</span>
      </div>
      <div className={`grid grid-cols-1 gap-5 items-stretch ${showAll ? 'xl:grid-cols-3' : 'max-w-5xl'}`}>
        {(showAll || activePanel === 'reasoning') && <WorkspacePanel title="REASONING" model="Qwen3:8b" icon={<Brain className="w-4 h-4" />} accent="amber" state={reasoning} setState={setReasoning} onRun={runReasoning} action="Ask model" />}
        {(showAll || activePanel === 'coding') && <WorkspacePanel title="CODING" model="qwen2.5-coder:7b" icon={<Code2 className="w-4 h-4" />} accent="blue" state={coding} setState={setCoding} onRun={runCoding} action="Generate code" code />}
        {(showAll || activePanel === 'vision') && <WorkspacePanel title="VISION" model="qwen3-vl:8b" icon={<Eye className="w-4 h-4" />} accent="violet" state={vision} setState={setVision} onRun={runVision} action="Analyze image" image={image} onImage={() => fileInputRef.current?.click()} />}
      </div>
      <input ref={fileInputRef} type="file" accept="image/*" onChange={handleImage} className="hidden" />
    </main>
  );
}

function WorkspacePanel({ title, model, icon, accent, state, setState, onRun, action, code, image, onImage }: { title: string; model: string; icon: React.ReactNode; accent: 'amber' | 'blue' | 'violet'; state: PanelState; setState: React.Dispatch<React.SetStateAction<PanelState>>; onRun: () => void; action: string; code?: boolean; image?: string | null; onImage?: () => void }) {
  const colors = { amber: '#f59e0b', blue: '#60a5fa', violet: '#c084fc' };
  const color = colors[accent];
  return (
    <section className="surface-card min-h-[520px] flex flex-col overflow-hidden" style={{ borderColor: `${color}45` }}>
      <header className="p-4 border-b" style={{ borderColor: 'var(--color-deck-border)', backgroundColor: `${color}0d` }}>
        <div className="flex items-center justify-between gap-2"><div className="flex items-center gap-2" style={{ color }}><span>{icon}</span><h2 className="text-xs font-bold tracking-widest">{title}</h2></div><span className="w-2 h-2 rounded-full" style={{ backgroundColor: color, boxShadow: `0 0 10px ${color}` }} /></div>
        <div className="font-instrument mt-2 truncate" style={{ color: 'var(--color-text-secondary)' }}>{model}</div>
        <div className="text-[10px] mt-1" style={{ color: 'var(--color-text-muted)' }}>Dedicated inference lane</div>
      </header>
      <div className="flex-1 p-4 flex flex-col gap-3">
        {onImage && <button type="button" onClick={onImage} className="h-24 border border-dashed rounded-lg flex flex-col items-center justify-center gap-1 text-xs transition-colors hover:bg-white/[0.03]" style={{ borderColor: `${color}55`, color: 'var(--color-text-secondary)' }}>{image ? <img src={image} alt="Selected visual input" className="h-20 max-w-full object-contain" /> : <><ImagePlus className="w-5 h-5" style={{ color }} /><span>Upload visual input</span></>}</button>}
        <textarea value={state.input} onChange={(event) => setState((current) => ({ ...current, input: event.target.value }))} rows={code ? 7 : 5} className="w-full resize-none rounded-lg p-3 text-xs leading-relaxed outline-none" style={{ backgroundColor: 'var(--color-deck-deep)', border: '1px solid var(--color-deck-border)', color: 'var(--color-text-primary)' }} />
        <button type="button" onClick={onRun} disabled={state.busy || (!!onImage && !image)} className="flex items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-semibold transition-opacity disabled:opacity-40" style={{ backgroundColor: `${color}22`, border: `1px solid ${color}66`, color }}>{state.busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : onImage ? <Play className="w-3.5 h-3.5" /> : <Send className="w-3.5 h-3.5" />}{action}</button>
        <div className="flex-1 min-h-32 rounded-lg p-3 overflow-y-auto" style={{ backgroundColor: 'var(--color-deck-deep)', border: '1px solid var(--color-deck-border)' }}><div className="font-label mb-2" style={{ color }}>OUTPUT</div><pre className="whitespace-pre-wrap text-xs leading-relaxed font-sans" style={{ color: state.error ? 'var(--color-error)' : 'var(--color-text-secondary)' }}>{state.error || state.output || 'Results from this model will stay in this panel.'}</pre></div>
      </div>
    </section>
  );
}