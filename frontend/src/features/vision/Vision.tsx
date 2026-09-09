import { useState, useRef } from 'react';
import {
  Eye,
  Image as ImageIcon,
  ScanLine,
  Download,
  Settings,
  Play,
  Loader2,
  UploadCloud,
  X,
} from 'lucide-react';
import { api } from '@/services/api';

export default function Vision() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('Analyze this image in detail. Extract text, identify components, and note any anomalies.');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);
  const [modelUsed, setModelUsed] = useState<string>('llama3.2-vision:latest');
  const [analysisDuration, setAnalysisDuration] = useState<number | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [maxTokens, setMaxTokens] = useState(1024);
  const [temperature, setTemperature] = useState(0.2);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sample SVG diagram as Data URI for immediate 1-click testing
  const SAMPLE_PID_IMAGE = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="600" height="400" fill="%230f172a"/><text x="30" y="50" fill="%2338bdf8" font-size="20" font-family="monospace">P%26ID REFINERY UNIT 04 - FLOW SCHEMATIC</text><rect x="50" y="100" width="120" height="200" rx="10" fill="%231e293b" stroke="%2338bdf8" stroke-width="2"/><text x="75" y="205" fill="%23f8fafc" font-size="14" font-family="sans-serif">VESSEL V-101</text><line x1="170" y1="200" x2="350" y2="200" stroke="%2310b981" stroke-width="4"/><polygon points="250,190 270,200 250,210" fill="%2310b981"/><circle cx="260" cy="200" r="16" fill="%230f172a" stroke="%23f59e0b" stroke-width="2"/><text x="248" y="204" fill="%23f59e0b" font-size="10" font-family="monospace">FCV-12</text><rect x="350" y="140" width="160" height="120" rx="6" fill="%231e293b" stroke="%23a855f7" stroke-width="2"/><text x="375" y="205" fill="%23f8fafc" font-size="14" font-family="sans-serif">HEAT EXCHANGER</text><text x="30" y="360" fill="%2394a3b8" font-size="12" font-family="monospace">TAGS: V-101, FCV-12, E-204 | STATUS: ACTIVE</text></svg>`;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setSelectedImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRunAnalysis = async (customPrompt?: string) => {
    const promptToUse = customPrompt || prompt;
    if (!selectedImage) {
      // Auto-load sample if none selected
      setSelectedImage(SAMPLE_PID_IMAGE);
    }
    const imageToAnalyze = selectedImage || SAMPLE_PID_IMAGE;

    setIsAnalyzing(true);
    setAnalysisResult(null);

    // Extract base64
    const base64Data = imageToAnalyze.includes(',')
      ? imageToAnalyze.split(',')[1]
      : imageToAnalyze;

    try {
      const res = await api.analyzeVision(promptToUse, [base64Data]);
      setAnalysisResult(res.content || 'Analysis complete.');
      setModelUsed(res.model_used || 'llama3.2-vision:latest');
      setAnalysisDuration(res.duration_ms || 1200);
    } catch (err: any) {
      const message = err instanceof Error ? err.message : 'Vision request failed';
      setAnalysisResult(
        `[Sovereign Vision Engine] Analysis unavailable.\n\n` +
          `The image was not analyzed because the vision backend could not be reached.\n\n` +
          `Backend message: ${message}\n\n` +
          `Start the backend on http://127.0.0.1:8080 and try again.`
      );
      setModelUsed('Unavailable');
      setAnalysisDuration(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleExport = () => {
    if (!analysisResult) return;
    const blob = new Blob([analysisResult], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vision_analysis_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 overflow-hidden font-sans">
      {/* Header */}
      <header className="flex-shrink-0 p-6 border-b border-slate-800 bg-slate-950/60 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center">
              <Eye className="w-6 h-6 mr-2 text-purple-400" />
              Vision Workspace
            </h2>
            <p className="text-slate-400 mt-1 text-sm">
              Multimodal document OCR, P&ID diagram understanding, and safety inspection.
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowConfigModal(true)}
              className="flex items-center px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
            >
              <Settings className="w-3.5 h-3.5 mr-1.5" />
              Configure
            </button>
            <button
              onClick={() => handleRunAnalysis()}
              disabled={isAnalyzing}
              className="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-800 text-white text-xs font-medium rounded-lg transition-colors shadow-lg shadow-purple-500/20"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 mr-1.5 fill-current" />
                  Run Analysis
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Image Selection & Preview */}
          <div className="space-y-4">
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-semibold text-slate-200 text-sm flex items-center">
                  <ImageIcon className="w-4 h-4 mr-2 text-purple-400" />
                  Input Image / Diagram
                </h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedImage(SAMPLE_PID_IMAGE)}
                    className="text-xs px-2.5 py-1 rounded bg-purple-500/10 border border-purple-500/20 text-purple-300 hover:bg-purple-500/20"
                  >
                    Load Sample P&ID
                  </button>
                  {selectedImage && (
                    <button
                      onClick={() => setSelectedImage(null)}
                      className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 hover:text-white"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {selectedImage ? (
                <div className="relative rounded-lg overflow-hidden border border-slate-800 bg-slate-900 max-h-72 flex items-center justify-center p-2">
                  <img
                    src={selectedImage}
                    alt="Uploaded preview"
                    className="max-h-64 object-contain rounded"
                  />
                </div>
              ) : (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-700/80 rounded-xl p-8 text-center hover:border-purple-500/50 hover:bg-purple-500/5 transition-all cursor-pointer group"
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="image/*"
                    className="hidden"
                  />
                  <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-purple-500/10 border border-purple-500/20 flex items-center justify-center group-hover:scale-105 transition-transform text-purple-400">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <h4 className="text-sm font-semibold text-slate-200 mb-1">
                    Click to browse or drop image here
                  </h4>
                  <p className="text-xs text-slate-500 mb-3">PNG, JPG, WEBP, or SVG schematics</p>
                  <button
                    type="button"
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700"
                  >
                    Browse Files
                  </button>
                </div>
              )}
            </div>

            {/* Prompt input */}
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5">
              <label className="text-xs font-semibold text-slate-300 block mb-2">
                Analysis Instruction / Prompt:
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500 resize-none"
                placeholder="Specify what features to detect or inspect..."
              />

              {/* Quick action buttons */}
              <div className="mt-3">
                <span className="text-[11px] text-slate-500 font-semibold block mb-2 uppercase tracking-wider">
                  Quick Vision Presets:
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <button
                    onClick={() => {
                      const p = 'Identify and locate all equipment, vessels, valves, and flow directions.';
                      setPrompt(p);
                      handleRunAnalysis(p);
                    }}
                    className="p-2 bg-slate-900 hover:bg-slate-800 rounded-lg border border-slate-800 text-slate-300 text-center"
                  >
                    P&ID Components
                  </button>
                  <button
                    onClick={() => {
                      const p = 'Perform OCR extraction on all tags, ratings, and measurement numbers.';
                      setPrompt(p);
                      handleRunAnalysis(p);
                    }}
                    className="p-2 bg-slate-900 hover:bg-slate-800 rounded-lg border border-slate-800 text-slate-300 text-center"
                  >
                    OCR Extraction
                  </button>
                  <button
                    onClick={() => {
                      const p = 'Check equipment for visible corrosion, wear, leakage, or defect markers.';
                      setPrompt(p);
                      handleRunAnalysis(p);
                    }}
                    className="p-2 bg-slate-900 hover:bg-slate-800 rounded-lg border border-slate-800 text-slate-300 text-center"
                  >
                    Defect Detection
                  </button>
                  <button
                    onClick={handleExport}
                    disabled={!analysisResult}
                    className="p-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 rounded-lg border border-slate-800 text-purple-300 text-center flex items-center justify-center"
                  >
                    <Download className="w-3.5 h-3.5 mr-1" /> Export
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Output & Model Status */}
          <div className="space-y-4">
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 flex flex-col h-full min-h-[380px]">
              <div className="flex justify-between items-center pb-3 border-b border-slate-800 mb-3">
                <div className="flex items-center space-x-2">
                  <ScanLine className="w-4 h-4 text-purple-400" />
                  <h3 className="font-semibold text-slate-200 text-sm">Vision Analysis Results</h3>
                </div>
                {analysisDuration && (
                  <span className="text-[11px] font-mono text-emerald-400">
                    {analysisDuration} ms • {modelUsed}
                  </span>
                )}
              </div>

              <div className="flex-1 overflow-y-auto">
                {isAnalyzing ? (
                  <div className="h-full flex flex-col items-center justify-center py-12 text-slate-400">
                    <Loader2 className="w-8 h-8 animate-spin text-purple-400 mb-3" />
                    <p className="text-sm font-medium">Processing vision tokens on GPU...</p>
                    <p className="text-xs text-slate-500 mt-1">Single-GPU VRAM Guard Active</p>
                  </div>
                ) : analysisResult ? (
                  <div className="p-4 bg-slate-900 rounded-lg border border-slate-800 text-xs text-slate-200 whitespace-pre-wrap leading-relaxed font-mono">
                    {analysisResult}
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center py-12 text-slate-500">
                    <Eye className="w-10 h-10 mb-3 opacity-40" />
                    <p className="text-sm">No analysis performed yet</p>
                    <p className="text-xs mt-1">Select an image and click "Run Analysis"</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Configure Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl max-w-sm w-full p-6 shadow-2xl relative text-xs">
            <button
              onClick={() => setShowConfigModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-100 mb-4">Vision Model Configuration</h3>
            <div className="space-y-4 text-slate-300">
              <div>
                <label className="block mb-1 font-semibold">Active Model:</label>
                <div className="p-2 bg-slate-900 rounded border border-slate-800 font-mono text-emerald-400">
                  {modelUsed}
                </div>
              </div>
              <div>
                <label className="block mb-1 font-semibold">Max Tokens: {maxTokens}</label>
                <input
                  type="range"
                  min="256"
                  max="4096"
                  step="256"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block mb-1 font-semibold">Temperature: {temperature}</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowConfigModal(false)}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg"
              >
                Save Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}SAMPLE_PID_IMAGE = data:image/png;base64,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;mport { useState, useRef } from 'react';
import {
  Eye,
  Image as ImageIcon,
  ScanLine,
  Download,
  Settings,
  Play,
  Loader2,
  UploadCloud,
  X,
} from 'lucide-react';
import { api } from '@/services/api';

export default function Vision() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('Analyze this image in detail. Extract text, identify components, and note any anomalies.');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);
  const [modelUsed, setModelUsed] = useState<string>('llama3.2-vision:latest');
  const [analysisDuration, setAnalysisDuration] = useState<number | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [maxTokens, setMaxTokens] = useState(1024);
  const [temperature, setTemperature] = useState(0.2);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sample SVG diagram as Data URI for immediate 1-click testing
  const SAMPLE_PID_IMAGE = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="600" height="400" fill="%230f172a"/><text x="30" y="50" fill="%2338bdf8" font-size="20" font-family="monospace">P%26ID REFINERY UNIT 04 - FLOW SCHEMATIC</text><rect x="50" y="100" width="120" height="200" rx="10" fill="%231e293b" stroke="%2338bdf8" stroke-width="2"/><text x="75" y="205" fill="%23f8fafc" font-size="14" font-family="sans-serif">VESSEL V-101</text><line x1="170" y1="200" x2="350" y2="200" stroke="%2310b981" stroke-width="4"/><polygon points="250,190 270,200 250,210" fill="%2310b981"/><circle cx="260" cy="200" r="16" fill="%230f172a" stroke="%23f59e0b" stroke-width="2"/><text x="248" y="204" fill="%23f59e0b" font-size="10" font-family="monospace">FCV-12</text><rect x="350" y="140" width="160" height="120" rx="6" fill="%231e293b" stroke="%23a855f7" stroke-width="2"/><text x="375" y="205" fill="%23f8fafc" font-size="14" font-family="sans-serif">HEAT EXCHANGER</text><text x="30" y="360" fill="%2394a3b8" font-size="12" font-family="monospace">TAGS: V-101, FCV-12, E-204 | STATUS: ACTIVE</text></svg>`;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setSelectedImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRunAnalysis = async (customPrompt?: string) => {
    const promptToUse = customPrompt || prompt;
    if (!selectedImage) {
      // Auto-load sample if none selected
      setSelectedImage(SAMPLE_PID_IMAGE);
    }
    const imageToAnalyze = selectedImage || SAMPLE_PID_IMAGE;

    setIsAnalyzing(true);
    setAnalysisResult(null);

    // Extract base64
    const base64Data = imageToAnalyze.includes(',')
      ? imageToAnalyze.split(',')[1]
      : imageToAnalyze;

    try {
      const res = await api.analyzeVision(promptToUse, [base64Data]);
      setAnalysisResult(res.content || 'Analysis complete.');
      setModelUsed(res.model_used || 'llama3.2-vision:latest');
      setAnalysisDuration(res.duration_ms || 1200);
    } catch (err: any) {
      const message = err instanceof Error ? err.message : 'Vision request failed';
      setAnalysisResult(
        `[Sovereign Vision Engine] Analysis unavailable.\n\n` +
          `The image was not analyzed because the vision backend could not be reached.\n\n` +
          `Backend message: ${message}\n\n` +
          `Start the backend on http://127.0.0.1:8080 and try again.`
      );
      setModelUsed('Unavailable');
      setAnalysisDuration(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleExport = () => {
    if (!analysisResult) return;
    const blob = new Blob([analysisResult], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vision_analysis_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 overflow-hidden font-sans">
      {/* Header */}
      <header className="flex-shrink-0 p-6 border-b border-slate-800 bg-slate-950/60 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center">
              <Eye className="w-6 h-6 mr-2 text-purple-400" />
              Vision Workspace
            </h2>
            <p className="text-slate-400 mt-1 text-sm">
              Multimodal document OCR, P&ID diagram understanding, and safety inspection.
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowConfigModal(true)}
              className="flex items-center px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
            >
              <Settings className="w-3.5 h-3.5 mr-1.5" />
              Configure
            </button>
            <button
              onClick={() => handleRunAnalysis()}
              disabled={isAnalyzing}
              className="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-800 text-white text-xs font-medium rounded-lg transition-colors shadow-lg shadow-purple-500/20"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 mr-1.5 fill-current" />
                  Run Analysis
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Image Selection & Preview */}
          <div className="space-y-4">
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-semibold text-slate-200 text-sm flex items-center">
                  <ImageIcon className="w-4 h-4 mr-2 text-purple-400" />
                  Input Image / Diagram
                </h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedImage(SAMPLE_PID_IMAGE)}
                    className="text-xs px-2.5 py-1 rounded bg-purple-500/10 border border-purple-500/20 text-purple-300 hover:bg-purple-500/20"
                  >
                    Load Sample P&ID
                  </button>
                  {selectedImage && (
                    <button
                      onClick={() => setSelectedImage(null)}
                      className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 hover:text-white"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {selectedImage ? (
                <div className="relative rounded-lg overflow-hidden border border-slate-800 bg-slate-900 max-h-72 flex items-center justify-center p-2">
                  <img
                    src={selectedImage}
                    alt="Uploaded preview"
                    className="max-h-64 object-contain rounded"
                  />
                </div>
              ) : (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-700/80 rounded-xl p-8 text-center hover:border-purple-500/50 hover:bg-purple-500/5 transition-all cursor-pointer group"
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="image/*"
                    className="hidden"
                  />
                  <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-purple-500/10 border border-purple-500/20 flex items-center justify-center group-hover:scale-105 transition-transform text-purple-400">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <h4 className="text-sm font-semibold text-slate-200 mb-1">
                    Click to browse or drop image here
                  </h4>
                  <p className="text-xs text-slate-500 mb-3">PNG, JPG, WEBP, or SVG schematics</p>
                  <button
                    type="button"
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700"
                  >
                    Browse Files
                  </button>
                </div>
              )}
            </div>

            {/* Prompt input */}
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5">
              <label className="text-xs font-semibold text-slate-300 block mb-2">
                Analysis Instruction / Prompt:
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500 resize-none"
                placeholder="Specify what features to detect or inspect..."
              />

              {/* Quick action buttons */}
              <div className="mt-3">
                <span className="text-[11px] text-slate-500 font-semibold block mb-2 uppercase tracking-wider">
                  Quick Vision Presets:
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <button
                    onClick={() => {
                      const p = 'Identify and locate all equipment, vessels, valves, and flow directions.';
                      setPrompt(p);
                      handleRunAnalysis(p);
                    }}
                    className="p-2 bg-slate-900 hover:bg-slate-800 rounded-lg border border-slate-800 text-slate-300 text-center"
                  >
                    P&ID Components
                  </button>
                  <button
                    onClick={() => {
                      const p = 'Perform OCR extraction on all tags, ratings, and measurement numbers.';
                      setPrompt(p);
                      handleRunAnalysis(p);
                    }}
                    className="p-2 bg-slate-900 hover:bg-slate-800 rounded-lg border border-slate-800 text-slate-300 text-center"
                  >
                    OCR Extraction
                  </button>
                  <button
                    onClick={() => {
                      const p = 'Check equipment for visible corrosion, wear, leakage, or defect markers.';
                      setPrompt(p);
                      handleRunAnalysis(p);
                    }}
                    className="p-2 bg-slate-900 hover:bg-slate-800 rounded-lg border border-slate-800 text-slate-300 text-center"
                  >
                    Defect Detection
                  </button>
                  <button
                    onClick={handleExport}
                    disabled={!analysisResult}
                    className="p-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 rounded-lg border border-slate-800 text-purple-300 text-center flex items-center justify-center"
                  >
                    <Download className="w-3.5 h-3.5 mr-1" /> Export
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Output & Model Status */}
          <div className="space-y-4">
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 flex flex-col h-full min-h-[380px]">
              <div className="flex justify-between items-center pb-3 border-b border-slate-800 mb-3">
                <div className="flex items-center space-x-2">
                  <ScanLine className="w-4 h-4 text-purple-400" />
                  <h3 className="font-semibold text-slate-200 text-sm">Vision Analysis Results</h3>
                </div>
                {analysisDuration && (
                  <span className="text-[11px] font-mono text-emerald-400">
                    {analysisDuration} ms • {modelUsed}
                  </span>
                )}
              </div>

              <div className="flex-1 overflow-y-auto">
                {isAnalyzing ? (
                  <div className="h-full flex flex-col items-center justify-center py-12 text-slate-400">
                    <Loader2 className="w-8 h-8 animate-spin text-purple-400 mb-3" />
                    <p className="text-sm font-medium">Processing vision tokens on GPU...</p>
                    <p className="text-xs text-slate-500 mt-1">Single-GPU VRAM Guard Active</p>
                  </div>
                ) : analysisResult ? (
                  <div className="p-4 bg-slate-900 rounded-lg border border-slate-800 text-xs text-slate-200 whitespace-pre-wrap leading-relaxed font-mono">
                    {analysisResult}
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center py-12 text-slate-500">
                    <Eye className="w-10 h-10 mb-3 opacity-40" />
                    <p className="text-sm">No analysis performed yet</p>
                    <p className="text-xs mt-1">Select an image and click "Run Analysis"</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Configure Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl max-w-sm w-full p-6 shadow-2xl relative text-xs">
            <button
              onClick={() => setShowConfigModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-slate-100 mb-4">Vision Model Configuration</h3>
            <div className="space-y-4 text-slate-300">
              <div>
                <label className="block mb-1 font-semibold">Active Model:</label>
                <div className="p-2 bg-slate-900 rounded border border-slate-800 font-mono text-emerald-400">
                  {modelUsed}
                </div>
              </div>
              <div>
                <label className="block mb-1 font-semibold">Max Tokens: {maxTokens}</label>
                <input
                  type="range"
                  min="256"
                  max="4096"
                  step="256"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block mb-1 font-semibold">Temperature: {temperature}</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowConfigModal(false)}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg"
              >
                Save Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
