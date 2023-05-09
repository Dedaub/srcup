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

from srcup.models import BuildSystem, ContractBytecode, ContractSource

app = typer.Typer()
builtins.print = rich.print  # type: ignore


@app.command()
def single(
    target: str = typer.Argument(...),
    framework: Optional[BuildSystem] = typer.Option(None),
    cache: bool = typer.Option(False, help="Use build cache"),
    api_url: str = typer.Option(
        "https://api.dedaub.com/api", help="URL of the Watchdog API"
    ),
    api_key: str = typer.Option(..., envvar="WD_API_KEY", help="Watchdog API key"),
):
    build, *_ = compile_build(target, framework, cache, "lzma")
    asyncio.run(asingle(build, api_url, api_key))


async def asingle(artifact: CryticCompile, api_url: str, api_key: str):
    contracts = process(artifact)

    sources, bytecodes = cast(
        tuple[list[ContractSource], list[ContractBytecode]], tuple(zip(*contracts))
    )

    try:
        project_id = await create_project(
            api_url,
            api_key,
            sources,
            bytecodes,
        )
        print(
            f"Successfully project #{project_id}: https://watchdog.dedaub.com/projects/{project_id}"
        )
    except Exception as e:
        print(type(e))
        print(e)
