from conans import ConanFile, CMake, tools
import os


class OpenEXRConan(ConanFile):
    name = "OpenEXR"
    description = "OpenEXR is a high dynamic-range (HDR) image file format developed by Industrial Light & Magic for use in computer imaging applications."
    version = "2.2.0"
    license = "BSD"
    url = "https://github.com/Mikayex/conan-openexr.git"
    requires = "IlmBase/2.2.0@Mikayex/stable", "zlib/1.2.8@lasote/stable"
    exports = "mingw-fix.patch", "FindOpenEXR.cmake"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "namespace_versioning": [True, False], "fPIC": [True, False]}
    default_options = "shared=True", "namespace_versioning=True", "fPIC=False"
    generators = "cmake"
    build_policy = "missing"

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")

    def configure(self):
        self.options["IlmBase"].namespace_versioning = self.options.namespace_versioning
        self.options["IlmBase"].shared = self.options.shared
        if "fPIC" in self.options.fields:
            if self.options.shared:
                self.options.fPIC = True
            self.options["IlmBase"].fPIC = self.options.fPIC

    def source(self):
        tools.download("http://download.savannah.nongnu.org/releases/openexr/openexr-%s.tar.gz" % self.version,
                       "openexr.tar.gz")
        tools.untargz("openexr.tar.gz")
        os.unlink("openexr.tar.gz")
        tools.replace_in_file("openexr-%s/CMakeLists.txt" % self.version, "PROJECT (openexr)",
                              """PROJECT (openexr)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
set(ILMBASE_PACKAGE_PREFIX ${CONAN_ILMBASE_ROOT})
file(GLOB RUNTIME_FILES ${CONAN_ILMBASE_ROOT}/bin/*.dll ${CONAN_ILMBASE_ROOT}/lib/*.dylib)
file(COPY ${RUNTIME_FILES} DESTINATION ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})""")

        # Fixes for conan putting binaries in bin folder
        tools.replace_in_file("openexr-%s/IlmImf/CMakeLists.txt" % self.version,
                              "${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_CFG_INTDIR}/b44ExpLogTable", "b44ExpLogTable")
        tools.replace_in_file("openexr-%s/IlmImf/CMakeLists.txt" % self.version,
                              "${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_CFG_INTDIR}/dwaLookups", "dwaLookups")
        tools.replace_in_file("openexr-%s/IlmImf/CMakeLists.txt" % self.version, "ADD_EXECUTABLE ( dwaLookups",
                              """file(COPY ${RUNTIME_FILES} DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
ADD_EXECUTABLE ( dwaLookups""")
        tools.replace_in_file("openexr-%s/IlmImf/CMakeLists.txt" % self.version,
                              """  Iex${ILMBASE_LIBSUFFIX}
  IlmThread${ILMBASE_LIBSUFFIX}""", """  IlmThread${ILMBASE_LIBSUFFIX}
  Iex${ILMBASE_LIBSUFFIX}""")  # Fix wrong link order when using static IlmBase on gcc

        # Remove tests compilation
        tools.replace_in_file("openexr-%s/CMakeLists.txt" % self.version, "ADD_SUBDIRECTORY ( IlmImfExamples )", "")
        tools.replace_in_file("openexr-%s/CMakeLists.txt" % self.version, "ADD_SUBDIRECTORY ( IlmImfTest )", "")
        tools.replace_in_file("openexr-%s/CMakeLists.txt" % self.version, "ADD_SUBDIRECTORY ( IlmImfUtilTest )", "")
        tools.replace_in_file("openexr-%s/CMakeLists.txt" % self.version, "ADD_SUBDIRECTORY ( IlmImfFuzzTest )", "")

        if self.settings.os == "Windows" and self.settings.compiler == "gcc":  # MinGW compiler
            tools.patch(patch_file="mingw-fix.patch", base_path="openexr-%s" % self.version)

    def build(self):
        if self.settings.os == "Linux":
            ld_library_paths = os.environ.get("LD_LIBRARY_PATH", "").split(":")
            ld_library_paths = [path for path in ld_library_paths if path]
            ilmbase_cpp_info = self.deps_cpp_info["IlmBase"]
            ld_library_paths.extend([ilmbase_cpp_info.rootpath + "/" + libdir
                                     for libdir in ilmbase_cpp_info.libdirs])
            os.environ["LD_LIBRARY_PATH"] = ":".join(ld_library_paths)

        cmake = CMake(self)
        cmake.definitions.update(
            { "BUILD_SHARED_LIBS": self.options.shared
            , "NAMESPACE_VERSIONING": self.options.namespace_versioning
            , "USE_ZLIB_WINAPI": False
            })
        if "fPIC" in self.options.fields:
            cmake.definitions["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.fPIC

        src_dir = "openexr-%s" % self.version
        cmake.configure(source_dir=src_dir)
        cmake.build()

    def package(self):
        self.copy("Imf*.h", dst="include/OpenEXR", src="openexr-%s/IlmImf" % self.version, keep_path=False)
        self.copy("Imf*.h", dst="include/OpenEXR", src="openexr-%s/IlmImfUtil" % self.version, keep_path=False)
        self.copy("OpenEXRConfig.h", dst="include/OpenEXR", src="config", keep_path=False)

        self.copy("*IlmImf*.lib", dst="lib", src=".", keep_path=False)
        self.copy("*IlmImf*.a", dst="lib", src=".", keep_path=False)
        self.copy("*IlmImf*.so", dst="lib", src=".", keep_path=False)
        self.copy("*IlmImf*.so.*", dst="lib", src=".", keep_path=False)
        self.copy("*IlmImf*.dylib*", dst="lib", src=".", keep_path=False)

        self.copy("*IlmImf*.dll", dst="bin", src="bin", keep_path=False)
        self.copy("exr*", dst="bin", src="bin", keep_path=False)

        self.copy("FindOpenEXR.cmake", src=".", dst=".")
        self.copy("license*", dst="licenses", src="openexr-%s" % self.version, ignore_case=True, keep_path=False)

    def package_info(self):
        parsed_version = self.version.split('.')
        version_suffix = "-%s_%s" % (parsed_version[0], parsed_version[1]) if self.options.namespace_versioning else ""

        if self.options.shared and self.settings.os == "Windows":
            self.cpp_info.defines.append("OPENEXR_DLL")
        self.cpp_info.bindirs = ["bin"]
        self.cpp_info.includedirs = ['include', 'include/OpenEXR']
        self.cpp_info.libs = ["IlmImf" + version_suffix, "IlmImfUtil" + version_suffix]
