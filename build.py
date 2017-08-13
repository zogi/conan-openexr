from conan.packager import ConanMultiPackager


if __name__ == "__main__":
    builder = ConanMultiPackager(username="zogi", channel="stable", args="--build=missing")
    builder.add_common_builds(shared_option_name="OpenEXR:shared")
    builder.run()
