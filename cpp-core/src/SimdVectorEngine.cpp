#include "SimdVectorEngine.hpp"
#include <immintrin.h>
#include <cmath>
#include <algorithm>
#include <queue>

namespace sovereign {

float FastVectorEngine::dot_product(const float* a, const float* b, int dim) {
    int i = 0;
    __m256 sum256 = _mm256_setzero_ps();

    for (; i + 8 <= dim; i += 8) {
        __m256 va = _mm256_loadu_ps(a + i);
        __m256 vb = _mm256_loadu_ps(b + i);
        sum256 = _mm256_fmadd_ps(va, vb, sum256);
    }

    alignas(32) float buffer[8];
    _mm256_store_ps(buffer, sum256);
    float total = buffer[0] + buffer[1] + buffer[2] + buffer[3] +
                  buffer[4] + buffer[5] + buffer[6] + buffer[7];

    for (; i < dim; ++i) {
        total += a[i] * b[i];
    }

    return total;
}

float FastVectorEngine::l2_norm(const float* a, int dim) {
    float dot = dot_product(a, a, dim);
    return std::sqrt(dot > 0.0f ? dot : 0.0f);
}

float FastVectorEngine::cosine_similarity(const float* a, const float* b, int dim) {
    float norm_a = l2_norm(a, dim);
    float norm_b = l2_norm(b, dim);
    if (norm_a <= 1e-9f || norm_b <= 1e-9f) {
        return 0.0f;
    }
    return dot_product(a, b, dim) / (norm_a * norm_b);
}

std::vector<SearchResult> FastVectorEngine::batch_topk(
    const float* query,
    const float* matrix,
    int num_vectors,
    int dim,
    int top_k
) {
    if (num_vectors <= 0 || top_k <= 0 || dim <= 0 || !query || !matrix) {
        return {};
    }

    float query_norm = l2_norm(query, dim);
    if (query_norm <= 1e-9f) {
        return {};
    }

    // Min-heap of size top_k for streaming top-k selection in O(N log K)
    auto cmp = [](const SearchResult& left, const SearchResult& right) {
        return left.score > right.score;
    };
    std::priority_queue<SearchResult, std::vector<SearchResult>, decltype(cmp)> min_heap(cmp);

    for (int i = 0; i < num_vectors; ++i) {
        const float* vec = matrix + (static_cast<size_t>(i) * dim);
        float vec_norm = l2_norm(vec, dim);
        float sim = (vec_norm > 1e-9f) ? (dot_product(query, vec, dim) / (query_norm * vec_norm)) : 0.0f;

        if (static_cast<int>(min_heap.size()) < top_k) {
            min_heap.push({i, sim});
        } else if (sim > min_heap.top().score) {
            min_heap.pop();
            min_heap.push({i, sim});
        }
    }

    std::vector<SearchResult> results;
    results.reserve(min_heap.size());
    while (!min_heap.empty()) {
        results.push_back(min_heap.top());
        min_heap.pop();
    }
    std::reverse(results.begin(), results.end());
    return results;
}

} // namespace sovereign
