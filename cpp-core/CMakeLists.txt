cmake_minimum_required(VERSION 3.20)
project(sovereign_core VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

set(SOURCES
    src/Router.cpp
    src/MemoryManager.cpp
    src/PromptManager.cpp
    src/SecurityFirewall.cpp
    src/HardwareManager.cpp
    src/SandboxEnclave.cpp
    src/SimdVectorEngine.cpp
    src/FastScanner.cpp
    src/bindings.cpp
)

add_library(sovereign_core SHARED ${SOURCES})

if(MSVC)
    target_compile_options(sovereign_core PRIVATE /O2 /arch:AVX2 /EHsc /W3)
    target_link_libraries(sovereign_core PRIVATE dxgi)
else()
    target_compile_options(sovereign_core PRIVATE -O3 -mavx2 -mfma -Wall)
    if(WIN32)
        target_link_libraries(sovereign_core PRIVATE dxgi)
    endif()
endif()

set_target_properties(sovereign_core PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/build"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/build"
)
