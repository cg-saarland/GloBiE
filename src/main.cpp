#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <iostream>

#include "interface.h"
#include "bvh.h"
#include "int.h"

template <size_t N, size_t M>
struct BvhNTriM {};

template <>
struct BvhNTriM<8, 4> {
    using Node = Node8;
    using Tri  = Tri4;
};

template <size_t N, size_t M>
class BvhNTriMAdapter {
    struct CostFn {
        static float leaf_cost(size_t count, float area) {
            return count * area;
        }
        static float traversal_cost(float area) {
            return area;
        }
    };

    using BvhBuilder = SplitBvhBuilder<N, CostFn>;
    using Adapter    = BvhNTriMAdapter;
    using Node       = typename BvhNTriM<N, M>::Node;
    using Tri        = typename BvhNTriM<N, M>::Tri;

    std::vector<Node>& nodes_;
    std::vector<Tri>&  tris_;
    BvhBuilder         builder_;

public:
    BvhNTriMAdapter(std::vector<Node>& nodes, std::vector<Tri>& tris)
        : nodes_(nodes), tris_(tris)
    {}

    void build(const std::vector<::Tri>& tris) {
        builder_.build(tris, NodeWriter(*this), LeafWriter(*this, tris), M / 2);
    }

#ifdef STATISTICS
    void print_stats() const override { builder_.print_stats(); }
#endif

private:
    struct NodeWriter {
        Adapter& adapter;

        NodeWriter(Adapter& adapter)
            : adapter(adapter)
        {}

        template <typename BBoxFn>
        int operator() (int parent, int child, const BBox& /*parent_bb*/, size_t count, BBoxFn bboxes) {
            auto& nodes = adapter.nodes_;

            int i = numeric_cast<int>(nodes.size());
            nodes.emplace_back();

            if (parent >= 0 && child >= 0) {
                //std::cout << "parent:" << parent << " child:" << child << " i:" << i << " N:" << N
                //    << " nodes:" << nodes.size() << std::endl;
                assert(parent >= 0 && parent < nodes.size());
                assert(child >= 0 && child < N);
                nodes[parent].child[child] = i + 1;
            }

            assert(count >= 2 && count <= N);

            for (size_t j = 0; j < count; j++) {
                const BBox& bbox = bboxes(j);
                nodes[i].bounds[0][j] = bbox.min.x;
                nodes[i].bounds[2][j] = bbox.min.y;
                nodes[i].bounds[4][j] = bbox.min.z;

                nodes[i].bounds[1][j] = bbox.max.x;
                nodes[i].bounds[3][j] = bbox.max.y;
                nodes[i].bounds[5][j] = bbox.max.z;
            }

            for (size_t j = count; j < N; ++j) {
                nodes[i].bounds[0][j] = std::numeric_limits<float>::infinity();
                nodes[i].bounds[2][j] = std::numeric_limits<float>::infinity();
                nodes[i].bounds[4][j] = std::numeric_limits<float>::infinity();

                nodes[i].bounds[1][j] = -std::numeric_limits<float>::infinity();
                nodes[i].bounds[3][j] = -std::numeric_limits<float>::infinity();
                nodes[i].bounds[5][j] = -std::numeric_limits<float>::infinity();

                nodes[i].child[j] = 0;
            }

            return i;
        }
    };

    struct LeafWriter {
        Adapter& adapter;
        const std::vector<::Tri>& in_tris;

        LeafWriter(Adapter& adapter, const std::vector<::Tri>& in_tris)
            : adapter(adapter)
            , in_tris(in_tris)
        {}

