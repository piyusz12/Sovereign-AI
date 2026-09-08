import { create } from 'zustand';

export interface HardwareProfile {
  name: string;
  gpu_name: string;
  ram_mb: number;
  vram_mb: number;
}

export interface SystemStatus {
  localOnly: boolean;
  queueDepth: number;
  activeWorkflows: number;
  hardwareProfile: HardwareProfile;
}

export interface NavState {
  isSidebarCollapsed: boolean;
}

export interface AppStore {
  navState: NavState;
  systemStatus: SystemStatus;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  updateSystemStatus: (status: Partial<SystemStatus>) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  navState: {
    isSidebarCollapsed: false,
  },
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
  toggleSidebar: () =>
    set((state) => ({
      navState: {
        ...state.navState,
        isSidebarCollapsed: !state.navState.isSidebarCollapsed,
      },
    })),
  setSidebarCollapsed: (collapsed: boolean) =>
    set((state) => ({
      navState: {
        ...state.navState,
        isSidebarCollapsed: collapsed,
      },
    })),
  updateSystemStatus: (status) =>
    set((state) => ({
      systemStatus: {
        ...state.systemStatus,
        ...status,
      },
    })),
}));
