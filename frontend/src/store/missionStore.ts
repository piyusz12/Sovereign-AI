/**
 * Sovereign Command Deck — Mission Store
 *
 * Manages the complete lifecycle of missions: creation, pipeline execution,
 * evidence tracking, trace recording, and replay.
 */

import { create } from 'zustand';
import { useAppStore } from './appStore';

/* ═══════════════════════════════════════════════════════════
   TYPE DEFINITIONS
   ═══════════════════════════════════════════════════════════ */

export type MissionType = 'document' | 'coding' | 'vision' | 'analysis' | 'general';
export type MissionStatus = 'planning' | 'executing' | 'verifying' | 'completed' | 'failed';
export type StepStatus = 'queued' | 'running' | 'verified' | 'failed' | 'skipped';

export interface PipelineStep {
  id: string;
  name: string;
  description: string;
  status: StepStatus;
  startedAt?: number;
  completedAt?: number;
  duration_ms?: number;
  metrics?: Record<string, string | number>;
  details?: string;
}

export interface EvidenceClaim {
  id: string;
  claim: string;
  confidence: number;
  sources: Array<{
    title: string;
    location: string;
    snippet?: string;
  }>;
}

export interface TraceEntry {
  timestamp: number;
  offset_ms: number;
  event: string;
  detail?: string;
  step_id?: string;
}

export interface Mission {
  id: string;
  number: number;
  title: string;
  type: MissionType;
  status: MissionStatus;
  input?: string;
  objective?: string;
  command: string;
  createdAt: number;
  startedAt?: number;
  completedAt?: number;
  total_duration_ms?: number;
  pipeline: PipelineStep[];
  evidence: EvidenceClaim[];
  trace: TraceEntry[];
  output?: {
    type: string;
    filename?: string;
    content?: string;
  };
  model_used?: string;
  attachments?: string[];
}

export interface MissionStore {
  missions: Mission[];
  activeMissionId: string | null;
  missionCounter: number;
  isReplayMode: boolean;
  replayStep: number;

  // Getters
  getActiveMission: () => Mission | undefined;
  getMission: (id: string) => Mission | undefined;

  // Mission lifecycle
  createMission: (command: string, type?: MissionType, attachments?: string[]) => Mission;
  setActiveMission: (id: string | null) => void;
  updateMissionStatus: (id: string, status: MissionStatus) => void;
  completeMission: (id: string, output?: Mission['output']) => void;

  // Pipeline
  updatePipelineStep: (missionId: string, stepId: string, update: Partial<PipelineStep>) => void;
  advancePipeline: (missionId: string) => void;

  // Evidence
  addEvidence: (missionId: string, evidence: EvidenceClaim) => void;

  // Trace
  addTraceEntry: (missionId: string, event: string, detail?: string, stepId?: string) => void;

  // Replay
  startReplay: (missionId: string) => void;
  stopReplay: () => void;
  setReplayStep: (step: number) => void;

  // Demo
  runDemoMission: () => void;
}

/* ═══════════════════════════════════════════════════════════
   PIPELINE TEMPLATES
   ═══════════════════════════════════════════════════════════ */

function getDocumentPipeline(): PipelineStep[] {
  return [
    { id: 'understand', name: 'UNDERSTAND', description: 'Analyze request and classify task', status: 'queued' },
    { id: 'ingest', name: 'DOCUMENT INGESTION', description: 'Parse and extract content', status: 'queued' },
    { id: 'ocr', name: 'OCR EXTRACTION', description: 'Optical character recognition', status: 'queued' },
    { id: 'rag', name: 'RAG RETRIEVAL', description: 'Search knowledge base', status: 'queued' },
    { id: 'rerank', name: 'RERANKING', description: 'Score and filter results', status: 'queued' },
    { id: 'reason', name: 'REASONING', description: 'LLM inference and analysis', status: 'queued' },
    { id: 'verify', name: 'VERIFICATION', description: 'Validate outputs', status: 'queued' },
    { id: 'output', name: 'GENERATE OUTPUT', description: 'Create deliverable', status: 'queued' },
  ];
}

function getCodingPipeline(): PipelineStep[] {
  return [
    { id: 'understand', name: 'UNDERSTAND', description: 'Parse coding request', status: 'queued' },
    { id: 'plan', name: 'PLAN', description: 'Design solution approach', status: 'queued' },
    { id: 'generate', name: 'CODE GENERATION', description: 'Generate code', status: 'queued' },
    { id: 'execute', name: 'SANDBOX EXECUTE', description: 'Run in isolated sandbox', status: 'queued' },
    { id: 'test', name: 'TEST & VALIDATE', description: 'Execute test cases', status: 'queued' },
    { id: 'repair', name: 'ERROR REPAIR', description: 'Fix issues if found', status: 'queued' },
    { id: 'output', name: 'PACKAGE OUTPUT', description: 'Bundle deliverables', status: 'queued' },
  ];
}

