#!/usr/bin/env python3

import aiohttp
from pydantic import BaseModel

from srcup.models import ContractBytecode, ContractSource, HexString


async def create_project(
    watchdog_api: str,
    api_key: str,
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
        name: str
        comment: str
        git_hash: HexString

    async with aiohttp.ClientSession(
        headers={"x-api-key": api_key}, json_serialize=lambda x: x.json()
    ) as session:
        print("Uploading...")

        project_id = await get_project_id(watchdog_api, api_key, name)

        if project_id != -1:
            raise Exception(f"Project with name {name} already exists")

        url = f"{watchdog_api}/project/"

        req = await session.post(
            url=url,
            json=Payload(sources=sources, bytecode=bytecode, name=name, comment=comment, git_hash=git_hash)
        )

        if req.status == 200:
            print("Done!")
            return await req.json()
        else:
            error = await req.text()
            raise Exception(error)


async def update_project(
    watchdog_api: str,
    api_key: str,
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
        comment: str
        git_hash: HexString

    async with aiohttp.ClientSession(
        headers={"x-api-key": api_key}, json_serialize=lambda x: x.json()
    ) as session:
        print("Uploading...")

        project_id = await get_project_id(watchdog_api,api_key, name, owner_username)
        if project_id == -1:
            raise Exception(f"No project with name {name} exists")

        url = f"{watchdog_api}/project/{project_id}/version"

        req = await session.post(
            url=url,
            json=Payload(sources=sources, bytecode=bytecode, comment=comment, git_hash=git_hash)
        )

        if req.status == 200:
            version_id = await req.json()
            print(f"Updated project {project_id} with a new version: {version_id}!")
            return project_id, version_id
        else:
            error = await req.text()
            raise Exception(error)


async def get_project_id(watchdog_api: str,
    api_key: str,
    name: str,
    owner_username: str = '',
) -> int:

    async with aiohttp.ClientSession(
            headers={"x-api-key": api_key}) as session:

        url = f"{watchdog_api}/project/exists/{name}"

        if owner_username:
            req = await session.get(url=url,  params={'owner_username', owner_username})
        else:
            req = await session.get(url=url)

        if req.status == 200:
            return await req.json()
        else:
            return -1  # project does not exist