#if __has_include("Router.hpp")
#include "Router.hpp"
#include "MemoryManager.hpp"
#include "SecurityFirewall.hpp"
#include "PromptManager.hpp"
#include "HardwareManager.hpp"
#include "SandboxEnclave.hpp"
#include "SimdVectorEngine.hpp"
#include "FastScanner.hpp"
#else
#include "../include/Router.hpp"
#include "../include/MemoryManager.hpp"
#include "../include/SecurityFirewall.hpp"
#include "../include/PromptManager.hpp"
#include "../include/HardwareManager.hpp"
#include "../include/SandboxEnclave.hpp"
#include "../include/SimdVectorEngine.hpp"
#include "../include/FastScanner.hpp"
#endif

#include <cstdint>
#include <cstring>
#include <cwchar>
#include <memory>
#include <string>

#if defined(_WIN32) || defined(__CYGWIN__)
#define SOVEREIGN_EXPORT __declspec(dllexport)
#else
#define SOVEREIGN_EXPORT __attribute__((visibility("default")))
#endif

extern "C" {

static std::unique_ptr<sovereign::FastRouter> g_router;
static std::unique_ptr<sovereign::FastMemoryManager> g_memory_manager;
static std::unique_ptr<sovereign::FastSecurityFirewall> g_firewall;
static std::unique_ptr<sovereign::FastPromptManager> g_prompt_manager;

// Initialization
SOVEREIGN_EXPORT int sovereign_core_init() {
    try {
        g_router = std::make_unique<sovereign::FastRouter>();
        g_memory_manager = std::make_unique<sovereign::FastMemoryManager>(8188, 16384);
        g_firewall = std::make_unique<sovereign::FastSecurityFirewall>();
        g_prompt_manager = std::make_unique<sovereign::FastPromptManager>(8192, 1024);
        return 0; // Success
    } catch (...) {
        return -1;
    }
}

// Router API
SOVEREIGN_EXPORT int sovereign_router_classify(
    const char* input,
    int has_image,
    int* out_task_type,
    char* out_model_buf,
    int model_buf_len,
    float* out_confidence
) {
    if (!g_router || !input) return -1;
    auto decision = g_router->classify(input, has_image != 0);
    if (out_task_type) *out_task_type = static_cast<int>(decision.task_type);
    if (out_confidence) *out_confidence = decision.confidence;
    if (out_model_buf && model_buf_len > 0) {
        std::strncpy(out_model_buf, decision.recommended_model, model_buf_len - 1);
        out_model_buf[model_buf_len - 1] = '\0';
    }
    return 0;
}

// Memory Manager API
SOVEREIGN_EXPORT int sovereign_memory_can_load(const char* model_id, int64_t required_vram_mb) {
    if (!g_memory_manager || !model_id) return 0;
    return g_memory_manager->can_load(model_id, required_vram_mb) ? 1 : 0;
}

SOVEREIGN_EXPORT int sovereign_memory_prepare_switch(
    const char* target_model_id,
    int64_t required_vram_mb,
    char* out_evict_buf,
    int evict_buf_len
) {
    if (!g_memory_manager || !target_model_id) return 0;
    std::string evict_model;
    bool allowed = g_memory_manager->prepare_switch(target_model_id, required_vram_mb, evict_model);
    if (out_evict_buf && evict_buf_len > 0) {
        std::strncpy(out_evict_buf, evict_model.c_str(), evict_buf_len - 1);
        out_evict_buf[evict_buf_len - 1] = '\0';
    }
    return allowed ? 1 : 0;
}

SOVEREIGN_EXPORT void sovereign_memory_record_loaded(const char* model_id, int64_t allocated_vram_mb) {
    if (g_memory_manager && model_id) {
        g_memory_manager->record_loaded(model_id, allocated_vram_mb);
    }
}

SOVEREIGN_EXPORT void sovereign_memory_record_unloaded(const char* model_id) {
    if (g_memory_manager && model_id) {
        g_memory_manager->record_unloaded(model_id);
    }
}

// Security Firewall API
SOVEREIGN_EXPORT int sovereign_firewall_evaluate(
    const char* action,
    const char* user_role,
    int* out_policy,
    char* out_reason_buf,
    int reason_buf_len
) {
    if (!g_firewall || !action) return -1;
    auto decision = g_firewall->evaluate(action, user_role ? user_role : "engineering");
    if (out_policy) *out_policy = static_cast<int>(decision.policy);
    if (out_reason_buf && reason_buf_len > 0) {
        std::strncpy(out_reason_buf, decision.reason, reason_buf_len - 1);
        out_reason_buf[reason_buf_len - 1] = '\0';
    }
    return decision.sovereign_compliant ? 1 : 0;
}

// Prompt Manager API
SOVEREIGN_EXPORT size_t sovereign_prompt_estimate_tokens(const char* text) {
    if (!text) return 0;
    return sovereign::FastPromptManager::estimate_tokens(text);
}

// ─────────────────────────────────────────────────────────────────────────────
// Hardware Control API (Direct DXGI & Win32 Interrogation)
// ─────────────────────────────────────────────────────────────────────────────

SOVEREIGN_EXPORT int sovereign_hardware_query(
    uint64_t* out_vram_bytes,
    uint64_t* out_shared_vram_bytes,
    uint64_t* out_total_ram_bytes,
    uint64_t* out_avail_ram_bytes,
    uint32_t* out_cores,
    wchar_t* out_name_buf,
    int name_buf_len
) {
    try {
        auto info = sovereign::FastHardwareManager::query_hardware();
        if (out_vram_bytes) *out_vram_bytes = info.dedicated_vram_bytes;
        if (out_shared_vram_bytes) *out_shared_vram_bytes = info.shared_vram_bytes;
        if (out_total_ram_bytes) *out_total_ram_bytes = info.total_ram_bytes;
        if (out_avail_ram_bytes) *out_avail_ram_bytes = info.available_ram_bytes;
        if (out_cores) *out_cores = info.cpu_cores;

        if (out_name_buf && name_buf_len > 0) {
            std::wcsncpy(out_name_buf, info.gpu_name.c_str(), name_buf_len - 1);
            out_name_buf[name_buf_len - 1] = L'\0';
        }
        return 0; // Success
    } catch (...) {
        return -1;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Sandbox Enclave API (Win32 Job Objects Hardware Containment)
// ─────────────────────────────────────────────────────────────────────────────

SOVEREIGN_EXPORT void* sovereign_sandbox_create(
    size_t max_memory_bytes,
    uint32_t max_processes,
    uint32_t cpu_rate_percent
) {
    try {
        sovereign::SandboxLimits limits = {
            max_memory_bytes,
            max_processes,
            cpu_rate_percent
        };
        auto enclave = new sovereign::FastSandboxEnclave(limits);
        if (!enclave->is_valid()) {
            delete enclave;
            return nullptr;
        }
        return static_cast<void*>(enclave);
    } catch (...) {
        return nullptr;
    }
}

SOVEREIGN_EXPORT int sovereign_sandbox_assign(void* enclave_handle, void* process_handle) {
    if (!enclave_handle || !process_handle) return 0;
    auto enclave = static_cast<sovereign::FastSandboxEnclave*>(enclave_handle);
    return enclave->assign_process(process_handle) ? 1 : 0;
}

SOVEREIGN_EXPORT int sovereign_sandbox_get_stats(
    void* enclave_handle,
    size_t* out_peak_memory,
    uint64_t* out_cpu_time_us,
    uint32_t* out_active_processes
) {
    if (!enclave_handle) return -1;
    auto enclave = static_cast<sovereign::FastSandboxEnclave*>(enclave_handle);
    auto stats = enclave->get_stats();
    if (out_peak_memory) *out_peak_memory = stats.peak_memory_bytes;
    if (out_cpu_time_us) *out_cpu_time_us = stats.total_cpu_time_us;
    if (out_active_processes) *out_active_processes = stats.active_processes;
    return 0;
}

SOVEREIGN_EXPORT int sovereign_sandbox_terminate(void* enclave_handle, uint32_t exit_code) {
    if (!enclave_handle) return 0;
    auto enclave = static_cast<sovereign::FastSandboxEnclave*>(enclave_handle);
    return enclave->terminate(exit_code) ? 1 : 0;
}

SOVEREIGN_EXPORT void sovereign_sandbox_close(void* enclave_handle) {
    if (!enclave_handle) return;
    auto enclave = static_cast<sovereign::FastSandboxEnclave*>(enclave_handle);
    delete enclave;
}

// ─────────────────────────────────────────────────────────────────────────────
// AVX2 SIMD Vector Similarity Engine API
// ─────────────────────────────────────────────────────────────────────────────

SOVEREIGN_EXPORT float sovereign_simd_dot(const float* a, const float* b, int dim) {
    if (!a || !b || dim <= 0) return 0.0f;
    return sovereign::FastVectorEngine::dot_product(a, b, dim);
}

SOVEREIGN_EXPORT float sovereign_simd_cosine(const float* a, const float* b, int dim) {
    if (!a || !b || dim <= 0) return 0.0f;
    return sovereign::FastVectorEngine::cosine_similarity(a, b, dim);
}

SOVEREIGN_EXPORT int sovereign_simd_batch_topk(
    const float* query,
    const float* matrix,
    int num_vectors,
    int dim,
    int top_k,
    int* out_indices,
    float* out_scores
) {
    if (!query || !matrix || !out_indices || !out_scores || num_vectors <= 0 || dim <= 0 || top_k <= 0) {
        return 0;
    }

    auto results = sovereign::FastVectorEngine::batch_topk(query, matrix, num_vectors, dim, top_k);
    int count = static_cast<int>(results.size());
    for (int i = 0; i < count; ++i) {
        out_indices[i] = results[i].index;
        out_scores[i] = results[i].score;
    }
    return count;
}

// ─────────────────────────────────────────────────────────────────────────────
// Fast Multi-Pattern Memory Scanner API
// ─────────────────────────────────────────────────────────────────────────────

SOVEREIGN_EXPORT int sovereign_fast_scan(
    const char* data,
    size_t length,
    const char** patterns,
    int pattern_count,
    int* out_matched_indices,
    int max_matches
) {
    return sovereign::FastScanner::scan_buffer(
        data,
        length,
        patterns,
        pattern_count,
        out_matched_indices,
        max_matches
    );
}

} // extern "C"
