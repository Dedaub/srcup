import json
import os
import subprocess
from pathlib import Path
from typing import Any

from crytic_compile.crytic_compile import CryticCompile, compile_all
from crytic_compile.platform.foundry import Foundry
from crytic_compile.platform.hardhat import Hardhat
from crytic_compile.platform.solc import Solc, relative_to_short
from crytic_compile.utils.naming import convert_filename, extract_name
from crytic_compile.utils.zip import save_to_zip
import srcup.constants
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
    use_ir: bool,
    framework: BuildSystem | None,
    use_cached_build: bool = False,
    compression_type: str | None = None,  # suppored: lzma, stored, deflated, bzip2
    export_dir: str = "watchdog",
    export_format: str = "archive",  # include source content in the exported json
) -> tuple[CryticCompile, dict | None, str, str | None]:
    extra_fields = None
    kwargs: dict[str, Any] = {"ignore_compile": use_cached_build}
    buildsystem = None
    if framework:
        kwargs["compile_force_framework"] = framework.value
        buildsystem = framework.value
    build = None
    if use_ir:
        if Foundry.is_supported(build_path) or buildsystem == BuildSystem.FOUNDRY:
            with open("foundry.toml", "r") as f:
                prev_json_config = f.read()
            with open("foundry.toml", "w") as f:
                f.write(subprocess.run(
                        ["forge", "config", "--extra-output-files", "irOptimized"], cwd=build_path, stdout=subprocess.PIPE, check=True
                    ).stdout.decode('utf8'))
            build = CryticCompile(build_path, **kwargs)
            with open("foundry.toml", "w") as f:
                f.write(prev_json_config)
        elif Solc.is_supported(build_path):
            build = CryticCompile(build_path, compile_custom_build="solc -o ./ --ir-optimized "+build_path)
        elif Hardhat.is_supported(build_path):
            extra_config = srcup.constants.extra_config + srcup.constants.ir_ast_config
            with open("hardhat.config.js", "r") as f:
                initial_config = f.read()
            with open("hardhat.config.js", "a") as f:
                f.write(extra_config)
            build = CryticCompile(build_path, **kwargs)
            build_directory = Path(
                build.target,
                "artifacts",
                "build-info",
            )
            extra_fields = get_extraFields(build, build.target, build_directory, build.working_dir, use_ir)
            with open("hardhat.config.js", "w") as f:
                f.write(initial_config)
    elif not use_ir and Hardhat.is_supported(build_path):
            extra_config = srcup.constants.extra_config
            with open("hardhat.config.js", "r") as f:
                initial_config = f.read()
            with open("hardhat.config.js", "a") as f:
                f.write(extra_config)
            build = CryticCompile(build_path, **kwargs)
            build_directory = os.path.join(
                build.target,
                "artifacts",
                "build-info",
            )
            extra_fields = get_extraFields(build, build.target, build_directory, build.working_dir, use_ir)
            with open("hardhat.config.js", "w") as f:
                f.write(initial_config)

    # crytic-compile automatically creates the `export_dir` directory if it does not exist
    export_path: str = build.export(export_format=export_format, export_dir=export_dir)[
        0
    ]

    zip_path: str | None = None
    if compression_type:
        zip_path = os.path.join(export_dir, "out.zip")
        save_to_zip([build], zip_path, compression_type)
        return build, extra_fields, export_path, zip_path

    return build, extra_fields, export_path, zip_path


class ExtraFieldsOfSOurceUnit():
    def __init__(self, filename):
        self.filename = filename
        self.contracts = []
        self.contract_to_ir = {}
        self.contract_to_debug_info = {}
        self.contract_to_im_ref = {}

    def add_contract(self, contract_name):
        self.contracts.append(contract_name)

    def add_ir(self, contract_name, ir_code):
        self.contract_to_ir[contract_name] = ir_code

    def add_immutable_ref(self, contract_name, imm_ref):
        self.contract_to_im_ref[contract_name] = imm_ref

    def add_debug_info(self, contract_name, debug_info):
        self.contract_to_debug_info[contract_name] = debug_info


def get_extraFields(
    crytic_compile: "CryticCompile", target: str, build_directory: Path, working_dir: str, use_ir: bool
) -> None:
    src_to_extra_fields = {}
    files = sorted(
        os.listdir(build_directory), key=lambda x: os.path.getmtime(Path(build_directory, x))
    )
    files = [str(f) for f in files if str(f).endswith(".json")]
    for file in files:
        build_info = Path(build_directory, file)
        with open(build_info, encoding="utf8") as file_desc:
            loaded_json = json.load(file_desc)
            targets_json = loaded_json["output"]
            if "contracts" in targets_json:
                for original_filename, contracts_info in targets_json["contracts"].items():

                    filename = convert_filename(
                        original_filename,
                        relative_to_short,
                        crytic_compile,
                        working_dir=working_dir,
                    )
                    src_to_extra_fields[filename.absolute] = ExtraFieldsOfSOurceUnit(filename.absolute)
                    for original_contract_name, info in contracts_info.items():
                        contract_name = extract_name(original_contract_name)
                        src_to_extra_fields[filename.absolute].add_contract(contract_name)
                        if use_ir:
                            src_to_extra_fields[filename.absolute].add_ir(contract_name, info["irOptimizedAst"])
                        src_to_extra_fields[filename.absolute].add_immutable_ref(contract_name, info["evm"]["deployedBytecode"]["immutableReferences"])
                        src_to_extra_fields[filename.absolute].add_debug_info(contract_name, info["evm"]["deployedBytecode"]["functionDebugData"])
    return src_to_extra_fields


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
