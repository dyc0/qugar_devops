macro(qugar_find_lapacke)
  set(LAPACKE_VERSION 3.9)

  # On Windows, conda-forge installs under $CONDA_PREFIX/Library/
  set(_LAPACKE_SEARCH_PATHS ${LAPACKE_DIR} $ENV{CONDA_PREFIX})
  if(WIN32 AND DEFINED ENV{CONDA_PREFIX})
    list(APPEND _LAPACKE_SEARCH_PATHS "$ENV{CONDA_PREFIX}/Library")
  endif()

  # Find LAPACKE header
  find_path(LAPACKE_INCLUDE_DIR
    NAMES lapacke.h
    PATHS ${_LAPACKE_SEARCH_PATHS}
    PATH_SUFFIXES include include/openblas
    NO_DEFAULT_PATH
  )

  # Find LAPACKE library
  find_library(LAPACKE_LIBRARY
    NAMES lapacke
    PATHS ${_LAPACKE_SEARCH_PATHS}
    PATH_SUFFIXES lib lib64
    NO_DEFAULT_PATH
  )

  # Also find LAPACK library (LAPACKE depends on it)
  find_library(LAPACK_LIBRARY
    NAMES lapack
    PATHS ${_LAPACKE_SEARCH_PATHS}
    PATH_SUFFIXES lib lib64
    NO_DEFAULT_PATH
  )
  
  if(LAPACKE_INCLUDE_DIR AND LAPACKE_LIBRARY AND LAPACK_LIBRARY)
    set(LAPACKE_FOUND TRUE)
    set(LAPACKE_INCLUDE_DIRS ${LAPACKE_INCLUDE_DIR})
    set(LAPACKE_LIBRARIES ${LAPACKE_LIBRARY} ${LAPACK_LIBRARY})
    
    message(STATUS "LAPACKE found:")
    message(STATUS "  LAPACKE_LIBRARIES: ${LAPACKE_LIBRARIES}")
    message(STATUS "  LAPACKE_INCLUDE_DIRS: ${LAPACKE_INCLUDE_DIRS}")
    
    add_compile_definitions(WITH_LAPACK)
    include_directories(${LAPACKE_INCLUDE_DIRS})
  else()
    message(STATUS "LAPACKE not found. Algoim's eigenvalue solvers will be used.")
    if(NOT LAPACKE_INCLUDE_DIR)
      message(STATUS "  - Could not find lapacke.h")
    endif()
    if(NOT LAPACKE_LIBRARY)
      message(STATUS "  - Could not find liblapacke")
    endif()
    if(NOT LAPACK_LIBRARY)
      message(STATUS "  - Could not find liblapack")
    endif()
  endif()
endmacro()
