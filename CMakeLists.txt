# --------------------------------------------------------------------------
#
# Copyright (C) 2025-present by Pablo Antolin
#
# This file is part of the QUGaR library.
#
# SPDX-License-Identifier:    MIT
#
# --------------------------------------------------------------------------

cmake_minimum_required(VERSION 3.23)

# Set the project name and language
set(qugar_VERSION "0.0.9")
project(
  qugar 
  VERSION ${qugar_VERSION}
  DESCRIPTION ""
  HOMEPAGE_URL "https://github.com/pantolin/qugar"
  )

option(BUILD_CPP "Build the C++ library" ON)
if(DEFINED SKBUILD)
  # If SKBUILD is defined, we are building with scikit-build
  # and we do not want to build the C++ library
  set(BUILD_CPP OFF)
endif()

option(BUILD_PYTHON "Build the Python bindings" OFF)
if(DEFINED SKBUILD)
  # If SKBUILD is defined, we are building with scikit-build
  # and we want to build the Python bindings
  set(BUILD_PYTHON ON)
endif()

set(qugar_SOURCE_DIR ${PROJECT_SOURCE_DIR}/cpp)
set(qugar_BINARY_DIR ${PROJECT_BINARY_DIR})

set(qugar_INCLUDE_DIR ${qugar_SOURCE_DIR}/include)
set(qugar_TEST_DIR ${qugar_SOURCE_DIR}/test)
set(qugar_DOC_DIR ${qugar_SOURCE_DIR}/doc)

set(qugar_CMAKE_DIR ${PROJECT_SOURCE_DIR}/cmake)

include(cmake/GitConfig.cmake)
include(cmake/PreventInSourceBuilds.cmake)
include(cmake/Dependencies.cmake)

git_config()
qugar_setup_dependencies()

if(BUILD_CPP)
  add_subdirectory(cpp)
endif()

if(BUILD_PYTHON)
  add_subdirectory(python)
endif()

