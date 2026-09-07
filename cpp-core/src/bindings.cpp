#include "Router.hpp"
#include "MemoryManager.hpp"
#include "SecurityFirewall.hpp"
#include "PromptManager.hpp"

#include <cstring>
#include <memory>

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

} // extern "C"
