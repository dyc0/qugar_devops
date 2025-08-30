include(${qugar_CMAKE_DIR}/ProjectOptions.cmake)
include(${qugar_CMAKE_DIR}/Install.cmake)

# Only set the cxx_standard if it is not set by someone else
if(NOT DEFINED CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 20)
endif()

# strongly encouraged to enable this globally to avoid conflicts between
# -Wpedantic being enabled and -std=c++20 and -std=gnu++20 for example
# when compiling with PCH enabled
set(CMAKE_CXX_EXTENSIONS ON)

qugar_setup_config_options()
qugar_setup_options()

qugar_global_options()
qugar_local_options()

# don't know if this should be set globally from here or not...
set(CMAKE_CXX_VISIBILITY_PRESET hidden)

# Adding sources
add_subdirectory(qugar)

# TODO: Check if this will work with top-level CMakeLists
# Don't even look at tests if we're not top level
if(NOT PROJECT_IS_TOP_LEVEL)
  return()
endif()

# Adding the tests:
include(CTest)

if(BUILD_TESTING)
  # message(AUTHOR_WARNING "Building Tests. Be sure to check out test/constexpr_tests.cpp for constexpr testing")
  add_subdirectory(test)
endif()


# If MSVC is being used, and ASAN is enabled, we need to set the debugger environment
# so that it behaves well with MSVC's debugger, and we can run the target from visual studio
if(MSVC)
  get_all_installable_targets(all_targets)
  message("all_targets=${all_targets}")
  set_target_properties(${all_targets} PROPERTIES VS_DEBUGGER_ENVIRONMENT "PATH=$(VC_ExecutablePath_x64);%PATH%")
endif()

if(qugar_BUILD_DOC)
  add_subdirectory(doc)
endif()

# set the startup project for the "play" button in MSVC
# set_property(DIRECTORY PROPERTY VS_STARTUP_PROJECT demo_reparam_gygroid)
if(qugar_WITH_DEMOS)
  add_subdirectory(demo)
endif()

qugar_install_project()
