#include "FastScanner.hpp"
#include <cstring>
#include <string_view>

namespace sovereign {

int FastScanner::scan_buffer(
    const char* data,
    size_t length,
    const char** patterns,
    int pattern_count,
    int* out_matched_indices,
    int max_matches
) {
    if (!data || length == 0 || !patterns || pattern_count <= 0 || !out_matched_indices || max_matches <= 0) {
        return 0;
    }

    std::string_view text(data, length);
    int match_count = 0;

    for (int p = 0; p < pattern_count; ++p) {
        if (!patterns[p]) continue;
        std::string_view pat(patterns[p]);
        if (pat.empty()) continue;

        if (text.find(pat) != std::string_view::npos) {
            out_matched_indices[match_count++] = p;
            if (match_count >= max_matches) {
                break;
            }
        }
    }

    return match_count;
}

} // namespace sovereign
