#!/usr/bin/env python3

import aiohttp
from pydantic import ConfigDict, BaseModel

from srcup.models import ContractBytecode, ContractSource, HexString, YulIRCode


async def create_project(
    watchdog_api: str,
    api_key: str,
    name: str,
    comment: str,
    sources: list[ContractSource],
    bytecode: list[ContractBytecode],
    ir_code: list[YulIRCode | None],
    git_hash: HexString
) -> int:
    class Payload(BaseModel):
        # TODO[pydantic]: The following keys were removed: `json_encoders`.
        # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
        model_config = ConfigDict(json_encoders={bytes: lambda bs: bs.hex()})

        sources: list[ContractSource]
        bytecode: list[ContractBytecode]
        ir_code: list[YulIRCode | None]
        name: str
        comment: str
        git_hash: HexString

    async with aiohttp.ClientSession(
        headers={"x-api-key": api_key}, json_serialize=lambda x: x.json()
    ) as session:
        print("Uploading...")

        project_id = await get_project_id(watchdog_api, api_key, name)

        if project_id is not None:
            raise Exception(f"Project with name {name} already exists")

        url = f"{watchdog_api}/project"
        payload=Payload(name=name, sources=sources, bytecode=bytecode, ir_code=[x for x in ir_code if x], comment=comment, git_hash=git_hash)

        req = await session.post(
            url=url,
            json=payload
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
    ir_code: list[YulIRCode | None],
    git_hash: HexString
) -> tuple[int, int]:
    class Payload(BaseModel):
        # TODO[pydantic]: The following keys were removed: `json_encoders`.
        # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
        model_config = ConfigDict(json_encoders={bytes: lambda bs: bs.hex()})
        sources: list[ContractSource]
        bytecode: list[ContractBytecode]
        ir_code: list[YulIRCode] | None
        comment: str
        git_hash: HexString

    async with aiohttp.ClientSession(
        headers={"x-api-key": api_key}, json_serialize=lambda x: x.json()
    ) as session:
        print("Uploading...")

        project_id = await get_project_id(watchdog_api, api_key, name, owner_username)
        if project_id is None:
            raise Exception(f"No project with name {name} exists")

        url = f"{watchdog_api}/project/{project_id}/version"
        payload=Payload(sources=sources, bytecode=bytecode, ir_code=[x for x in ir_code if x], comment=comment, git_hash=git_hash)

        req = await session.post(
            url=url,
            json=payload,
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
                         ) -> int | None:

    async with aiohttp.ClientSession(
            headers={"x-api-key": api_key}) as session:

        url = f"{watchdog_api}/project/exists/{name}"

        if owner_username:
            req = await session.get(url=url,  params={'owner_username': owner_username})
        else:
            req = await session.get(url=url)

        if req.status == 200:
            return await req.json()
        else:
            return None  # project does not exist
