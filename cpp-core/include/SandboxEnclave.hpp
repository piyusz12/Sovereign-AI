#ifndef SOVEREIGN_SANDBOX_ENCLAVE_HPP
#define SOVEREIGN_SANDBOX_ENCLAVE_HPP

#include <cstdint>
#include <cstddef>

#ifdef _WIN32
#include <windows.h>
#endif

namespace sovereign {

struct SandboxLimits {
    size_t max_memory_bytes;     // Hard limit on committed RAM (e.g. 512 MB)
    uint32_t max_processes;      // Max concurrent processes in job (prevents fork bombs)
    uint32_t cpu_rate_percent;   // Hard CPU cycle quota (e.g. 80 = 80%)
};

struct SandboxStats {
    size_t peak_memory_bytes;
    size_t current_memory_bytes;
    uint64_t total_cpu_time_us;
    uint32_t active_processes;
    bool limit_violation;
};

class FastSandboxEnclave {
public:
    FastSandboxEnclave(const SandboxLimits& limits);
    ~FastSandboxEnclave();

    bool is_valid() const;
    bool assign_process(void* process_handle);
    SandboxStats get_stats() const;
    bool terminate(uint32_t exit_code = 1);
    void close();

    void* get_native_handle() const;

private:
#ifdef _WIN32
    HANDLE job_handle_;
#else
    void* job_handle_;
#endif
    bool limit_violation_;
};

} // namespace sovereign

#endif // SOVEREIGN_SANDBOX_ENCLAVE_HPP
