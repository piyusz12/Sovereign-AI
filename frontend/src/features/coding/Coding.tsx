import { Code, Play, Save, GitBranch, Terminal, FileCode, CheckCircle, XCircle } from 'lucide-react';

interface CodeFile {
  id: string;
  name: string;
  language: string;
  status: 'modified' | 'saved' | 'error';
}

const mockFiles: CodeFile[] = [
  { id: '1', name: 'main.py', language: 'python', status: 'modified' },
  { id: '2', name: 'utils.ts', language: 'typescript', status: 'saved' },
  { id: '3', name: 'config.json', language: 'json', status: 'saved' },
  { id: '4', name: 'test_app.py', language: 'python', status: 'error' },
];

export default function Coding() {
  return (
    <div className="h-full flex flex-col bg-slate-900 overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 p-6 border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center">
              <Code className="w-6 h-6 mr-2 text-emerald-400" />
              Coding Agent
            </h2>
            <p className="text-slate-400 mt-1 text-sm">AI-powered code generation and refactoring</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-md transition-colors border border-slate-700">
              <GitBranch className="w-4 h-4 mr-2" />
              Branch
            </button>
            <button className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-md transition-colors border border-slate-700">
              <Save className="w-4 h-4 mr-2" />
              Save
            </button>
            <button className="flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-md transition-colors shadow-lg shadow-emerald-500/20">
              <Play className="w-4 h-4 mr-2" />
              Run Code
            </button>
          </div>
        </div>

        {/* Prompt Input */}
        <div className="relative">
          <textarea
            placeholder="Describe what you want to build or refactor..."
            rows={2}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 pr-32 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 resize-none transition-all duration-200"
          />
          <div className="absolute right-3 bottom-3 flex items-center space-x-2">
            <button className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-md transition-colors">
              Generate
            </button>
          </div>
        </div>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden flex">
        {/* File Explorer */}
        <aside className="w-64 flex-shrink-0 border-r border-slate-800 bg-slate-950/30 overflow-y-auto">
          <div className="p-4 border-b border-slate-800">
            <h3 className="font-semibold text-slate-200 text-sm flex items-center">
              <FileCode className="w-4 h-4 mr-2 text-emerald-400" />
              Project Files
            </h3>
          </div>
          <div className="p-2">
            {mockFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center justify-between px-3 py-2 rounded-md hover:bg-slate-800/50 cursor-pointer group transition-colors"
              >
                <div className="flex items-center space-x-2 min-w-0">
                  <Terminal className="w-4 h-4 text-slate-500 flex-shrink-0" />
                  <span className="text-sm text-slate-300 truncate">{file.name}</span>
                </div>
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  file.status === 'modified' ? 'bg-amber-400' :
                  file.status === 'saved' ? 'bg-emerald-400' : 'bg-rose-400'
                }`} />
              </div>
            ))}
          </div>
        </aside>

        {/* Code Editor Area */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden h-full flex flex-col">
            {/* Editor Tabs */}
            <div className="flex items-center border-b border-slate-800 bg-slate-950/50 px-2">
              <TabButton name="main.py" active />
              <TabButton name="utils.ts" />
              <TabButton name="test_app.py" hasError />
            </div>

            {/* Code Area */}
            <div className="flex-1 p-4 font-mono text-sm overflow-auto">
              <div className="flex">
                <div className="text-slate-600 select-none pr-4 text-right">
                  {Array.from({ length: 20 }, (_, i) => (
                    <div key={i} className="leading-6">{i + 1}</div>
                  ))}
                </div>
                <pre className="flex-1 text-slate-300 leading-6">
                  <code>{`import asyncio
from typing import List, Optional

class AIAgent:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.context_window = 8192
    
    async def generate(
        self, 
        prompt: str, 
        max_tokens: int = 1024
    ) -> Optional[str]:
        """Generate a response using the AI model."""
        try:
            # TODO: Implement actual API call
            response = await self._call_api(prompt, max_tokens)
            return response.completion
        except Exception as e:
            print(f"Generation error: {e}")
            return None
    
    def _call_api(self, prompt: str, tokens: int):
        # Placeholder for API implementation
        pass`}</code>
                </pre>
              </div>
            </div>

            {/* Status Bar */}
            <div className="flex items-center justify-between px-4 py-2 border-t border-slate-800 bg-slate-950/50 text-xs text-slate-500">
              <div className="flex items-center space-x-4">
                <span>Python 3.11</span>
                <span>UTF-8</span>
                <span>Ln 15, Col 32</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span>No syntax errors</span>
              </div>
            </div>
          </div>
        </main>

        {/* Output Panel */}
        <aside className="w-80 flex-shrink-0 border-l border-slate-800 bg-slate-950/30 overflow-y-auto">
          <div className="p-4 border-b border-slate-800">
            <h3 className="font-semibold text-slate-200 text-sm flex items-center">
              <Terminal className="w-4 h-4 mr-2 text-blue-400" />
              Output
            </h3>
          </div>
          <div className="p-4 space-y-3">
            <OutputItem type="info" message="Ready to execute code" />
            <OutputItem type="success" message="Last run completed in 1.2s" />
            <OutputItem type="error" message="Test failed: assertion error on line 42" />
          </div>
        </aside>
      </div>
    </div>
  );
}

interface TabButtonProps {
  name: string;
  active?: boolean;
  hasError?: boolean;
}

function TabButton({ name, active, hasError }: TabButtonProps) {
  return (
    <button
      className={`px-4 py-2 text-sm border-r border-slate-800 transition-colors ${
        active
          ? 'bg-slate-800 text-slate-200'
          : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
      }`}
    >
      <span className="flex items-center">
        {name}
        {hasError && <XCircle className="w-3.5 h-3.5 ml-2 text-rose-400" />}
      </span>
    </button>
  );
}

interface OutputItemProps {
  type: 'info' | 'success' | 'error';
  message: string;
}

function OutputItem({ type, message }: OutputItemProps) {
  const styles = {
    info: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    success: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    error: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
  };

  return (
    <div className={`p-2 rounded border text-xs ${styles[type]}`}>
      {message}
    </div>
  );
}
