import os
from typing import Any

from crytic_compile.crytic_compile import CryticCompile, compile_all
from crytic_compile.utils.zip import save_to_zip

from srcup.models import BuildSystem

"""
    Compiles a single build and exports it to the `export_dir` directory. Output can be compressed.

    Raises:
    [compilation]
    - crytic_compile.platform.exceptions.InvalidCompilation: If the particular build-system failed to run
    - ValueError: If solc-json is the selected framework and the target name/path is invalid

    [zip compression]
    - OSError or ValueError: If a related error is encountered

"""


def compile_build(
    build_path: str,
    framework: BuildSystem | None,
    use_cached_build: bool = False,
    compression_type: str | None = None,  # suppored: lzma, stored, deflated, bzip2
    export_dir: str = "watchdog",
    export_format: str = "archive",  # include source content in the exported json
) -> tuple[CryticCompile, str, str | None]:

    kwargs: dict[str, Any] = {"ignore_compile": use_cached_build}
    if framework:
        kwargs["compile_force_framework"] = framework.value

    build = CryticCompile(build_path, **kwargs)

    # crytic-compile automatically creates the `export_dir` directory if it does not exist
    export_path: str = build.export(export_format=export_format, export_dir=export_dir)[
        0
    ]

    zip_path: str | None = None
    if compression_type:
        zip_path = os.path.join(export_dir, "out.zip")
        save_to_zip([build], zip_path, compression_type)
        return build, export_path, zip_path

    return build, export_path, zip_path


"""
    Analogous to `compile_build` but supports multiple builds (builds can be of different language types)

    Raises:
    [compilation]
    - crytic_compile.platform.exceptions.InvalidCompilation: If the particular build-system failed to run
    - ValueError: If solc-json is the selected framework and the target name/path is invalid

    [zip compression]
    - OSError or ValueError: If a related error is encountered

"""


def compile_builds(
    builds_path: str,
    framework: BuildSystem,
    use_cached_build: bool = False,
    compression_type: str | None = None,  # suppored: lzma, stored, deflated, bzip2
    export_dir: str = "watchdog",
) -> tuple[list[CryticCompile], str | None]:

    builds = compile_all(
        builds_path,
        compile_force_framework=framework.value,
        ignore_compile=use_cached_build,  # type: ignore
    )

    zip_path: str | None = None
    if compression_type:
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        zip_path = os.path.join(export_dir, "out.zip")
        # builds are exported as "archives" so source gets also included !
        save_to_zip(builds, zip_path, compression_type)

    return builds, zip_path
