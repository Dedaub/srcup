#!/usr/bin/env python3

import asyncio
import os
import pathlib
import sys
import typer
from crytic_compile import InvalidCompilation

from crytic_compile.crytic_compile import CryticCompile
from hashlib import sha1
from subprocess import Popen, PIPE, TimeoutExpired
from typing import Optional, cast

from srcup.api import create_project, update_project, get_org_entity_id, extract_organization_from_name
from srcup.build import ExtraFieldsOfSourceUnit, compile_build
from srcup.extract import process
from srcup.models import BuildSystem, ContractBytecode, ContractInitCode, ContractSource, YulIRCode
from srcup.utils import version_callback, __version__


app = typer.Typer()


@app.command()
def single(
    target: str = typer.Argument(...),
    framework: Optional[BuildSystem] = typer.Option(None),
    cache: bool = typer.Option(False, help="Use build cache"),
    init: bool = typer.Option(False, help="Is this a new project?"),
    organization: str = typer.Option(default='', help="Organization to which the project belongs. Ignored when --init is not present"),
    api_url: str = typer.Option(
          "https://api.dedaub.com/api",
        help="URL of the Dedaub API"
    ),
    api_key: str = typer.Option(..., envvar="WD_API_KEY", help="Dedaub API key"),
    owner_username: str = typer.Option('', help="Username of project owner. Ignored when --init is also present"),
    name: str = typer.Option('', help="Project name"),
    comment: str = typer.Option('', help="Comment for the project"),
    app_version: bool = typer.Option(False, '--version', '-v', help="Show the version of the app", is_eager=True, callback=version_callback),
    use_ir: bool = typer.Option(False, help="Analyse Yul-IR instead of EVM bytecode"),
    debug_info: bool = typer.Option(True, help="Extract debug info from the build artifacts. This can help recover some high-level names."),
    init_code: bool = typer.Option(False, help="Extract the init code from the build artifacts."),
):
    try:
        target = os.path.abspath(target)
        build, extra_fields, *_ = compile_build(target, use_ir, debug_info, framework, cache, "lzma")
        asyncio.run(asingle(build, extra_fields, use_ir, debug_info, init_code, api_url, api_key, init, organization, owner_username, name, comment, target))
    except InvalidCompilation as e:
        print(f"Unable to perform compilation.\n")
        print("""
             Check the README file:
            'srcup assumes that the project to be uploaded has the default file layout of the underlying build system!'
            """)
        print(f"Error message was: {str(e)}")
        sys.exit(-1)


async def asingle(
    artifact: CryticCompile,
    extra_fields: dict[str, ExtraFieldsOfSourceUnit],
    use_ir: bool,
    get_debug_info: bool,
    get_init_code: bool,
    api_url: str,
    api_key: str,
    init: bool,
    organization: str,
    owner_username: str,
    name: str,
    comment: str,
    target: str
):
    contracts = process(artifact, extra_fields, use_ir, get_debug_info, get_init_code)

    sources: list[ContractSource] = []
    bytecodes: list[ContractBytecode] = []
    yul_ir: list[YulIRCode | None] = []
    init_code: list[ContractInitCode | None] = []

    if len(contracts):
        sources, bytecodes, yul_ir, init_code = cast(
            tuple[list[ContractSource], list[ContractBytecode], list[YulIRCode | None], list[ContractInitCode | None]], tuple(zip(*contracts))
        )
    else:
        print("WARNING: Discovered 0 contracts -- are you pointing srcup to the right directory? Aborting upload...")
        return

    git_hash = await calc_hash(bytecodes, target)

    if not name:
        name = pathlib.Path(target).resolve().name

    if not organization:
        organization, name = extract_organization_from_name(name)

    try:
        if init:
            entity_id: int | None = None
            if organization:
                entity_id = await get_org_entity_id(api_url, api_key, organization)

            project_id, version_sequence = await create_project(
                api_url,
                api_key,
                name,
                comment,
                sources,
                bytecodes,
                yul_ir,
                init_code,
                git_hash,
                organization,
                entity_id,
                {"use_ir": use_ir, "build_system": artifact.platform.NAME, "debug_info": get_debug_info}
            )
            print(
                f"Successfully created project #{project_id} with version {version_sequence}: https://app.dedaub.com/projects/{project_id}_{version_sequence}"
            )
        else:
            project_id, version_sequence = await update_project(api_url, api_key, owner_username or organization, name, comment, sources, bytecodes, yul_ir, init_code, git_hash, {"use_ir": use_ir, "build_system": artifact.platform.NAME, "debug_info": get_debug_info})
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
