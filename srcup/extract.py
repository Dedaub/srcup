#!/usr/bin/env python3

from hashlib import md5
import json
from typing import cast

from crytic_compile.compilation_unit import CompilationUnit
from crytic_compile.crytic_compile import CryticCompile
from crytic_compile.platform.types import Type
from crytic_compile.source_unit import SourceUnit
from eth_hash.auto import keccak

import os
from .models import ContractBytecode, ContractSource, HexBytes, YulIRCode


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

def extract_extra_fields(md5_bytecode: bytes, contract_name: str, source_unit, artifact: CryticCompile, extra_fields: dict, use_ir: bool) -> tuple[dict | None, dict | None, YulIRCode | None]:
    im_ref, debug_info, yul_ir = None, None, None

    # If we are building with Hardhat, we can extract the extra fields
    if artifact.platform.TYPE == Type.HARDHAT:
        extra_fields_of_file = extra_fields.get(source_unit.filename.absolute)

        if extra_fields_of_file:
            im_ref = extra_fields_of_file.contract_to_im_ref.get(contract_name)
            debug_info = extra_fields_of_file.contract_to_debug_info.get(contract_name)

    # Nothing else to do for the other systems (for now)
    if not use_ir:
        return im_ref, debug_info, yul_ir

    # Try and extract yul
    yul_code = None
    if artifact.platform.TYPE == Type.FOUNDRY:
        output_dir = os.path.join(artifact.working_dir, "out")
        filename_only = source_unit.filename.short.split("/")[-1]
        contract_output = contract_name + ".iropt"
        optimized_ir_filename = os.path.join(output_dir, filename_only, contract_output)

        if os.path.isfile(optimized_ir_filename):
            with open(optimized_ir_filename, "r") as f:
                yul_code = f.read()
        else:
            print(f"Could not find IR optimized output for {contract_name}")
    elif artifact.platform.TYPE == Type.SOLC:
        optimized_ir_filename = os.path.join(artifact.working_dir, contract_name+"_opt.yul")
        with open(optimized_ir_filename, "r") as f:
            yul_code = f.read()
    elif artifact.platform.TYPE == Type.HARDHAT:
        if extra_fields is not None:
            extra_fields_of_file = extra_fields.get(source_unit.filename.absolute)
            if extra_fields_of_file and (raw_yul_code := extra_fields_of_file.contract_to_ir.get(contract_name)):
                yul_code = json.dumps(raw_yul_code)

    if yul_code:
        yul_ir = YulIRCode(
            md5_bytecode=HexBytes(md5_bytecode),
            codehash=HexBytes(keccak(bytes(yul_code, 'utf8'))),
            yul_ast=yul_code
        )

    return im_ref, debug_info, yul_ir



def process(artifact: CryticCompile, extra_fields: dict, use_ir: bool) -> list[tuple[ContractSource, ContractBytecode, YulIRCode | None]]:
    contracts: list[tuple[ContractSource, ContractBytecode, YulIRCode | None]] = []

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

                im_ref, debug_info, yul_ir = extract_extra_fields(md5_bytecode, contract_name, source_unit, artifact, extra_fields, use_ir)

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
                    array_function_selectors=[
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
                    json_immutable_references=im_ref,
                    json_function_debug_info=debug_info,
                )
                bytecode = ContractBytecode(
                    md5_bytecode=HexBytes(md5_bytecode),
                    codehash=HexBytes(keccak(runtime_bytecode)),
                    bytecode=HexBytes(runtime_bytecode),
                )

                contracts.append((src, bytecode, yul_ir))

    return contracts

