/**
 * CommandBar — Execute-oriented command input at the bottom
 *
 * Uses "mission" language, not chatbot language.
 * Buttons: EXECUTE MISSION, PLAN, PREVIEW, VERIFY, EXPORT
 */

import { useState, useRef, useEffect } from 'react';
import {
  Plus,
  Paperclip,
  X,
} from 'lucide-react';
import { useMissionStore, type MissionType } from '@/store/missionStore';
import { useAppStore } from '@/store/appStore';

export function CommandBar() {
  const [command, setCommand] = useState('');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { createMission } = useMissionStore();
  const { updateRouting } = useAppStore();

  const handleExecute = () => {
    if (!command.trim()) return;

    // Detect mission type from command
    let detectedType: MissionType = 'general';
    const lc = command.toLowerCase();
    if (lc.includes('code') || lc.includes('script') || lc.includes('program') || lc.includes('function')) {
      detectedType = 'coding';
    } else if (lc.includes('image') || lc.includes('diagram') || lc.includes('p&id') || lc.includes('photo')) {
      detectedType = 'vision';
    } else if (lc.includes('report') || lc.includes('document') || lc.includes('pdf') || lc.includes('inspect') || lc.includes('approval') || lc.includes('sop')) {
      detectedType = 'document';
    } else if (lc.includes('analyze') || lc.includes('analysis') || lc.includes('data')) {
      detectedType = 'analysis';
    }


    // Update routing
    const routingMap: Record<MissionType, { task: string; model: string; reason: string }> = {
      document: { task: 'Document Reasoning', model: 'Qwen3-14B', reason: 'High reasoning requirement for document analysis' },
      coding: { task: 'Code Generation', model: 'Qwen2.5-Coder-7B', reason: 'Specialized code generation model' },
      vision: { task: 'Vision Analysis', model: 'Qwen3-VL-8B', reason: 'Multimodal vision-language model required' },
      analysis: { task: 'Data Analysis', model: 'Qwen3-14B', reason: 'Complex analytical reasoning required' },
      general: { task: 'General Reasoning', model: 'Qwen3-14B', reason: 'General-purpose reasoning' },
    };
    const route = routingMap[detectedType] || routingMap.general;
    updateRouting({
      task_type: route.task,
      selected_model: route.model,
      reason: route.reason,
    });

    // Create a real mission
    createMission(command.trim(), detectedType, attachments);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleExecute();
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [command]);

  return (
    <div
      className="flex-shrink-0 border-t"
      style={{
        backgroundColor: 'var(--color-deck-base)',
        borderColor: 'var(--color-deck-border)',
      }}
    >
      {/* Attachments row */}
      {attachments.length > 0 && (
        <div className="px-5 pt-2 flex items-center gap-2 flex-wrap">
          {attachments.map((file, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-instrument"
              style={{
                backgroundColor: 'var(--color-deck-elevated)',
                border: '1px solid var(--color-deck-border)',
                color: 'var(--color-text-secondary)',
              }}
            >
              <Paperclip className="w-3 h-3" style={{ color: 'var(--color-amber-primary)' }} />
              {file}
              <button
                onClick={() => removeAttachment(i)}
                className="ml-0.5 hover:text-[var(--color-error)] transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="px-5 py-3">
        <div className="flex items-start gap-3">
          {/* Add button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-1 p-2 rounded-lg transition-colors"
            style={{
              backgroundColor: 'var(--color-deck-elevated)',
              border: '1px solid var(--color-deck-border)',
              color: 'var(--color-text-muted)',
            }}
          >
            <Plus className="w-4 h-4" />
          </button>

          {/* Textarea */}
          <div className="flex-1">
            <textarea
              ref={textareaRef}
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsExpanded(true)}
              placeholder="Command — Describe your mission objective..."
              rows={1}
              className="w-full resize-none bg-transparent outline-none text-sm placeholder:text-[var(--color-text-dim)]"
              style={{ color: 'var(--color-text-primary)', lineHeight: '1.6' }}
            />
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1.5 mt-0.5">
            {isExpanded && (
              <>
                <button
                  className="px-2.5 py-1.5 rounded-md text-[10px] font-semibold tracking-wider transition-colors"
                  style={{
                    backgroundColor: 'var(--color-deck-elevated)',
                    border: '1px solid var(--color-deck-border)',
                    color: 'var(--color-text-muted)',
                  }}
                >
                  PLAN
                </button>
                <button
                  className="px-2.5 py-1.5 rounded-md text-[10px] font-semibold tracking-wider transition-colors"
                  style={{
                    backgroundColor: 'var(--color-deck-elevated)',
                    border: '1px solid var(--color-deck-border)',
                    color: 'var(--color-text-muted)',
                  }}
                >
                  PREVIEW
                </button>
              </>
            )}
            <button
              onClick={handleExecute}
              disabled={!command.trim()}
              className="px-4 py-1.5 rounded-md text-[10px] font-bold tracking-wider transition-all disabled:opacity-30"
              style={{
                backgroundColor: command.trim() ? 'var(--color-amber-primary)' : 'var(--color-deck-elevated)',
                color: command.trim() ? 'var(--color-deck-void)' : 'var(--color-text-dim)',
                border: `1px solid ${command.trim() ? 'var(--color-amber-hover)' : 'var(--color-deck-border)'}`,
              }}
            >
              EXECUTE MISSION
            </button>
          </div>
        </div>

        {/* Hint */}
        {!isExpanded && (
          <div className="mt-1 text-[10px]" style={{ color: 'var(--color-text-dim)' }}>
            Ctrl+Enter to execute • Click + to attach files • Type to begin
          </div>
        )}
      </div>
    </div>
  );
}
