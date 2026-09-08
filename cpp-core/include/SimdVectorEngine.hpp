#ifndef SOVEREIGN_SIMD_VECTOR_ENGINE_HPP
#define SOVEREIGN_SIMD_VECTOR_ENGINE_HPP

#include <cstddef>
#include <vector>

namespace sovereign {

struct SearchResult {
    int index;
    float score;
};

class FastVectorEngine {
public:
    FastVectorEngine() = default;
    ~FastVectorEngine() = default;

    // SIMD AVX2 Dot Product of two float arrays of given dimension
    static float dot_product(const float* a, const float* b, int dim);

    // SIMD AVX2 L2 Norm
    static float l2_norm(const float* a, int dim);

    // SIMD AVX2 Cosine Similarity
    static float cosine_similarity(const float* a, const float* b, int dim);

    // Batch top-K similarity search against a row-major matrix of vectors [num_vectors x dim]
    static std::vector<SearchResult> batch_topk(
        const float* query,
        const float* matrix,
        int num_vectors,
        int dim,
        int top_k
    );
};

} // namespace sovereign

#endif // SOVEREIGN_SIMD_VECTOR_ENGINE_HPP
