#include "MemoryManager.hpp"
#include <algorithm>

namespace sovereign {

FastMemoryManager::FastMemoryManager(int64_t total_vram_mb, int64_t total_ram_mb)
    : total_vram_mb_(total_vram_mb),
      total_ram_mb_(total_ram_mb),
      current_allocated_vram_mb_(0),
      active_heavy_model_("") {
#ifdef _WIN32
    InitializeCriticalSection(&cs_);
#endif
}

FastMemoryManager::~FastMemoryManager() {
#ifdef _WIN32
    DeleteCriticalSection(&cs_);
#endif
}

void FastMemoryManager::lock() {
#ifdef _WIN32
    EnterCriticalSection(&cs_);
#endif
}

void FastMemoryManager::unlock() {
#ifdef _WIN32
    LeaveCriticalSection(&cs_);
#endif
}

bool FastMemoryManager::can_load(const std::string& model_id, int64_t required_vram_mb) {
    lock();
    if (active_heavy_model_ == model_id) {
        unlock();
        return true;
    }
    int64_t max_allowed = total_vram_mb_ - 1024;
    bool allowed = (required_vram_mb <= max_allowed);
    unlock();
    return allowed;
}

bool FastMemoryManager::prepare_switch(const std::string& target_model_id, int64_t required_vram_mb, std::string& out_evict_model) {
    lock();
    out_evict_model.clear();

    if (active_heavy_model_ == target_model_id) {
        unlock();
        return true;
    }

    if (!active_heavy_model_.empty()) {
        out_evict_model = active_heavy_model_;
    }

    int64_t max_allowed = total_vram_mb_ - 1024;
    bool allowed = (required_vram_mb <= max_allowed);
    unlock();
    return allowed;
}

void FastMemoryManager::record_loaded(const std::string& model_id, int64_t allocated_vram_mb) {
    lock();
    active_heavy_model_ = model_id;
    current_allocated_vram_mb_ = allocated_vram_mb;
    unlock();
}

void FastMemoryManager::record_unloaded(const std::string& model_id) {
    lock();
    if (active_heavy_model_ == model_id) {
        active_heavy_model_.clear();
        current_allocated_vram_mb_ = 0;
    }
    unlock();
}

MemoryStatus FastMemoryManager::get_status() {
    lock();
    int64_t free_mb = std::max<int64_t>(0, total_vram_mb_ - current_allocated_vram_mb_);
    MemoryStatus status = {
        total_vram_mb_,
        free_mb,
        current_allocated_vram_mb_,
        total_ram_mb_,
        active_heavy_model_.c_str(),
        true
    };
    unlock();
    return status;
}

} // namespace sovereign
