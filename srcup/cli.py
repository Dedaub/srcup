#!/usr/bin/env python3

import asyncio
import builtins
import os
import pathlib
import rich
import sys
import typer
from crytic_compile import InvalidCompilation

from crytic_compile.crytic_compile import CryticCompile
from hashlib import sha1
from packaging import version
from subprocess import Popen, PIPE, TimeoutExpired
from typing import Optional, cast

from srcup.api import create_project, update_project
from srcup.build import compile_build
from srcup.extract import process
from srcup.models import BuildSystem, ContractBytecode, ContractSource, YulIRCode
from srcup.utils import get_latest_app_version, version_callback, __version__


app = typer.Typer()
builtins.print = rich.print  # type: ignore


@app.command()
def single(
    target: str = typer.Argument(...),
    framework: Optional[BuildSystem] = typer.Option(None),
    cache: bool = typer.Option(False, help="Use build cache"),
    init: bool = typer.Option(False, help="Is this a new project?"),
    api_url: str = typer.Option(
          "https://api.dedaub.com/api",
        help="URL of the Dedaub API"
    ),
    api_key: str = typer.Option(..., envvar="WD_API_KEY", help="Dedaub API key"),
    owner_username: str = typer.Option('', help="Username of project owner. Ignored when --init is also present"),
    name: str = typer.Option('', help="Project name"),
    comment: str = typer.Option('', help="Comment for the project"),
    app_version: bool = typer.Option(False, '--version', '-v', help="Show the version of the app", is_eager=True, callback=version_callback),
    use_ir: bool = typer.Option(False, help="Analyse Yul-IR instead of EVM bytecode")
):
    latest_app_version = asyncio.run(get_latest_app_version())
    if not latest_app_version:
        print("Warning: Failed to retrieve the latest available version of the app")

    elif version.parse(__version__) < version.parse(latest_app_version):
        print(f'Warning: A new version is available ({latest_app_version})\n')
        print(f'Please, update the app to continue:')
        print(f'  For pipx installation run:      pipx upgrade srcup')
        print(f'  For plain pip installation run: pip install --upgrade git+https://github.com/Dedaub/srcup#egg=srcup')
        return

    try:
        target = os.path.abspath(target)
        build, extra_fields, *_ = compile_build(target, use_ir, framework, cache, "lzma")
        asyncio.run(asingle(build, extra_fields, use_ir, api_url, api_key, init, owner_username, name, comment, target))
    except InvalidCompilation as e:
        print(f"Unable to perform compilation.\n")
        print("""
             Check the README file:
            'srcup assumes that the project to be uploaded has the default file layout of the underlying build system!'
            """)
        print(f"Error message was: {str(e)}")
        sys.exit(-1)


async def asingle(artifact: CryticCompile, extra_fields: dict, use_ir: bool, api_url: str, api_key: str,  init: bool, owner_username: str, name: str, comment: str, target: str):
    contracts = process(artifact, extra_fields, use_ir)

    sources, bytecodes, yul_ir = cast(
        tuple[list[ContractSource], list[ContractBytecode], list[YulIRCode | None]], tuple(zip(*contracts))
    )
    git_hash = await calc_hash(bytecodes, target)

    if not name:
        name = pathlib.Path(target).resolve().name

    try:
        if init:
            project_id, version_sequence = await create_project(
                api_url,
                api_key,
                name,
                comment,
                sources,
                bytecodes,
                yul_ir,
                git_hash
            )
            print(
                f"Successfully created project #{project_id} with version {version_sequence}: https://app.dedaub.com/projects/{project_id}_{version_sequence}"
            )
        else:
            project_id, version_sequence = await update_project(api_url, api_key, owner_username, name, comment, sources, bytecodes, yul_ir, git_hash)
            print(
                f"Successfully updated project #{project_id} with new version {version_sequence}: https://app.dedaub.com/projects/{project_id}_{version_sequence}"
            )
        print(f"{project_id} {version_sequence}")

    except Exception as e:
        print(f"Something went wrong with the project: {e}")
        sys.exit(-1)


async def calc_hash(bytecodes, target):
    try:
        git_hash = ''
        git_process = Popen(['git', '-C', os.path.dirname(target), 'rev-parse', 'HEAD'], shell=False, stdout=PIPE,
                            stderr=PIPE)
        result, error = git_process.communicate(timeout=60)
        if error == b'':
            git_hash = result.strip().decode("utf-8")
    except FileNotFoundError as error:
        print(f"git was not installed or git repository not detected: {error}")
    except TimeoutExpired:
        git_process.kill()
        print(f"git took too long to answer")
    finally:
        if git_hash == '':
            bytecode_hashes = b"".join([item.codehash for item in bytecodes])
            git_hash = sha1(bytecode_hashes).hexdigest()
    return git_hash
