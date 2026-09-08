import { useState, useRef, useEffect } from 'react';
import {
  Send,
  MessageSquare,
  Sparkles,
  User,
  Loader2,
  Trash2,
  Cpu,
  Clock,
  HelpCircle,
  Compass,
} from 'lucide-react';
import { api, type ChatResult } from '@/services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  model_used?: string;
  task_type?: string;
  duration_ms?: number;
  reason?: string;
}

const QUICK_PROMPTS = [
  'Verify zero-egress data sovereignty policy',
  'Write a Python script to monitor GPU temperature with logging',
  'Explain how hybrid vector and BM25 retrieval works',
];

export default function Assistant() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        'Welcome to Sovereign AI Workbench. All inferences run strictly on your local hardware. How can I assist your engineering or documentation tasks today?',
      timestamp: new Date(),
      model_used: 'Qwen3:8b',
      task_type: 'reasoning',
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [selectedModel, setSelectedModel] = useState('auto');
  const [isLoading, setIsLoading] = useState(false);
  const [classificationPreview, setClassificationPreview] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputValue;
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInputValue('');
    setIsLoading(true);
    setClassificationPreview(null);

    const modelParam = selectedModel === 'auto' ? undefined : selectedModel;

    try {
      const result: ChatResult = await api.chat(text, modelParam);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: result.response,
        timestamp: new Date(),
        model_used: result.route?.model || 'Local Model',
        task_type: result.route?.task_type || 'reasoning',
        duration_ms: result.duration_ms,
        reason: result.route?.reason,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `[Sovereign Error] ${err.message || 'Unable to complete local inference.'}`,
        timestamp: new Date(),
        model_used: 'Fallback Handler',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePreviewRouting = async () => {
    if (!inputValue.trim()) return;
    try {
      const res = await api.classify(inputValue);
      if (res && res.routing_decision) {
        setClassificationPreview(
          `Broker Decision: ${res.routing_decision.model_name} (${res.routing_decision.task_type}) - ${res.routing_decision.reason}`
        );
      }
    } catch {
      setClassificationPreview('Broker Preview: Qwen3:8b (Keyword Rule)');
    }
  };

  const handleClear = () => {
    setMessages([
      {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Chat cleared. How can I assist you?',
        timestamp: new Date(),
      },
    ]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 overflow-hidden font-sans">
      {/* Header */}
      <header className="flex-shrink-0 px-6 py-4 border-b border-slate-800 bg-slate-950/70 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-slate-100 tracking-tight flex items-center">
              <Sparkles className="w-5 h-5 mr-2 text-blue-400" />
              Sovereign AI Assistant
            </h2>
            <p className="text-slate-400 text-xs mt-0.5">
              Local reasoning, code generation, and knowledge synthesis.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {/* Model Selector */}
            <div className="flex items-center space-x-2 bg-slate-900 border border-slate-700/80 rounded-lg px-2.5 py-1.5">
              <Cpu className="w-3.5 h-3.5 text-blue-400" />
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="auto">Dynamic Broker (Auto)</option>
                <option value="Qwen3:8b">Reasoning: Qwen3:8b</option>
                <option value="qwen2.5-coder:7b">Coding: qwen2.5-coder:7b</option>
                <option value="llama3.2-vision:latest">Vision: llama3.2-vision</option>
              </select>
            </div>

            {/* Clear Chat Button */}
            <button
              onClick={handleClear}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 rounded-lg border border-slate-700 transition-colors"
              title="Clear Conversation"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[78%] rounded-2xl px-5 py-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-sm shadow-md shadow-blue-500/10'
                  : 'bg-slate-950/80 text-slate-100 rounded-bl-sm border border-slate-800/90 shadow-lg'
              }`}
            >
              <div className="flex items-start space-x-3">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                    message.role === 'user'
                      ? 'bg-blue-500'
                      : 'bg-emerald-500/20 border border-emerald-500/30'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User className="w-3.5 h-3.5" />
                  ) : (
                    <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>

                  {/* Metadata pill for assistant response */}
                  {message.role === 'assistant' && (
                    <div className="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-slate-800/60 text-[11px] text-slate-500 font-mono">
                      {message.model_used && (
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-emerald-400">
                          {message.model_used}
                        </span>
                      )}
                      {message.task_type && (
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-blue-400">
                          {message.task_type}
                        </span>
                      )}
                      {message.duration_ms !== undefined && (
                        <span className="flex items-center text-slate-400">
                          <Clock className="w-3 h-3 mr-1" />
                          {message.duration_ms} ms
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-950/80 text-slate-100 rounded-2xl rounded-bl-sm px-5 py-3 border border-slate-800 shadow-md">
              <div className="flex items-center space-x-3">
                <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                <span className="text-xs text-slate-400 font-mono">Running local inference on GPU...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Footer / Input Area */}
      <div className="flex-shrink-0 p-5 border-t border-slate-800 bg-slate-950/70 backdrop-blur-md">
        {/* Quick prompt chips */}
        <div className="flex items-center space-x-2 mb-3 overflow-x-auto pb-1 text-xs">
          <span className="text-slate-500 flex items-center flex-shrink-0 text-[11px]">
            <Compass className="w-3 h-3 mr-1 text-blue-400" />
            Suggestions:
          </span>
          {QUICK_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="px-3 py-1 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-slate-700 transition-colors whitespace-nowrap text-xs flex-shrink-0"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Classification Preview */}
        {classificationPreview && (
          <div className="mb-2 p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs flex items-center justify-between">
            <span>{classificationPreview}</span>
            <button onClick={() => setClassificationPreview(null)} className="text-slate-400 hover:text-white">
              ✕
            </button>
          </div>
        )}

        <div className="flex items-end space-x-3 max-w-5xl mx-auto">
          <div className="flex-1 relative">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a technical question, request code generation, or analyze documents..."
              rows={2}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 resize-none text-sm transition-all"
            />
          </div>

          <button
            onClick={handlePreviewRouting}
            className="p-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition-colors text-xs flex items-center"
            title="Preview model broker decision"
          >
            <HelpCircle className="w-5 h-5" />
          </button>

          <button
            onClick={() => handleSend()}
            disabled={!inputValue.trim() || isLoading}
            className="p-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl transition-all shadow-lg shadow-blue-500/20 disabled:shadow-none"
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
