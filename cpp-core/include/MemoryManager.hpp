#ifndef SOVEREIGN_MEMORY_MANAGER_HPP
#define SOVEREIGN_MEMORY_MANAGER_HPP

#include <string>
#include <cstdint>

#ifdef _WIN32
#include <windows.h>
#endif

namespace sovereign {

struct MemoryStatus {
    int64_t total_vram_mb;
    int64_t free_vram_mb;
    int64_t used_vram_mb;
    int64_t total_ram_mb;
    const char* active_heavy_model;
    bool single_heavy_model_policy;
};

class FastMemoryManager {
public:
    FastMemoryManager(int64_t total_vram_mb = 8188, int64_t total_ram_mb = 16384);
    ~FastMemoryManager();

    bool can_load(const std::string& model_id, int64_t required_vram_mb);
    bool prepare_switch(const std::string& target_model_id, int64_t required_vram_mb, std::string& out_evict_model);

    void record_loaded(const std::string& model_id, int64_t allocated_vram_mb);
    void record_unloaded(const std::string& model_id);

    MemoryStatus get_status();

private:
    void lock();
    void unlock();

    int64_t total_vram_mb_;
    int64_t total_ram_mb_;
    int64_t current_allocated_vram_mb_;
    std::string active_heavy_model_;

#ifdef _WIN32
    CRITICAL_SECTION cs_;
#endif
};

} // namespace sovereign

#endif // SOVEREIGN_MEMORY_MANAGER_HPP
