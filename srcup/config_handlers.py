import os
from pathlib import Path
import subprocess

import srcup.constants

def find_hardhat_config(target: str) -> str | None:
    for candidate in ("hardhat.config.js", "hardhat.config.ts", "hardhat.config.cjs"):  
        if os.path.isfile(os.path.join(target, candidate)):
            return candidate

    return None


def handle_hardhat_config(build_path: str, use_ir: bool) -> tuple[Path, str] | None:
    if (config := find_hardhat_config(build_path)) is None:
        print("Can't locate hardhat config file")
        return None

    config_path = Path(build_path, config)

    if not config_path.is_file():
        print("Can't locate hardhat config file")
        return None

    with open(config_path) as f:
        original_config = f.read()

    with open(config_path, "a") as f:
        extra_config = srcup.constants.get_extra_config(use_ir)
        f.write(extra_config)

    return config_path, original_config


def handle_foundry_config(build_path: str, use_ir: bool) -> tuple[Path, str] | None:
    if not use_ir:
        return None

    config_path = Path(build_path, "foundry.toml")

    if not config_path.is_file():
        print("Can't locate foundry config file")
        return None

    with open(config_path, "r") as f:
        original_config = f.read()

    extra_config = subprocess.run(
        ["forge", "config", "--extra-output-files", "irOptimized"],
        cwd=build_path,
        stdout=subprocess.PIPE,
        check=True
    ).stdout.decode("utf8")

    with open(config_path, "w") as f:
        f.write(extra_config)

    return config_path, original_config


