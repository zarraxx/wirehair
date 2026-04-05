cmake_minimum_required(VERSION 3.20)

if(POLICY CMP0077)
    cmake_policy(SET CMP0077 NEW)
endif()

project(wirehair_all_os LANGUAGES C CXX)

include(CTest)

set(WIREHAIR_SOURCE_DIR "${CMAKE_CURRENT_LIST_DIR}/.." CACHE PATH "Path to the upstream wirehair source tree")
option(WIREHAIR_ALL_OS_BUILD_TESTS "Build upstream wirehair test targets" OFF)
option(WIREHAIR_ALL_OS_MARCH_NATIVE "Enable -march=native in the upstream project" OFF)
option(WIREHAIR_ALL_OS_BUILD_PYTHON_CTYPES_TEST "Register the Python ctypes smoke test with CTest when runnable" ON)

if(NOT EXISTS "${WIREHAIR_SOURCE_DIR}/wirehair.cpp")
    message(FATAL_ERROR "WIREHAIR_SOURCE_DIR must point at the upstream wirehair repo root: ${WIREHAIR_SOURCE_DIR}")
endif()

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

set(BUILD_SHARED_LIBS ON CACHE BOOL "Build wirehair as a shared library" FORCE)
set(BUILD_TESTS "${WIREHAIR_ALL_OS_BUILD_TESTS}" CACHE BOOL "Build upstream tests" FORCE)
set(MARCH_NATIVE "${WIREHAIR_ALL_OS_MARCH_NATIVE}" CACHE BOOL "Enable -march=native" FORCE)

add_subdirectory("${WIREHAIR_SOURCE_DIR}" "${CMAKE_BINARY_DIR}/wirehair-upstream")

if(NOT TARGET wirehair)
    message(FATAL_ERROR "Upstream project did not define the expected wirehair target")
endif()

set_target_properties(wirehair PROPERTIES
    OUTPUT_NAME wirehair
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/stage/bin"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/stage/lib"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/stage/lib"
)

if(CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64" OR CMAKE_SYSTEM_PROCESSOR STREQUAL "AMD64")
    if(NOT MSVC)
        target_compile_options(wirehair PRIVATE -mssse3)
    endif()
endif()

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    target_compile_options(wirehair PRIVATE -Wno-nullability-completeness)
    target_link_options(wirehair PRIVATE -Wno-nullability-completeness)
endif()

if(WIN32)
    set_target_properties(wirehair PROPERTIES PREFIX "")
endif()

set(_wirehair_host_system "${CMAKE_HOST_SYSTEM_NAME}")
set(_wirehair_target_system "${CMAKE_SYSTEM_NAME}")
set(_wirehair_host_processor "${CMAKE_HOST_SYSTEM_PROCESSOR}")
set(_wirehair_target_processor "${CMAKE_SYSTEM_PROCESSOR}")

string(TOLOWER "${_wirehair_host_processor}" _wirehair_host_processor)
string(TOLOWER "${_wirehair_target_processor}" _wirehair_target_processor)

if(_wirehair_host_processor STREQUAL "amd64")
    set(_wirehair_host_processor "x86_64")
elseif(_wirehair_host_processor STREQUAL "arm64")
    set(_wirehair_host_processor "aarch64")
endif()

if(_wirehair_target_processor STREQUAL "amd64")
    set(_wirehair_target_processor "x86_64")
elseif(_wirehair_target_processor STREQUAL "arm64")
    set(_wirehair_target_processor "aarch64")
endif()

set(_wirehair_can_run_local_tests OFF)
if(_wirehair_host_system STREQUAL _wirehair_target_system AND _wirehair_host_processor STREQUAL _wirehair_target_processor)
    set(_wirehair_can_run_local_tests ON)
endif()

if(BUILD_TESTING AND WIREHAIR_ALL_OS_BUILD_PYTHON_CTYPES_TEST AND _wirehair_can_run_local_tests)
    find_package(Python3 COMPONENTS Interpreter QUIET)
    if(Python3_Interpreter_FOUND)
        add_test(
            NAME wirehair_python_ctypes
            COMMAND
                "${Python3_EXECUTABLE}"
                "${WIREHAIR_SOURCE_DIR}/python/whirehair.py"
                --lib "$<TARGET_FILE:wirehair>"
                --quiet
        )
    else()
        message(STATUS "Python3 interpreter not found; skipping ctypes smoke test registration")
    endif()
elseif(BUILD_TESTING AND WIREHAIR_ALL_OS_BUILD_PYTHON_CTYPES_TEST)
    message(STATUS "Target is not runnable on this host; skipping runtime ctypes smoke test registration")
endif()

message(STATUS "wirehair-all-os source dir: ${WIREHAIR_SOURCE_DIR}")
message(STATUS "wirehair-all-os target: ${CMAKE_SYSTEM_NAME}/${CMAKE_SYSTEM_PROCESSOR}")
