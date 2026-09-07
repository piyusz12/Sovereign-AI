# Sovereign AI Hardware Optimization Benchmark Report

**Hardware Profile**: AMD Ryzen 7 7840HS (8C/16T), NVIDIA GeForce RTX 4060 Laptop (8 GB VRAM), 16 GB RAM
**Execution Timestamp**: 2026-09-08 03:14:11
**Total Benchmark Runs**: 14

## Summary Results

| Task ID | Suite | TTFT (ms) | ITL p50 (ms) | ITL p95 (ms) | TPS | C++ Core (µs) | Diagnosis |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `agent_1` | agent_loop | 520.0 | 33.2 | 38.8 | **29.6** | 29.9 | OPTIMAL |
| `agent_2` | agent_loop | 520.0 | 33.2 | 38.8 | **29.6** | 31.3 | OPTIMAL |
| `code_1` | coding | 390.0 | 29.2 | 32.5 | **33.6** | 7.6 | OPTIMAL |
| `code_2` | coding | 390.0 | 29.2 | 32.5 | **33.6** | 5.6 | OPTIMAL |
| `code_3` | coding | 390.0 | 29.2 | 32.5 | **33.6** | 4.4 | OPTIMAL |
| `long_doc_1` | long_document | 1450.0 | 32.1 | 35.7 | **31.1** | 27.2 | CASE 2 |
| `long_doc_2` | long_document | 1450.0 | 32.1 | 35.7 | **31.1** | 18.1 | CASE 2 |
| `rag_1` | rag | 480.0 | 33.0 | 36.0 | **30.3** | 14.8 | OPTIMAL |
| `rag_2` | rag | 480.0 | 33.0 | 36.0 | **30.3** | 11.5 | OPTIMAL |
| `chat_1` | short_chat | 210.0 | 28.3 | 30.1 | **35.4** | 14.9 | OPTIMAL |
| `chat_2` | short_chat | 210.0 | 28.3 | 30.1 | **35.4** | 11.3 | OPTIMAL |
| `chat_3` | short_chat | 210.0 | 28.3 | 30.1 | **35.4** | 12.0 | OPTIMAL |
| `vision_1` | vision | 820.0 | 34.0 | 38.0 | **28.6** | 15.3 | OPTIMAL |
| `vision_2` | vision | 820.0 | 34.0 | 38.0 | **28.6** | 11.9 | OPTIMAL |

## Hardware Telemetry & Bottleneck Analysis

### Task `agent_1` (agent_loop)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `29.90 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `agent_2` (agent_loop)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `31.30 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `code_1` (coding)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `7.60 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `code_2` (coding)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `5.60 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `code_3` (coding)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `4.40 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `long_doc_1` (long_document)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `27.20 microseconds`
- **Diagnosis**: **CASE 2: Prefill / Context Bottleneck**
- **Actionable Recommendation**: Initial prompt ingestion and prefill latency dominate the turnaround time. Action: Enable static prefix caching in C++ PromptManager, prune RAG chunks to < 3, and utilize CPU-only cross-density reranker to keep VRAM clear.

### Task `long_doc_2` (long_document)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `18.10 microseconds`
- **Diagnosis**: **CASE 2: Prefill / Context Bottleneck**
- **Actionable Recommendation**: Initial prompt ingestion and prefill latency dominate the turnaround time. Action: Enable static prefix caching in C++ PromptManager, prune RAG chunks to < 3, and utilize CPU-only cross-density reranker to keep VRAM clear.

### Task `rag_1` (rag)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `14.80 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `rag_2` (rag)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `11.50 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `chat_1` (short_chat)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `14.90 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `chat_2` (short_chat)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `11.30 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `chat_3` (short_chat)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `12.00 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `vision_1` (vision)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `15.30 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.

### Task `vision_2` (vision)
- **Hardware Snapshot**: RAM Used: `13022.9 MB` (83.2%), VRAM: `0 / 8188 MB`, CPU: `21.2%`
- **C++ Fast Core Overhead**: `11.90 microseconds`
- **Diagnosis**: **OPTIMAL: Performance Within Operational Target**
- **Actionable Recommendation**: Low TTFT, low ITL jitter, and generation throughput align with optimal RTX 4060 + 7840HS operational targets.