        template <typename RefFn>
        void operator() (int parent, int child, const BBox& /*leaf_bb*/, size_t ref_count, RefFn refs) {
            auto& nodes   = adapter.nodes_;
            auto& tris    = adapter.tris_;

            nodes[parent].child[child] = ~numeric_cast<int>(tris.size());

            // Group triangles by packets of M
            for (size_t i = 0; i < ref_count; i += M) {
                const size_t c = i + M <= ref_count ? M : ref_count - i;

                Tri tri;
                std::memset(&tri, 0, sizeof(Tri));
                for (size_t j = 0; j < c; j++) {
                    const size_t id = refs(i + j);
                    auto& in_tri = in_tris[id];
                    const float3 e1 = in_tri.v0 - in_tri.v1;
                    const float3 e2 = in_tri.v2 - in_tri.v0;
                    const float3 n = cross(e1, e2);
                    tri.v0[0][j] = in_tri.v0.x;
                    tri.v0[1][j] = in_tri.v0.y;
                    tri.v0[2][j] = in_tri.v0.z;

                    tri.e1[0][j] = e1.x;
                    tri.e1[1][j] = e1.y;
                    tri.e1[2][j] = e1.z;

                    tri.e2[0][j] = e2.x;
                    tri.e2[1][j] = e2.y;
                    tri.e2[2][j] = e2.z;

                    tri.n[0][j] = n.x;
                    tri.n[1][j] = n.y;
                    tri.n[2][j] = n.z;

                    tri.prim_id[j] = numeric_cast<int>(id);
                    tri.geom_id[j] = 0;
                }

                for (size_t j = c; j < 4; j++)
                    tri.prim_id[j] = 0xFFFFFFFF;

                tris.emplace_back(tri);
            }
            assert(ref_count > 0);
            tris.back().prim_id[M - 1] |= 0x80000000;
        }
    };
};

template <size_t N, size_t M>
static void build_bvh(const float3* vertices, size_t num_tris,
                      std::vector<typename BvhNTriM<N, M>::Node>& nodes,
                      std::vector<typename BvhNTriM<N, M>::Tri>& tris) {
    BvhNTriMAdapter<N, M> adapter(nodes, tris);
    std::vector<::Tri> in_tris(num_tris);
    for (size_t i = 0; i < num_tris; i++) {
        auto& v0 = vertices[i * 3 + 0];
        auto& v1 = vertices[i * 3 + 1];
        auto& v2 = vertices[i * 3 + 2];
        in_tris[i] = Tri(v0, v1, v2);
    }
    adapter.build(in_tris);
}

namespace py = pybind11;

static constexpr size_t N = 8;
static constexpr size_t M = 4;

