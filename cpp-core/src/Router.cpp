#include "Router.hpp"
#include <algorithm>
#include <cctype>
#include <cstring>

namespace sovereign {

FastRouter::FastRouter() = default;

bool FastRouter::contains_ignore_case(const std::string& haystack, const char* needle) {
    if (!needle || !needle[0]) return true;
    size_t needle_len = std::strlen(needle);
    if (haystack.size() < needle_len) return false;

    auto it = std::search(
        haystack.begin(), haystack.end(),
        needle, needle + needle_len,
        [](char ch1, char ch2) {
            return std::tolower(static_cast<unsigned char>(ch1)) ==
                   std::tolower(static_cast<unsigned char>(ch2));
        }
    );
    return it != haystack.end();
}

RouteDecision FastRouter::classify(const std::string& input, bool has_image) const {
    if (has_image) {
        return {
            TaskType::VISION,
            "vision",
            "qwen3-vl-8b",
            0.95f,
            "Image attached to request"
        };
    }

    // Coding keywords
    static const char* code_keywords[] = {
        "def ", "class ", "function", "write code", "python", "javascript",
        "typescript", "rust", "c++", "cpp", "java", "sql", "bug", "traceback",
        "error in line", "refactor", "unit test", "pytest", "implement", "script",
        "algorithm", "regex", "json parse", "api endpoint", "git commit"
    };
    for (const auto* kw : code_keywords) {
        if (contains_ignore_case(input, kw)) {
            return {
                TaskType::CODING,
                "coding",
                "qwen2.5-coder-7b",
                0.90f,
                "Strong coding intent detected"
            };
        }
    }

    // Vision keywords
    static const char* vision_keywords[] = {
        "inspect this image", "look at this diagram", "p&id", "schematic",
        "ocr", "chart", "plot", "screenshot", "visual", "valve in drawing"
    };
    for (const auto* kw : vision_keywords) {
        if (contains_ignore_case(input, kw)) {
            return {
                TaskType::VISION,
                "vision",
                "qwen3-vl-8b",
                0.85f,
                "Visual inspection keyword pattern"
            };
        }
    }

    // Document reasoning keywords
    static const char* doc_keywords[] = {
        "summarize document", "according to the manual", "inspection report",
        "sop", "policy", "purchase order", "invoice", "specification",
        "search documents", "rag", "find in files", "contract terms"
    };
    for (const auto* kw : doc_keywords) {
        if (contains_ignore_case(input, kw)) {
            return {
                TaskType::DOCUMENT_REASONING,
                "document_reasoning",
                "qwen3-14b",
                0.85f,
                "Enterprise document reasoning query"
            };
        }
    }

    // Data analysis keywords
    static const char* data_keywords[] = {
        "pandas", "dataframe", "csv", "excel", "xlsx", "aggregate", "trend",
        "forecast", "statistics", "dataset", "correlation", "variance"
    };
    for (const auto* kw : data_keywords) {
        if (contains_ignore_case(input, kw)) {
            return {
                TaskType::DATA_ANALYSIS,
                "data_analysis",
                "qwen2.5-coder-7b",
                0.80f,
                "Data analysis / tabular processing"
            };
        }
    }

    // Default to heavy reasoning
    return {
        TaskType::REASONING,
        "reasoning",
        "qwen3-14b",
        0.70f,
        "Default multi-step reasoning"
    };
}

} // namespace sovereign
