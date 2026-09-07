#ifndef SOVEREIGN_SECURITY_FIREWALL_HPP
#define SOVEREIGN_SECURITY_FIREWALL_HPP

#include <string>

namespace sovereign {

enum class ActionPolicy {
    ALLOW = 0,
    REQUIRE_APPROVAL = 1,
    BLOCK = 2
};

struct FirewallDecision {
    ActionPolicy policy;
    const char* action;
    const char* reason;
    bool sovereign_compliant;
};

class FastSecurityFirewall {
public:
    FastSecurityFirewall() = default;
    ~FastSecurityFirewall() = default;

    FirewallDecision evaluate(const std::string& action, const std::string& user_role) const;
};

} // namespace sovereign

#endif // SOVEREIGN_SECURITY_FIREWALL_HPP
