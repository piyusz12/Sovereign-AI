#ifndef SOVEREIGN_FAST_SCANNER_HPP
#define SOVEREIGN_FAST_SCANNER_HPP

#include <cstddef>
#include <string>
#include <vector>

namespace sovereign {

class FastScanner {
public:
    FastScanner() = default;
    ~FastScanner() = default;

    // Zero-copy search for multiple forbidden patterns in a data buffer
    // Returns number of matches found, populated in out_matched_indices
    static int scan_buffer(
        const char* data,
        size_t length,
        const char** patterns,
        int pattern_count,
        int* out_matched_indices,
        int max_matches
    );
};

} // namespace sovereign

#endif // SOVEREIGN_FAST_SCANNER_HPP
