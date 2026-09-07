#include "PromptManager.hpp"
#include <sstream>
#include <iomanip>

namespace sovereign {

FastPromptManager::FastPromptManager(size_t max_total_tokens, size_t output_reserve_tokens)
    : max_input_tokens_(max_total_tokens > output_reserve_tokens ? max_total_tokens - output_reserve_tokens : 7168) {}

size_t FastPromptManager::estimate_tokens(const std::string& text) {
    return (text.size() + 3) / 4;
}

// Simple FNV-1a hash for static prefix identification
static std::string fnv1a_hash(const std::string& str) {
    uint64_t hash = 14695981039346656037ULL;
    for (char c : str) {
        hash ^= static_cast<uint8_t>(c);
        hash *= 1099511628211ULL;
    }
    std::stringstream ss;
    ss << std::hex << std::setw(16) << std::setfill('0') << hash;
    return ss.str();
}

std::string FastPromptManager::assemble_prompt(const PromptBlock& block, std::string& out_static_prefix_hash) const {
    std::ostringstream prefix;
    
    // Priority 5: Deterministic Prompt Order
    // 1. System instructions
    if (!block.system_instructions.empty()) {
        prefix << "[SYSTEM]\n" << block.system_instructions << "\n\n";
    }
    // 2. Agent policy
    if (!block.agent_policy.empty()) {
        prefix << "[POLICY]\n" << block.agent_policy << "\n\n";
    }
    // 3. Tool definitions
    if (!block.tool_definitions.empty()) {
        prefix << "[TOOLS]\n" << block.tool_definitions << "\n\n";
    }
    // 4. Output schema
    if (!block.output_schema.empty()) {
        prefix << "[SCHEMA]\n" << block.output_schema << "\n\n";
    }
    // 5. Static enterprise context
    if (!block.static_enterprise_context.empty()) {
        prefix << "[ENTERPRISE_CONTEXT]\n" << block.static_enterprise_context << "\n\n";
    }

    std::string prefix_str = prefix.str();
    out_static_prefix_hash = fnv1a_hash(prefix_str);

    std::ostringstream full;
    full << prefix_str;

    // Dynamic Suffix:
    // 6. Retrieved context
    if (!block.retrieved_context.empty()) {
        full << "[RETRIEVED_CONTEXT]\n" << block.retrieved_context << "\n\n";
    }
    // 7. Current task
    if (!block.current_task.empty()) {
        full << "[USER_REQUEST]\n" << block.current_task << "\n\n";
    }
    // 8. Current tool result
    if (!block.current_tool_result.empty()) {
        full << "[TOOL_RESULT]\n" << block.current_tool_result << "\n";
    }

    return full.str();
}

} // namespace sovereign
