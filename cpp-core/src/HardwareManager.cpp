#include "HardwareManager.hpp"

#ifdef _WIN32
#include <windows.h>
#include <dxgi.h>
#endif

namespace sovereign {

HardwareInfo FastHardwareManager::query_hardware() {
    HardwareInfo info = {};

#ifdef _WIN32
    // 1. Query System RAM via GlobalMemoryStatusEx
    MEMORYSTATUSEX memStatus;
    memStatus.dwLength = sizeof(MEMORYSTATUSEX);
    if (GlobalMemoryStatusEx(&memStatus)) {
        info.total_ram_bytes = memStatus.ullTotalPhys;
        info.available_ram_bytes = memStatus.ullAvailPhys;
    }

    // 2. Query CPU Cores
    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);
    info.cpu_cores = sysInfo.dwNumberOfProcessors;

    // 3. Query GPU Hardware VRAM via DXGI
    IDXGIFactory* pFactory = nullptr;
    HRESULT hr = CreateDXGIFactory(__uuidof(IDXGIFactory), (void**)&pFactory);
    if (SUCCEEDED(hr) && pFactory != nullptr) {
        IDXGIAdapter* pAdapter = nullptr;
        uint64_t max_dedicated_vram = 0;

        for (UINT i = 0; pFactory->EnumAdapters(i, &pAdapter) != DXGI_ERROR_NOT_FOUND; ++i) {
            DXGI_ADAPTER_DESC desc;
            if (SUCCEEDED(pAdapter->GetDesc(&desc))) {
                // Find primary or highest-capacity discrete GPU (e.g. RTX 4060)
                if (desc.DedicatedVideoMemory > max_dedicated_vram) {
                    max_dedicated_vram = desc.DedicatedVideoMemory;
                    info.dedicated_vram_bytes = desc.DedicatedVideoMemory;
                    info.shared_vram_bytes = desc.SharedSystemMemory;
                    info.gpu_name = desc.Description;
                    info.is_discrete_gpu = (desc.DedicatedVideoMemory > 1024 * 1024 * 512); // >512MB
                }
            }
            pAdapter->Release();
        }
        pFactory->Release();
    }
#endif

    return info;
}

} // namespace sovereign