PYBIND11_MODULE(ig_rendering_support, m) {
    m.doc() = R"pbdoc(
        Pybind11 example plugin
        -----------------------

        .. currentmodule:: ig_rendering_support

        .. autosummary::
           :toctree: _generate

           add
           subtract
    )pbdoc";

	m.def("bakeAO", [](
        py::array_t<uint8_t, py::array::c_style | py::array::forcecast> data,
        py::array_t<float, py::array::c_style | py::array::forcecast> vertices,
        py::array_t<float, py::array::c_style | py::array::forcecast> normals,
        py::array_t<float, py::array::c_style | py::array::forcecast> texcoord
	) {
		std::cout << "bakeAO called" << std::endl;

		py::ssize_t w = data.shape(0);
		py::ssize_t h = data.shape(1);
        assert(data.shape(2) == 4);
		py::buffer_info d = data.request(true);
		char* dptr = reinterpret_cast<char*>(d.ptr);
		std::cout << "image(" << w << "x" << h << ")" << std::endl;

		py::ssize_t numv = vertices.shape(0);
		py::buffer_info v = vertices.request();
		auto vptr = reinterpret_cast<float3*>(v.ptr);
		std::cout << "vertices for " << numv << " triangles" << std::endl;

        py::ssize_t numn = normals.shape(0);
        py::buffer_info n = normals.request();
        auto nptr = reinterpret_cast<float3*>(n.ptr);
        std::cout << "normals for " << numn << " triangles" << std::endl;

		py::ssize_t numt = texcoord.shape(0);
		py::buffer_info t = texcoord.request();
		auto tptr = reinterpret_cast<float*>(t.ptr);
		std::cout << "texcoord for " << numt << " triangles" << std::endl;

        std::vector<typename BvhNTriM<N, M>::Node> nodes;
        std::vector<typename BvhNTriM<N, M>::Tri> tris;
        build_bvh<N, M>(vptr, numv, nodes, tris);
        
        /* Release GIL before calling into (potentially long-running) C++ code */
        py::gil_scoped_release release;
        
		aomap(
            numeric_cast<int>(w), numeric_cast<int>(h), dptr,
            numeric_cast<int>(numv), reinterpret_cast<float*>(vptr),
            numeric_cast<int>(numn), reinterpret_cast<float*>(nptr),
            numeric_cast<int>(numt), tptr,
            nodes.data(), tris.data());

        /* Acquire GIL before calling Python code */
        py::gil_scoped_acquire acquire;
    }, R"pbdoc(
        Run bakeAO

        Some other explanation about the bakeAO function.
    )pbdoc");



    m.def("alphaBlur", [](
        py::array_t<uint8_t, py::array::c_style | py::array::forcecast> data,
        py::ssize_t width,
        py::ssize_t height
    ) {
        std::cout << "alphaBlur called" << std::endl;

        // py::ssize_t w = data.shape(0);
        // py::ssize_t h = data.shape(1);
        const py::ssize_t nch = 4;
        assert(data.shape(2) == nch);
        py::buffer_info d = data.request(true);
        unsigned char* dptr = reinterpret_cast<unsigned char*>(d.ptr);
        std::cout << "image(" << width << "x" << height << ")" << std::endl;

        py::array_t<unsigned char> result = py::array_t<unsigned char, py::array::c_style | py::array::forcecast>(width * height * nch);
        py::buffer_info r = result.request(true);
        unsigned char* rptr = reinterpret_cast<unsigned char*>(r.ptr);

        int cache[8] = {0,0,0,0,0,0,0,0};

        int centerPixel;
        int centerIdx;
        int leftCol;
        int rightCol;
        int upperRow;
        int lowerRow;
        int avg;
        unsigned char avgResult;
        int lenAvg;

        for (py::ssize_t x = 0; x < width; ++x) {
            for (py::ssize_t y = 0; y < height; ++y) {
                //  pixel raster around center pixel
                //  0 1 2
                //  3 c 4
                //  5 6 7
                centerIdx = x + y * width;
                leftCol = std::max<py::ssize_t>(0, std::min<py::ssize_t>(x - 1, width - 1));
                rightCol = std::max<py::ssize_t>(0, std::min<py::ssize_t>(x + 1, width - 1));
                upperRow = std::max<py::ssize_t>(0, std::min<py::ssize_t>(y - 1, height - 1));
                lowerRow = std::max<py::ssize_t>(0, std::min<py::ssize_t>(y + 1, height - 1));

                cache[0] = (leftCol + upperRow * width) * nch;
                cache[1] = (x + upperRow * width) * nch;
                cache[2] = (rightCol + upperRow * width) * nch;

                cache[3] = (leftCol + y * width) * nch;
                centerPixel = centerIdx * nch;
                cache[4] = (rightCol + y * width) * nch;

                cache[5] = (leftCol + lowerRow * width) * nch;
                cache[6] = (x + lowerRow * width) * nch;
                cache[7] = (rightCol + lowerRow * width) * nch;

                // std::cout << centerPixel << std::endl;
                // std::cout << numeric_cast<int>(dptr[centerPixel + 3]) << std::endl;

                rptr[centerPixel] = dptr[centerPixel];
                rptr[centerPixel + 1] = dptr[centerPixel + 1];
                rptr[centerPixel + 2] = dptr[centerPixel + 2];
                rptr[centerPixel + 3] = 255;

                if (dptr[centerPixel + 3] == 0) {
                    avg = 0;
                    lenAvg = 0;
                    for (int ic = 0; ic < 8; ++ic) {
                        if (dptr[cache[ic] + 3] > 0) {
                            avg += numeric_cast<int>(dptr[cache[ic]]);
                            ++lenAvg;
                        }
                    }

                    if (lenAvg > 0) {
                        avg /= lenAvg;
                        avgResult = numeric_cast<unsigned char>(std::max(std::min(avg, 255), 0));

                        // std::cout << avg << std::endl;

                        rptr[centerPixel] = avgResult;
                        rptr[centerPixel + 1] = avgResult;
                        rptr[centerPixel + 2] = avgResult;
                    }
                    else {
                        rptr[centerPixel] = 255;
                        rptr[centerPixel + 1] = 255;
                        rptr[centerPixel + 2] = 255;
                    }
                }
            }
        }

        return result;

    }, R"pbdoc(
        Run alphaBlur

        Some other explanation about the bakeAO function.
    )pbdoc");

#ifdef VERSION_INFO
    m.attr("__version__") = VERSION_INFO;
#else
    m.attr("__version__") = "dev";
#endif
}