function getVisionPipeline(): PipelineStep[] {
  return [
    { id: 'understand', name: 'UNDERSTAND', description: 'Analyze vision request', status: 'queued' },
    { id: 'load', name: 'IMAGE LOADING', description: 'Load and preprocess image', status: 'queued' },
    { id: 'detect', name: 'DETECTION', description: 'Identify regions and components', status: 'queued' },
    { id: 'ocr', name: 'OCR LABELS', description: 'Extract text from image', status: 'queued' },
    { id: 'analyze', name: 'ANALYSIS', description: 'Vision model inference', status: 'queued' },
    { id: 'evidence', name: 'EVIDENCE MAPPING', description: 'Map observations to evidence', status: 'queued' },
    { id: 'output', name: 'REPORT', description: 'Generate analysis report', status: 'queued' },
  ];
}

function getGeneralPipeline(): PipelineStep[] {
  return [
    { id: 'understand', name: 'UNDERSTAND', description: 'Classify and route request', status: 'queued' },
    { id: 'retrieve', name: 'RETRIEVE', description: 'Search relevant context', status: 'queued' },
    { id: 'reason', name: 'REASON', description: 'LLM inference', status: 'queued' },
    { id: 'verify', name: 'VERIFY', description: 'Validate response', status: 'queued' },
    { id: 'output', name: 'OUTPUT', description: 'Format response', status: 'queued' },
  ];
}

function getPipelineForType(type: MissionType): PipelineStep[] {
  switch (type) {
    case 'document': return getDocumentPipeline();
    case 'coding': return getCodingPipeline();
    case 'vision': return getVisionPipeline();
    default: return getGeneralPipeline();
  }
}

/* ═══════════════════════════════════════════════════════════
   STORE
   ═══════════════════════════════════════════════════════════ */

