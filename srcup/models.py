import re
from datetime import datetime
from enum import Enum

from typing import Any, Callable, Generator

from pydantic import BaseModel, errors, ConstrainedStr


def hex_bytes_validator(val: Any) -> bytes:
    if isinstance(val, bytes):
        return val
    elif isinstance(val, bytearray):
        return bytes(val)
    elif isinstance(val, str):
        return bytes.fromhex(val.removeprefix("0x"))
    raise errors.BytesError()


class HexBytes(bytes):
    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
        yield hex_bytes_validator

class HexString(ConstrainedStr):
    regex = re.compile("^(0x)?[0-9A-Fa-f]{2,}$")

class BuildSystem(Enum):
    # ARCHIVE = "Archive"
    BROWNIE = "Brownie"
    # BUIDLER = "Buidler"
    # DAPP = "Dapp"
    # EMBARK = "Embark"
    # ETHERLIME = "Etherlime"
    # ETHERSCAN = "Etherscan"
    HARDHAT = "Hardhat"
    SOLC = "Solc"
    # SOLC_STANDARD_JSON = "SolcStandardJson"
    STANDARD = "Standard"
    TRUFFLE = "Truffle"
    VYPER = "Vyper"
    # WAFFLE = "Waffle"
    FOUNDRY = "Foundry"


class ContractSource(BaseModel):
    class Config:
        json_encoders = {bytes: lambda bs: f"0x{bs.hex()}"}

    md5_bytecode: HexBytes
    contract_name: str
    contract_path: str
    array_source_level: list[str]
    array_source_names: list[str]
    source_map: str
    json_abi: list[dict]
    array_function_selectors: list[HexBytes]
    array_event_selectors: list[HexBytes]
    array_error_selectors: list[HexBytes]


class ProjectSource(ContractSource):
    class Config:
        json_encoders = {bytes: lambda bs: f"0x{bs.hex()}"}

    project_id: int


class ContractBytecode(BaseModel):
    class Config:
        json_encoders = {bytes: lambda bs: f"0x{bs.hex()}"}

    md5_bytecode: HexBytes
    codehash: HexBytes
    bytecode: HexBytes
    debug_info: str | None
    immutable_references: str | None
    origin: str = "watchdog"
    _ts: datetime | None = None


class YulIRCode(BaseModel):
    # class Config:
        # json_encoders = {bytes: lambda bs: f"0x{bs.hex()}"}

    md5_bytecode: HexBytes
    codehash: HexBytes
    code: str
    debug_info: str | None
    immutable_references: str | None
    origin: str = "watchdog"
    _ts: datetime | None = None

