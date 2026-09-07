#ifndef SOVEREIGN_ROUTER_HPP
#define SOVEREIGN_ROUTER_HPP

#include <string>
#include <vector>

namespace sovereign {

enum class TaskType {
    REASONING = 0,
    CODING = 1,
    VISION = 2,
    DOCUMENT_REASONING = 3,
    DATA_ANALYSIS = 4,
    GENERAL = 5
};

struct RouteDecision {
    TaskType task_type;
    const char* task_name;
    const char* recommended_model;
    float confidence;
    const char* reason;
};

class FastRouter {
public:
    FastRouter();
    ~FastRouter() = default;

    RouteDecision classify(const std::string& input, bool has_image = false) const;

private:
    static bool contains_ignore_case(const std::string& haystack, const char* needle);
};

} // namespace sovereign

#endif // SOVEREIGN_ROUTER_HPP