export const useMissionStore = create<MissionStore>((set, get) => ({
  missions: [],
  activeMissionId: null,
  missionCounter: 0,
  isReplayMode: false,
  replayStep: 0,

  getActiveMission: () => {
    const state = get();
    return state.missions.find((m) => m.id === state.activeMissionId);
  },

  getMission: (id: string) => {
    return get().missions.find((m) => m.id === id);
  },

  createMission: (command, type = 'general', attachments) => {
    const counter = get().missionCounter + 1;
    const mission: Mission = {
      id: `mission-${Date.now()}`,
      number: counter,
      title: command.length > 60 ? command.substring(0, 57) + '...' : command,
      type,
      status: 'planning',
      command,
      createdAt: Date.now(),
      pipeline: getPipelineForType(type),
      evidence: [],
      trace: [{ timestamp: Date.now(), offset_ms: 0, event: 'Mission created' }],
      attachments,
    };
    set((s) => ({
      missions: [mission, ...s.missions],
      activeMissionId: mission.id,
      missionCounter: counter,
    }));
    return mission;
  },

  setActiveMission: (id) => set({ activeMissionId: id }),

  updateMissionStatus: (id, status) =>
    set((s) => ({
      missions: s.missions.map((m) =>
        m.id === id
          ? {
              ...m,
              status,
              startedAt: status === 'executing' && !m.startedAt ? Date.now() : m.startedAt,
            }
          : m
      ),
    })),

  completeMission: (id, output) =>
    set((s) => ({
      missions: s.missions.map((m) =>
        m.id === id
          ? {
              ...m,
              status: 'completed' as MissionStatus,
              completedAt: Date.now(),
              total_duration_ms: m.startedAt ? Date.now() - m.startedAt : 0,
              output,
            }
          : m
      ),
    })),

  updatePipelineStep: (missionId, stepId, update) =>
    set((s) => ({
      missions: s.missions.map((m) =>
        m.id === missionId
          ? {
              ...m,
              pipeline: m.pipeline.map((step) =>
                step.id === stepId ? { ...step, ...update } : step
              ),
            }
          : m
      ),
    })),

  advancePipeline: (missionId) => {
    const mission = get().getMission(missionId);
    if (!mission) return;
    const nextQueued = mission.pipeline.find((s) => s.status === 'queued');
    if (nextQueued) {
      get().updatePipelineStep(missionId, nextQueued.id, {
        status: 'running',
        startedAt: Date.now(),
      });
    }
  },

  addEvidence: (missionId, evidence) =>
    set((s) => ({
      missions: s.missions.map((m) =>
        m.id === missionId
          ? { ...m, evidence: [...m.evidence, evidence] }
          : m
      ),
    })),

  addTraceEntry: (missionId, event, detail, stepId) => {
    const mission = get().getMission(missionId);
    const baseTime = mission?.createdAt || Date.now();
    set((s) => ({
      missions: s.missions.map((m) =>
        m.id === missionId
          ? {
              ...m,
              trace: [
                ...m.trace,
                {
                  timestamp: Date.now(),
                  offset_ms: Date.now() - baseTime,
                  event,
                  detail,
                  step_id: stepId,
                },
              ],
            }
          : m
      ),
    }));
  },

  startReplay: (missionId) => set({ activeMissionId: missionId, isReplayMode: true, replayStep: 0 }),
  stopReplay: () => set({ isReplayMode: false, replayStep: 0 }),
  setReplayStep: (step) => set({ replayStep: step }),

  /* ─── Demo Mission ─── */
  runDemoMission: () => {
    const store = get();
    const mission = store.createMission(
      'Analyze inspection_report.pdf and prepare an approval note using the relevant internal SOP.',
      'document',
      ['inspection_report.pdf']
    );

    const missionId = mission.id;
    const steps = mission.pipeline;
    const delay = 300;

    // Start executing
    setTimeout(() => {
      store.updateMissionStatus(missionId, 'executing');
      store.addTraceEntry(missionId, 'Mission execution started');
      useAppStore.getState().updateRouting({
        task_type: 'Document Reasoning',
        selected_model: 'Qwen3-14B',
        reason: 'High reasoning requirement for document analysis',
      });
    }, 200);

    // Progress through each pipeline step
    steps.forEach((step, index) => {
      const stepDelay = delay + index * 1200;

      // Start step
      setTimeout(() => {
        const currentStore = useMissionStore.getState();
        currentStore.updatePipelineStep(missionId, step.id, {
          status: 'running',
          startedAt: Date.now(),
        });
        currentStore.addTraceEntry(missionId, `${step.name} started`, step.description, step.id);
      }, stepDelay);

      // Complete step
      setTimeout(() => {
        const currentStore = useMissionStore.getState();
        const duration = 180 + Math.random() * 600;
        const metricsMap: Record<string, Record<string, string | number>> = {
          'ocr': { 'pages_processed': 24, 'text_blocks': 186, 'confidence': '98.2%' },
          'rag': { 'chunks_searched': 42, 'candidates': 8, 'retained': 4 },
          'rerank': { 'input_docs': 8, 'output_docs': 4, 'top_score': 0.94 },
          'reason': { 'input_tokens': 3840, 'output_tokens': 1206, 'model': 'Qwen3-14B' },
          'verify': { 'claims_checked': 6, 'verified': 6, 'confidence': '0.94' },
          'ingest': { 'file_size': '2.4 MB', 'format': 'PDF', 'pages': 24 },
          'understand': { 'task_type': 'document_reasoning', 'complexity': 'high' },
          'output': { 'format': 'DOCX', 'sections': 4, 'size': '186 KB' },
        };

        currentStore.updatePipelineStep(missionId, step.id, {
          status: 'verified',
          completedAt: Date.now(),
          duration_ms: Math.round(duration),
          metrics: metricsMap[step.id] || { 'status': 'complete' },
        });
        currentStore.addTraceEntry(
          missionId,
          `${step.name} verified`,
          `${Math.round(duration)}ms`,
          step.id
        );

        // Add evidence after reasoning step
        if (step.id === 'reason') {
          currentStore.addEvidence(missionId, {
            id: 'ev-1',
            claim: 'Valve V-204 requires immediate replacement due to corrosion exceeding allowable limits.',
            confidence: 0.94,
            sources: [
              { title: 'Inspection Report', location: 'Page 18, Section 4.2', snippet: 'Corrosion depth measured at 3.2mm, exceeding the 2.5mm threshold per ASME B31.3' },
              { title: 'SOP-204', location: 'Section 5.2', snippet: 'Valves exceeding corrosion allowance must be scheduled for replacement within 30 days' },
              { title: 'Maintenance Record MR-4421', location: 'Entry 2024-08-15', snippet: 'Previous inspection noted early-stage pitting on V-204 body' },
            ],
          });
          currentStore.addEvidence(missionId, {
            id: 'ev-2',
            claim: 'Pressure relief system PSV-108 is within certification validity.',
            confidence: 0.97,
            sources: [
              { title: 'Inspection Report', location: 'Page 22, Section 5.1', snippet: 'PSV-108 last certified 2024-03-12, valid until 2025-03-12' },
              { title: 'SOP-108', location: 'Section 3.1', snippet: 'Annual PSV certification required per API 510' },
            ],
          });
        }
      }, stepDelay + 800);
    });

    // Complete mission
    const totalDelay = delay + steps.length * 1200 + 400;
    setTimeout(() => {
      const currentStore = useMissionStore.getState();
      currentStore.completeMission(missionId, {
        type: 'DOCX',
        filename: 'Approval_Note_V204_Inspection.docx',
        content: 'Approval note generated with 6 verified findings and SOP cross-references.',
      });
      currentStore.addTraceEntry(missionId, 'Mission completed', 'DOCX generated successfully');
    }, totalDelay);
  },
}));
