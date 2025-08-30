# --------------------------------------------------------------------------
#
# Copyright (C) 2025-present by Pablo Antolin
#
# This file is part of the QUGaR library.
#
# SPDX-License-Identifier:    MIT
#
# --------------------------------------------------------------------------

if(WIN32)
  # Windows requires all symbols to be manually exported. This flag exports all
  # symbols automatically, as in Unix.
  set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)
endif(WIN32)

find_package(
  Python
  COMPONENTS Interpreter Development # TODO: Development.Module? for CMake>3.18?
  REQUIRED
)

# Detect the installed nanobind package and import it into CMake
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE
  OUTPUT_VARIABLE NB_DIR
)
list(APPEND CMAKE_PREFIX_PATH "${NB_DIR}")
find_package(nanobind CONFIG REQUIRED)

# Create the binding library 
# nanobind handles its own calls to target_link_libraries
nanobind_add_module(
  cpp
  NOMINSIZE
  MODULE
  nanobind_wrappers/qugar.cpp
  nanobind_wrappers/common.cpp
  nanobind_wrappers/quad.cpp
  nanobind_wrappers/cut_quad.cpp
  nanobind_wrappers/unf_domain.cpp
  nanobind_wrappers/reparam.cpp
  nanobind_wrappers/impl_functions.cpp
)

# TODO: This DOES NOT set the standard, rather just defines a flag -Dcxx_std_20?
target_compile_definitions(cpp PRIVATE cxx_std_20) 

# Add QUGAR libraries. 
# target_link_libraries(cpp PRIVATE qugar::qugar qugar::qugar_options qugar::qugar_warnings qugar::algoim algoim::algoim)
if(BUILD_CPP)
  # If we are building the C++ library, add it as a submodule
  message(STATUS "Linking against local build of qugar")
  target_link_libraries(cpp PRIVATE qugar algoim::algoim ${LAPACKE_LIBRARIES})
else()
  # If we are not building the C++ library, we assume it is installed
  message(STATUS "Linking against installed qugar")
  if (DEFINED qugar_DIR)
    list(APPEND CMAKE_PREFIX_PATH "${qugar_DIR}")
  endif()
  find_package(qugar CONFIG REQUIRED)
  if(qugar_FOUND)
    message(STATUS "Found qugar at ${qugar_DIR}")
  endif()
  target_link_libraries(cpp PRIVATE qugar::qugar algoim::algoim ${LAPACKE_LIBRARIES})
endif()

target_include_directories(cpp SYSTEM PRIVATE
  ${Python_INCLUDE_DIRS}
  ${NB_DIR}/include
)

set_target_properties(cpp PROPERTIES INSTALL_RPATH_USE_LINK_PATH TRUE)

install(TARGETS cpp DESTINATION qugar)
