cmake_minimum_required(VERSION 3.12)
project(EquiFlowEngine CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Define shared library compilation target
add_library(engine SHARED engine.cpp engine.h)

# Set macOS dynamic library suffix and standard name
set_target_properties(engine PROPERTIES
    PREFIX "lib"
    SUFFIX ".dylib"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)
