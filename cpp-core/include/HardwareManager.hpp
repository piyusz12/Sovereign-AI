#ifndef SOVEREIGN_HARDWARE_MANAGER_HPP
#define SOVEREIGN_HARDWARE_MANAGER_HPP

#include <cstdint>
#include <string>

namespace sovereign {

struct HardwareInfo {
    uint64_t dedicated_vram_bytes;
    uint64_t shared_vram_bytes;
    uint64_t total_ram_bytes;
    uint64_t available_ram_bytes;
    uint32_t cpu_cores;
    std::wstring gpu_name;
    bool is_discrete_gpu;
};

class FastHardwareManager {
public:
    FastHardwareManager() = default;
    ~FastHardwareManager() = default;

    static HardwareInfo query_hardware();
};

} // namespace sovereign

#endif // SOVEREIGN_HARDWARE_MANAGER_HPP
