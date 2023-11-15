#!/usr/bin/env python3

import aiohttp
from pydantic import BaseModel

from srcup.models import ContractBytecode, ContractSource, HexString


async def create_project(
    watchdog_api: str,
    api_key: str,
    init: bool,
    owner_username: str,
    name: str,
    comment: str,
    sources: list[ContractSource],
    bytecode: list[ContractBytecode],
    git_hash: HexString
) -> int:
    class Payload(BaseModel):
        class Config:
            json_encoders = {bytes: lambda bs: bs.hex()}

        sources: list[ContractSource]
        bytecode: list[ContractBytecode]
        owner_username: str | None
        name: str
        comment: str
        git_hash: HexString

    async with aiohttp.ClientSession(
        headers={"x-api-key": api_key}, json_serialize=lambda x: x.json()
    ) as session:
        print("Uploading...")
        if init:
            url = f"{watchdog_api}/project/"
        else:
            url = f"{watchdog_api}/project/version/"

        req = await session.post(
            url=url,
            json=Payload(sources=sources, bytecode=bytecode, owner_username=owner_username, name=name, comment=comment, git_hash=git_hash)
        )

        if req.status == 200:
            print("Done!")
            return await req.json()
        else:
            print(await req.text())
            raise Exception("Something went while creating a new project")
