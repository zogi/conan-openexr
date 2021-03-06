find_package(IlmBase REQUIRED)
find_package(ZLIB REQUIRED)

set(OPENEXR_INCLUDE_DIRS ${CONAN_INCLUDE_DIRS_OPENEXR})
set(OPENEXR_LIBRARY_DIRS ${CONAN_LIB_DIRS_OPENEXR})

set(OPENEXR_INCLUDE_DIR  ${OPENEXR_INCLUDE_DIRS})
set(OPENEXR_LIBRARY_DIR  ${OPENEXR_LIBRARY_DIRS})

set(OPENEXR_LIBRARIES "")
foreach (LIBNAME ${CONAN_LIBS_OPENEXR})
    string(REGEX MATCH "[^-]+" LIBNAME_STEM ${LIBNAME})
    find_library(OPENEXR_${LIBNAME_STEM}_LIBRARY NAMES ${LIBNAME} PATHS ${OPENEXR_LIBRARY_DIRS})
    list(APPEND OPENEXR_LIBRARIES "${OPENEXR_${LIBNAME_STEM}_LIBRARY}")
endforeach()
list(APPEND OPENEXR_LIBRARIES "${ILMBASE_LIBRARIES}")
list(APPEND OPENEXR_LIBRARIES "${ZLIB_LIBRARIES}")
set(OPENEXR_LIBRARY ${OPENEXR_LIBRARIES})

foreach (INCLUDE_DIR ${OPENEXR_INCLUDE_DIRS})
    if(NOT OPENEXR_VERSION AND INCLUDE_DIR AND EXISTS "${INCLUDE_DIR}/OpenEXR/OpenEXRConfig.h")
      file(STRINGS
           ${INCLUDE_DIR}/OpenEXR/OpenEXRConfig.h
           TMP
           REGEX "#define OPENEXR_VERSION_STRING.*$")
      string(REGEX MATCHALL "[0-9.]+" OPENEXR_VERSION ${TMP})
    endif()
endforeach()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(OpenEXR
    REQUIRED_VARS
        OPENEXR_INCLUDE_DIRS
        OPENEXR_LIBRARIES
    VERSION_VAR
        OPENEXR_VERSION
)
