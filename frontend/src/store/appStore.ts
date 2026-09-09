/**
 * Sovereign Command Deck — Core Application Store
 *
 * Manages system telemetry, UI state, and trust metrics.
 * Mission-specific state lives in missionStore.ts.
 */

import { create } from 'zustand';

/* ═══════════════════════════════════════════════════════════
   TYPE DEFINITIONS
   ═══════════════════════════════════════════════════════════ */

export interface HardwareProfile {
  name: string;
  gpu_name: string;
  ram_mb: number;
  vram_mb: number;
}

export interface SystemTelemetry {
  gpu_percent: number;
  vram_used_mb: number;
  vram_total_mb: number;
  ram_used_mb: number;
  ram_total_mb: number;
  ttft_ms: number;
  itl_ms: number;
  tokens_per_sec: number;
  context_used: number;
  context_max: number;
}

export interface TrustMetrics {
  is_local: boolean;
  external_connections: number;
  dns_requests: number;
  cloud_api_calls: number;
  data_egress_mb: number;
  local_models: number;
  local_documents: number;
  active_policies: number;
}

export interface ModelRouting {
  task_type: string;
  selected_model: string;
  reason: string;
  available_models: Array<{
    id: string;
    name: string;
    role: string;
    loaded: boolean;
    vram_mb: number;
    quantization?: string;
  }>;
}

export interface UIState {
  rightPanelVisible: boolean;
  leftPanelCollapsed: boolean;
  activeView: 'command' | 'missions' | 'knowledge' | 'artifacts' | 'reasoning' | 'coding' | 'vision' | 'trust' | 'system' | 'attestation' | 'mcp' | 'mantic' | 'cyberscan' | 'rag';
}

export interface SystemStatus {
  localOnly: boolean;
  queueDepth: number;
  activeWorkflows: number;
  hardwareProfile: HardwareProfile;
}

export interface AppStore {
  // System
  telemetry: SystemTelemetry;
  trust: TrustMetrics;
  routing: ModelRouting;
  hardware: HardwareProfile;
  queueDepth: number;
  systemStatus: SystemStatus;

  // UI
  ui: UIState;

  // Auth
  currentUser: { username: string; role: string; department: string } | null;
  availableWorkflows: string[];

  // Actions
  updateTelemetry: (data: Partial<SystemTelemetry>) => void;
  updateTrust: (data: Partial<TrustMetrics>) => void;
  updateRouting: (data: Partial<ModelRouting>) => void;
  updateHardware: (data: Partial<HardwareProfile>) => void;
  updateSystemStatus: (status: Partial<SystemStatus>) => void;
  setQueueDepth: (depth: number) => void;
  setActiveView: (view: UIState['activeView']) => void;
  toggleRightPanel: () => void;
  toggleLeftPanel: () => void;
  setCurrentUser: (user: AppStore['currentUser']) => void;
  setAvailableWorkflows: (workflows: string[]) => void;
  setModelLoaded: (modelId: string, loaded: boolean) => void;
  setSelectedModel: (modelName: string) => void;
}

/* ═══════════════════════════════════════════════════════════
   STORE
   ═══════════════════════════════════════════════════════════ */

export const useAppStore = create<AppStore>((set) => ({
  telemetry: {
    gpu_percent: 61,
    vram_used_mb: 6348,
    vram_total_mb: 8192,
    ram_used_mb: 11674,
    ram_total_mb: 16384,
    ttft_ms: 420,
    itl_ms: 51,
    tokens_per_sec: 31.6,
    context_used: 5200,
    context_max: 16384,
  },

  trust: {
    is_local: true,
    external_connections: 0,
    dns_requests: 0,
    cloud_api_calls: 0,
    data_egress_mb: 0,
    local_models: 3,
    local_documents: 128,
    active_policies: 17,
  },

  routing: {
    task_type: 'Idle',
    selected_model: 'Qwen3-14B',
    reason: 'Awaiting mission',
    available_models: [
      { id: 'qwen3-14b', name: 'Qwen3-14B', role: 'reasoning', loaded: true, vram_mb: 5200, quantization: '4-bit' },
      { id: 'qwen2.5-coder-7b', name: 'Qwen2.5-Coder-7B', role: 'coding', loaded: false, vram_mb: 4700, quantization: '4-bit' },
      { id: 'qwen3-vl-8b', name: 'Qwen3-VL-8B', role: 'vision', loaded: false, vram_mb: 7800, quantization: '4-bit' },
    ],
  },

  hardware: {
    name: 'NVIDIA RTX 4060 Laptop',
    gpu_name: 'RTX 4060 (8GB)',
    ram_mb: 16384,
    vram_mb: 8192,
  },

  queueDepth: 0,

  systemStatus: {
    localOnly: true,
    queueDepth: 0,
    activeWorkflows: 0,
    hardwareProfile: {
      name: 'NVIDIA RTX 4060 Laptop',
      gpu_name: 'RTX 4060 (8GB)',
      ram_mb: 16384,
      vram_mb: 8192,
    },
  },

  ui: {
    rightPanelVisible: true,
    leftPanelCollapsed: false,
    activeView: 'command',
  },

  currentUser: null,

  availableWorkflows: [],

  // Actions
  updateTelemetry: (data) =>
    set((s) => ({ telemetry: { ...s.telemetry, ...data } })),

  updateTrust: (data) =>
    set((s) => ({ trust: { ...s.trust, ...data } })),

  updateRouting: (data) =>
    set((s) => ({ routing: { ...s.routing, ...data } })),

  updateHardware: (data) =>
    set((s) => ({ hardware: { ...s.hardware, ...data } })),

  updateSystemStatus: (status) =>
    set((s) => ({
      systemStatus: {
        ...s.systemStatus,
        ...status,
      },
      queueDepth: status.queueDepth !== undefined ? status.queueDepth : s.queueDepth,
      hardware: status.hardwareProfile ? { ...s.hardware, ...status.hardwareProfile } : s.hardware,
    })),

  setQueueDepth: (depth) => set({ queueDepth: depth }),

  setActiveView: (view) =>
    set((s) => ({ ui: { ...s.ui, activeView: view } })),

  toggleRightPanel: () =>
    set((s) => ({ ui: { ...s.ui, rightPanelVisible: !s.ui.rightPanelVisible } })),

  toggleLeftPanel: () =>
    set((s) => ({ ui: { ...s.ui, leftPanelCollapsed: !s.ui.leftPanelCollapsed } })),

  setCurrentUser: (user) => set({ currentUser: user }),

  setAvailableWorkflows: (workflows) => set({ availableWorkflows: workflows }),

  setModelLoaded: (modelId, loaded) =>
    set((s) => ({
      routing: {
        ...s.routing,
        available_models: s.routing.available_models.map((m) =>
          m.id === modelId ||
          m.name.toLowerCase() === modelId.toLowerCase() ||
          m.id.toLowerCase().includes(modelId.toLowerCase()) ||
          modelId.toLowerCase().includes(m.id.toLowerCase())
            ? { ...m, loaded }
            : m
        ),
      },
    })),

  setSelectedModel: (modelName) =>
    set((s) => ({
      routing: {
        ...s.routing,
        selected_model: modelName,
      },
      ui: {
        ...s.ui,
        activeView: 'system',
      },
    })),
}));
