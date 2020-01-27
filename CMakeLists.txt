cmake_minimum_required(VERSION 3.8)

set(CMAKE_CONFIGURATION_TYPES "Debug;Release")

project(ig_rendering_support)


find_package(AnyDSL_runtime REQUIRED)
include_directories(${AnyDSL_runtime_INCLUDE_DIRS})

set(CLANG_FLAGS -march=native)
set(IMPALA_FLAGS --log-level info)

set(IMPALA_SOURCES
	src/ao/backend_cpu.impala
	src/ao/utils.impala
	src/ao/mapping_cpu.impala
    src/core/common.impala
    src/core/cpu_common.impala
    src/core/sort.impala
    src/core/vector.impala
    src/traversal/intersection.impala
    src/traversal/stack.impala
    src/traversal/mapping_cpu.impala
	src/ao/aobench.impala
)

anydsl_runtime_wrap(AOBENCH_PROGRAM
    CLANG_FLAGS ${CLANG_FLAGS}
    IMPALA_FLAGS ${IMPALA_FLAGS}
    INTERFACE ${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_CFG_INTDIR}/interface
    FILES ${IMPALA_SOURCES})
include_directories(${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_CFG_INTDIR})

set(CPP_SOURCES
	src/main.cpp
	src/bbox.h
	src/bvh.h
	src/common.h
	src/float3.h
	src/float4.h
	src/int.h
	src/tri.h
)

find_package(pybind11 2.2 REQUIRED)
pybind11_add_module(ig_rendering_support ${CPP_SOURCES} ${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_CFG_INTDIR}/interface.h ${AOBENCH_PROGRAM} ${IMPALA_SOURCES})
target_link_libraries(ig_rendering_support PRIVATE ${AnyDSL_runtime_LIBRARIES})

source_group(TREE ${CMAKE_CURRENT_SOURCE_DIR} FILES ${IMPALA_SOURCES} ${CPP_SOURCES})
set(RUNTIME_FILES ${AOBENCH_PROGRAM})
list(FILTER RUNTIME_FILES INCLUDE REGEX "\.(impala|h|hpp)$")
source_group("Runtime Files" FILES ${RUNTIME_FILES})

find_package(PythonInterp 3.6 REQUIRED)

set(PYINSTALLER_DELIMITER ":")
if(MSVC)
	set(COMMAND1 "COMMAND" "set")
	set(COMMAND2 "COMMAND")
	set(PYINSTALLER_DELIMITER ";")
endif()
add_custom_target(test_service
    ${COMMAND1} PYTHONPATH=$<TARGET_FILE_DIR:ig_rendering_support>
    ${COMMAND2} ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/service.py --test
    DEPENDS ig_rendering_support
)

find_program(PYINSTALLER_EXECUTABLE "pyinstaller")

set(PYINSTALLER_DEPLOYFORMAT "-F" CACHE STRING "Choose whether PyInstaller shall create a single file (-F) or a directory (-D)")
set_property(CACHE PYINSTALLER_DEPLOYFORMAT PROPERTY STRINGS "-F" "-D")

add_custom_target(dist
    ${COMMAND1} PYTHONPATH=$<TARGET_FILE_DIR:ig_rendering_support>
    ${COMMAND2} ${PYINSTALLER_EXECUTABLE} -n "GloBiE" ${PYINSTALLER_DEPLOYFORMAT} --add-binary "${CMAKE_CURRENT_SOURCE_DIR}/openctm/openctm.dll${PYINSTALLER_DELIMITER}./" ${CMAKE_CURRENT_SOURCE_DIR}/server.py
    DEPENDS ig_rendering_support
)
