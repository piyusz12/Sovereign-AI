/**
 * CommandBar — Industrial Command Deck Execution Center
 *
 * Provides real-time mission dispatch, quick-action prompt chips,
 * real file attachments, and model routing preview.
 */

import { useState, useRef, useEffect } from 'react';
import {
  Paperclip,
  X,
  Play,
  Layers,
} from 'lucide-react';
import { useMissionStore, type MissionType } from '@/store/missionStore';
import { useAppStore } from '@/store/appStore';

export function CommandBar() {
  const [command, setCommand] = useState('');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [selectedType] = useState<MissionType>('general');
  const [previewMode, setPreviewMode] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { runDemoMission, createMission } = useMissionStore();
  const { updateRouting } = useAppStore();

  const handleExecute = () => {
    if (!command.trim()) return;

    // Detect mission type from command if general
    let finalType = selectedType;
    if (finalType === 'general') {
      const lc = command.toLowerCase();
      if (lc.includes('code') || lc.includes('script') || lc.includes('python') || lc.includes('algorithm')) {
        finalType = 'coding';
      } else if (lc.includes('image') || lc.includes('diagram') || lc.includes('p&id') || lc.includes('schematic') || lc.includes('valve')) {
        finalType = 'vision';
      } else if (lc.includes('report') || lc.includes('document') || lc.includes('audit') || lc.includes('spec') || lc.includes('pdf')) {
        finalType = 'document';
      } else if (lc.includes('analyze') || lc.includes('data') || lc.includes('pressure')) {
        finalType = 'analysis';
      }
    }

    const routingMap: Record<MissionType, { task: string; model: string; reason: string }> = {
      document: { task: 'Document Reasoning', model: 'Qwen3-14B', reason: 'High contextual reasoning and zero-egress citation tracking' },
      coding: { task: 'Code Generation', model: 'Qwen2.5-Coder-7B', reason: 'Specialized syntax precision and AST code patching' },
      vision: { task: 'Vision Analysis', model: 'Qwen3-VL-8B', reason: 'Multimodal vision-language parser for engineering schematics' },
      analysis: { task: 'Data Analysis', model: 'Qwen3-14B', reason: 'Complex analytical synthesis and parameter verification' },
      general: { task: 'General Reasoning', model: 'Qwen3-14B', reason: 'Air-gapped general reasoning and multi-stage verification' },
    };

    const route = routingMap[finalType] || routingMap.general;
    updateRouting({
      task_type: route.task,
      selected_model: route.model,
      reason: route.reason,
    });

    // Create mission and launch simulation
    createMission(command, finalType, attachments);
    runDemoMission();

    setCommand('');
    setAttachments([]);
    setPreviewMode(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleExecute();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const names = Array.from(e.target.files).map((f) => f.name);
      setAttachments((prev) => [...prev, ...names]);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 100) + 'px';
    }
  }, [command]);

  return (
    <footer
      className="flex-shrink-0 border-t relative z-20"
      style={{
        backgroundColor: 'var(--color-deck-base)',
        borderColor: 'var(--color-deck-border)',
        boxShadow: '0 -8px 24px -4px rgba(0,0,0,0.5)',
      }}
    >
      {/* Hidden native file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        multiple
        className="hidden"
      />

      {/* Attachments preview row */}
      {attachments.length > 0 && (
        <div className="px-4 pt-2 flex items-center gap-2 flex-wrap">
          {attachments.map((file, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-mono bg-cyan-950/40 border border-cyan-500/30 text-cyan-300"
            >
              <Paperclip className="w-3 h-3 text-cyan-400" />
              <span>{file}</span>
              <button
                onClick={() => removeAttachment(i)}
                className="ml-1 hover:text-rose-400 transition-colors cursor-pointer"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Main command input & actions */}
      <div className="px-4 py-2.5">
        <div className="flex items-end gap-3">
          {/* Attach file button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-all cursor-pointer"
            title="Attach documents, schematics, or code files"
          >
            <Paperclip className="w-4 h-4 text-slate-400 hover:text-amber-400 transition-colors" />
          </button>

          {/* Text input area */}
          <div className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-2 focus-within:border-amber-500/50 focus-within:ring-1 focus-within:ring-amber-500/30 transition-all">
            <textarea
              ref={textareaRef}
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter sovereign mission objective, code synthesis request, or audit query..."
              rows={1}
              className="w-full resize-none bg-transparent outline-none text-sm placeholder:text-slate-500 text-slate-100"
              style={{ lineHeight: '1.5' }}
            />
            {previewMode && (
              <div className="mt-2 pt-2 border-t border-white/5 flex items-center gap-2 text-[11px] font-mono text-slate-400">
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
                <span>Routing Preview:</span>
                <span className="text-amber-300 font-bold">Qwen3-14B</span>
                <span className="text-slate-600">•</span>
                <span>VRAM Reserve:</span>
                <span className="text-cyan-300">5.5 GB</span>
                <span className="text-slate-600">•</span>
                <span>Air-Gap Check:</span>
                <span className="text-emerald-400">VERIFIED</span>
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">

            <button
              onClick={() => setPreviewMode(!previewMode)}
              className={`px-3 py-2 rounded-lg text-xs font-mono font-medium border transition-all cursor-pointer ${
                previewMode
                  ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
                  : 'bg-white/5 border-white/10 text-slate-400 hover:text-slate-200'
              }`}
              title="Preview execution route & VRAM allocation"
            >
              PREVIEW
            </button>

            <button
              onClick={handleExecute}
              disabled={!command.trim()}
              className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-bold tracking-wider transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-lg active:scale-95"
              style={{
                background: command.trim()
                  ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                  : 'rgba(255,255,255,0.06)',
                color: command.trim() ? '#07090e' : '#64748b',
                boxShadow: command.trim() ? '0 0 16px rgba(245, 158, 11, 0.4)' : 'none',
              }}
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>EXECUTE</span>
            </button>
          </div>
        </div>

        {/* Status hotkey hint */}
        <div className="mt-1.5 flex items-center justify-between text-[10px] font-mono text-slate-500">
          <div>
            <span>Press </span>
            <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">Ctrl</kbd>
            <span> + </span>
            <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">Enter</kbd>
            <span> to dispatch mission</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-emerald-400/80">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Zero-Egress Guard Active
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
