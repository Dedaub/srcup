#!/usr/bin/env python3

import asyncio
import builtins
import importlib.metadata
import pathlib
import rich
import typer

from crytic_compile.crytic_compile import CryticCompile
from hashlib import sha1
from packaging import version
from subprocess import Popen, PIPE
from typing import Optional, cast

from srcup.api import create_project, update_project
from srcup.build import compile_build
from srcup.extract import process
from srcup.models import BuildSystem, ContractBytecode, ContractSource, HexBytes
from srcup.utils import get_latest_app_version

app = typer.Typer()
builtins.print = rich.print  # type: ignore


@app.command()
def single(
    target: str = typer.Argument('DEFAULT_ARGUMENT'),
    framework: Optional[BuildSystem] = typer.Option(None),
    cache: bool = typer.Option(False, help="Use build cache"),
    init: bool = typer.Option(False, help="Is this a new project?"),
    api_url: str = typer.Option(
         "https://api.dedaub.com/api",
        help="URL of the Watchdog API"
    ),
    api_key: str = typer.Option(..., envvar="WD_API_KEY", help="Watchdog API key"),
    owner_username: str = typer.Option('', help="Username of project owner. Ignored when --init is also present"),
    name: str = typer.Option('', help="Project name"),
    comment: str = typer.Option('', help="Comment for the project"),
    show_version: bool = typer.Option(False, '--version', '-v', help="Show the version of the app")
):
    if target == 'DEFAULT_ARGUMENT' and not show_version:
        raise typer.BadParameter("Missing argument 'TARGET'")

    app_version = importlib.metadata.version('srcup')

    if show_version:
        print(app_version)
        return

    latest_app_version = asyncio.run(get_latest_app_version())
    if not latest_app_version:
        print("Error: Failed to retrieve the latest version of the app")
        return

    if version.parse(app_version) < version.parse(latest_app_version):
        print(f'Warning: A new version is available ({latest_app_version})\n')
        print(f'Please, update the app to continue:')
        print(f'  For pipx installation run:      pipx upgrade srcup')
        print(f'  For plain pip installation run: pip install --upgrade git+https://github.com/Dedaub/srcup#egg=srcup')
        return

    build, *_ = compile_build(target, framework, cache, "lzma")
    asyncio.run(asingle(build, api_url, api_key, init, owner_username, name, comment, target))


async def asingle(artifact: CryticCompile, api_url: str, api_key: str,  init: bool, owner_username: str, name: str, comment: str, target: str):
    contracts = process(artifact)

    sources, bytecodes = cast(
        tuple[list[ContractSource], list[ContractBytecode]], tuple(zip(*contracts))
    )
    try:
        git_process = Popen(['git', '-C', target, 'rev-parse', 'HEAD'], shell=False, stdout=PIPE)
        result = git_process.communicate()
        git_hash = result[0].strip().decode("utf-8")
    except:
        #No git present?
        git_hash = ''

    if git_hash == '':
        bytecode_hashes = b"".join([item.codehash for item in bytecodes])
        git_hash = sha1(bytecode_hashes).hexdigest()

    if not name:
        name = pathlib.Path(target).resolve().name

    try:
        if init:
            project_id = await create_project(
                api_url,
                api_key,
                name,
                comment,
                sources,
                bytecodes,
                git_hash
            )
            print(
                f"Successfully created project #{project_id}: https://watchdog.dedaub.com/projects/{project_id}"
            )
        else:
            project_id, version_id = await update_project(api_url, api_key, owner_username, name, comment, sources, bytecodes, git_hash)
            print(
                f"Successfully updated project #{project_id} with new version {version_id}: https://watchdog.dedaub.com/projects/{project_id}"
            )

    except Exception as e:
        print(type(e))
        print(e)
