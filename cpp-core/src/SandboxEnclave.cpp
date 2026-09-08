#include "SandboxEnclave.hpp"

#ifdef _WIN32
#include <windows.h>
#endif

namespace sovereign {

FastSandboxEnclave::FastSandboxEnclave(const SandboxLimits& limits)
    : job_handle_(nullptr), limit_violation_(false) {
#ifdef _WIN32
    // Create an anonymous Job Object
    job_handle_ = CreateJobObjectW(nullptr, nullptr);
    if (!job_handle_) {
        return;
    }

    // Configure Extended Limits: Hard Memory Limit, Active Processes, Kill on Job Close
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION jeli = {};
    jeli.BasicLimitInformation.LimitFlags = 
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE |
        JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION;

    if (limits.max_memory_bytes > 0) {
        jeli.BasicLimitInformation.LimitFlags |= 
            JOB_OBJECT_LIMIT_PROCESS_MEMORY | 
            JOB_OBJECT_LIMIT_JOB_MEMORY;
        jeli.ProcessMemoryLimit = limits.max_memory_bytes;
        jeli.JobMemoryLimit = limits.max_memory_bytes;
    }

    if (limits.max_processes > 0) {
        jeli.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
        jeli.BasicLimitInformation.ActiveProcessLimit = limits.max_processes;
    }

    SetInformationJobObject(
        job_handle_,
        JobObjectExtendedLimitInformation,
        &jeli,
        sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)
    );

    // Configure CPU Rate Control if requested
    if (limits.cpu_rate_percent > 0 && limits.cpu_rate_percent <= 100) {
        JOBOBJECT_CPU_RATE_CONTROL_INFORMATION cpuInfo = {};
        cpuInfo.ControlFlags = JOB_OBJECT_CPU_RATE_CONTROL_ENABLE | JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP;
        cpuInfo.CpuRate = limits.cpu_rate_percent * 100; // In hundredths of a percent (e.g. 5000 = 50%)
        SetInformationJobObject(
            job_handle_,
            JobObjectCpuRateControlInformation,
            &cpuInfo,
            sizeof(JOBOBJECT_CPU_RATE_CONTROL_INFORMATION)
        );
    }
#endif
}

FastSandboxEnclave::~FastSandboxEnclave() {
    close();
}

bool FastSandboxEnclave::is_valid() const {
    return job_handle_ != nullptr;
}

bool FastSandboxEnclave::assign_process(void* process_handle) {
#ifdef _WIN32
    if (!job_handle_ || !process_handle) return false;
    return AssignProcessToJobObject(job_handle_, (HANDLE)process_handle) != 0;
#else
    return false;
#endif
}

SandboxStats FastSandboxEnclave::get_stats() const {
    SandboxStats stats = {};
#ifdef _WIN32
    if (!job_handle_) return stats;

    JOBOBJECT_EXTENDED_LIMIT_INFORMATION jeli = {};
    if (QueryInformationJobObject(job_handle_, JobObjectExtendedLimitInformation, &jeli, sizeof(jeli), nullptr)) {
        stats.peak_memory_bytes = jeli.PeakJobMemoryUsed;
    }

    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION jbai = {};
    if (QueryInformationJobObject(job_handle_, JobObjectBasicAccountingInformation, &jbai, sizeof(jbai), nullptr)) {
        stats.active_processes = jbai.ActiveProcesses;
        stats.total_cpu_time_us = (jbai.TotalKernelTime.QuadPart + jbai.TotalUserTime.QuadPart) / 10;
    }
#endif
    return stats;
}

bool FastSandboxEnclave::terminate(uint32_t exit_code) {
#ifdef _WIN32
    if (!job_handle_) return false;
    return TerminateJobObject(job_handle_, exit_code) != 0;
#else
    return false;
#endif
}

void FastSandboxEnclave::close() {
#ifdef _WIN32
    if (job_handle_) {
        CloseHandle(job_handle_);
        job_handle_ = nullptr;
    }
#endif
}

void* FastSandboxEnclave::get_native_handle() const {
    return job_handle_;
}

} // namespace sovereign
