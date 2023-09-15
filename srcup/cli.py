#!/usr/bin/env python3


import asyncio
import builtins
from typing import Optional, cast

import rich
import typer
from crytic_compile.crytic_compile import CryticCompile
from srcup.build import compile_build
from srcup.api import create_project
from srcup.extract import process

from srcup.models import BuildSystem, ContractBytecode, ContractSource, HexBytes
from subprocess import Popen, PIPE
from hashlib import sha1

app = typer.Typer()
builtins.print = rich.print  # , type: ignore


@app.command()
def single(
    target: str = typer.Argument(...),
    framework: Optional[BuildSystem] = typer.Option(None),
    cache: bool = typer.Option(False, help="Use build cache"),
    api_url: str = typer.Option(
        "https://api.dedaub.com/api",
        help="URL of the Watchdog API"
    ),
    api_key: str = typer.Option(..., envvar="WD_API_KEY", help="Watchdog API key"),
    name: str = typer.Option('', help="Project name")
):
    build, *_ = compile_build(target, framework, cache, "lzma")
    asyncio.run(asingle(build, api_url, api_key, name, target))


async def asingle(artifact: CryticCompile, api_url: str, api_key: str, name: str, target: str):
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

    try:
        project_id = await create_project(
            api_url,
            api_key,
            name,
            sources,
            bytecodes,
            git_hash
        )
        print(
            f"Successfully project #{project_id}: https://watchdog.dedaub.com/projects/{project_id}"
        )
    except Exception as e:
        print(type(e))
        print(e)
