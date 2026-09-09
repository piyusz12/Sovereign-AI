#include "SecurityFirewall.hpp"

namespace sovereign {

FirewallDecision FastSecurityFirewall::evaluate(const std::string& action, const std::string& user_role) const {
    // 1. Strict zero-egress sovereignty checks
    if (action == "send_external" || action == "network_request" || action == "external_connect") {
        return {
            ActionPolicy::BLOCK,
            action.c_str(),
            "SOVEREIGNTY VIOLATION: External network requests are strictly forbidden.",
            false
        };
    }

    // 2. Destructive actions requiring human approval
    if (action == "delete_file" || action == "modify_config" || action == "install_package") {
        return {
            ActionPolicy::REQUIRE_APPROVAL,
            action.c_str(),
            "Destructive or system modification action requires explicit operator approval.",
            true
        };
    }

    // 3. Safe read and execution actions
    if (action == "read_file" || action == "write_file" || action == "list_files" ||
        action == "search_documents" || action == "calculate" || action == "run_python" ||
        action == "create_docx" || action == "create_xlsx" || action == "create_pptx" ||
        action == "inspect_image" || action == "sandbox.execute" || action == "ai.chat" ||
        action == "model.load" || action == "model.unload" || action == "load_model" || action == "unload_model") {
        return {
            ActionPolicy::ALLOW,
            action.c_str(),
            "Operation allowed under sovereign local security policy.",
            true
        };
    }

    // 4. Default fail-closed for unknown actions
    return {
        ActionPolicy::BLOCK,
        action.c_str(),
        "Unknown action blocked by default (fail-closed policy).",
        false
    };
}

} // namespace sovereign
