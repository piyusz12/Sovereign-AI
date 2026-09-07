#ifndef SOVEREIGN_PROMPT_MANAGER_HPP
#define SOVEREIGN_PROMPT_MANAGER_HPP

#include <string>
#include <vector>

namespace sovereign {

struct PromptBlock {
    std::string system_instructions;
    std::string agent_policy;
    std::string tool_definitions;
    std::string output_schema;
    std::string static_enterprise_context;
    std::string retrieved_context;
    std::string current_task;
    std::string current_tool_result;
};

class FastPromptManager {
public:
    FastPromptManager(size_t max_total_tokens = 8192, size_t output_reserve_tokens = 1024);
    ~FastPromptManager() = default;

    // Assembles prompt in strict deterministic order:
    // 1. System instructions
    // 2. Agent policy
    // 3. Tool definitions
    // 4. Output schema
    // 5. Static enterprise context
    // 6. Retrieved context
    // 7. Current task
    // 8. Current tool result
    std::string assemble_prompt(const PromptBlock& block, std::string& out_static_prefix_hash) const;

    // Token estimation (conservative ~4 chars per token)
    static size_t estimate_tokens(const std::string& text);

private:
    size_t max_input_tokens_;
};

} // namespace sovereign

#endif // SOVEREIGN_PROMPT_MANAGER_HPP
