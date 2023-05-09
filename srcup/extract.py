#!/usr/bin/env python3

from hashlib import md5
from typing import cast

from crytic_compile.compilation_unit import CompilationUnit
from crytic_compile.crytic_compile import CryticCompile
from crytic_compile.source_unit import SourceUnit
from eth_hash.auto import keccak

from srcup.models import ContractBytecode, ContractSource, HexBytes


def handle_type(input: dict) -> str:
    _type = input["type"]
    if not _type.startswith("tuple"):
        return _type
    array_type = _type[5:]
    return "(" + ",".join(map(handle_type, input["components"])) + ")" + array_type


def construct_signature(abi: dict) -> str:
    return f'{abi["name"]}({",".join(map(handle_type, abi["inputs"]))})'


def create_file_mapping(comp_unit: CompilationUnit) -> dict[str, SourceUnit]:
    files: dict[str, SourceUnit] = {}
    for source_unit in comp_unit.source_units.values():
        if comp_unit.compiler_version.compiler == "vyper":
            file_id = source_unit.ast["ast"]["body"][0]["src"].split(":")[2]
        else:
            file_id = source_unit.ast["src"].split(":")[2]
        files[file_id] = source_unit
    return files


def get_referenced_sources(src_map: list[str] | str) -> list[str]:
    return sorted(
        {
            file_id
            for _map in (src_map if isinstance(src_map, list) else src_map.split(";"))
            if len(items := _map.split(":")) >= 3 and (file_id := items[2]) != ""
        },
        key=int,
    )


def remap_srcmap(src_map: list[str], remapping: dict[str, str]):
    remapped_src_map: list[str] = []
    for _map in src_map:
        if len(items := _map.split(":")) >= 3 and (file_id := items[2]) != "":
            items[2] = remapping[file_id]
            remapped_src_map.append(":".join(items))
        else:
            remapped_src_map.append(_map)
    return remapped_src_map


def generate_remapping(references: list[str], file_ids: set[str]) -> dict[str, str]:
    return {
        v: str(k) if v in file_ids else "-1"
        for k, v in enumerate(
            references,
            start=-1 if len(references) and references[0] == "-1" else 0,
        )
    }


def process(artifact: CryticCompile) -> list[tuple[ContractSource, ContractBytecode]]:

    contracts: list[tuple[ContractSource, ContractBytecode]] = []

    for comp_unit in artifact.compilation_units.values():
        file_mapping = create_file_mapping(comp_unit)
        for source_unit in comp_unit.source_units.values():
            for contract_name in source_unit.contracts_names:
                if (
                    hex_runtime_bytecode := source_unit.bytecode_runtime(
                        contract_name,
                        {k: 0 for k, v in source_unit.libraries[contract_name]},
                    )
                ) == "":
                    continue

                src_map = source_unit.srcmap_runtime(contract_name)
                references = get_referenced_sources(src_map)
                ref_remap = generate_remapping(references, set(file_mapping.keys()))
                remapped_srcmap = remap_srcmap(src_map, ref_remap)
                sources = [
                    file
                    for k in references
                    if (file := file_mapping.get(k)) is not None
                ]

                runtime_bytecode = bytes.fromhex(hex_runtime_bytecode)

                md5_bytecode = md5(runtime_bytecode).digest()

                src = ContractSource(
                    contract_name=contract_name,
                    contract_path=source_unit.filename.short,
                    array_source_names=[source.filename.short for source in sources],
                    array_source_level=[
                        artifact.src_content[source.filename.absolute]
                        for source in sources
                    ],
                    md5_bytecode=HexBytes(md5_bytecode),
                    source_map=";".join(remapped_srcmap),
                    json_abi=cast(list[dict], source_unit.abi(contract_name)),
                    array_selectors=[
                        HexBytes(keccak(construct_signature(abi).encode())[:4])
                        for abi in source_unit.abi(contract_name)
                        if abi["type"] == "function"
                    ],
                    array_event_selectors=[
                        HexBytes(keccak(construct_signature(abi).encode()))
                        for abi in source_unit.abi(contract_name)
                        if abi["type"] == "event"
                    ],
                    array_error_selectors=[
                        HexBytes(keccak(construct_signature(abi).encode())[:4])
                        for abi in source_unit.abi(contract_name)
                        if abi["type"] == "error"
                    ],
                )

                bytecode = ContractBytecode(
                    md5_bytecode=HexBytes(md5_bytecode),
                    codehash=HexBytes(keccak(runtime_bytecode)),
                    bytecode=HexBytes(runtime_bytecode),
                )

                contracts.append((src, bytecode))

    return contracts
