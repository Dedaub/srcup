#!/usr/bin/env python3

from typing import Any
import aiohttp
from pydantic import BaseModel

from srcup.models import ContractBytecode, ContractInitCode, ContractSource, HexString, YulIRCode


async def create_project(
    watchdog_api: str,
    api_key: str,
    name: str,
    comment: str,
    sources: list[ContractSource],
    bytecode: list[ContractBytecode],
    ir_code: list[YulIRCode | None],
    init_code: list[ContractInitCode | None],
    git_hash: HexString,
    organization: str,
    entity_id: int | None,
    metadata: dict[str, Any],
) -> tuple[int, int]:
    class Payload(BaseModel):
        sources: list[ContractSource]
        bytecode: list[ContractBytecode]
        ir_code: list[YulIRCode | None]
        init_code: list[ContractInitCode | None]
        name: str
        comment: str
        git_hash: HexString
        organization: str
        entity_id: int | None
        metadata: dict[str, Any]

    req = Payload(
        sources=sources,
        bytecode=bytecode,
        ir_code=ir_code,
        init_code=init_code,
        name=name,
        comment=comment,
        git_hash=git_hash,
        organization=organization,
        entity_id=entity_id,
        metadata=metadata,
    )

    headers = {"Authorization": api_key, "User-Agent": "srcup"}

    async with aiohttp.ClientSession(headers=headers) as session:
        url = f"{watchdog_api}/project/create"
        async with session.post(url, json=req.model_dump()) as resp:
            if resp.status == 200:
                res = await resp.json()
                return res["project_id"], res["version_id"]
            else:
                raise Exception(await resp.text())
