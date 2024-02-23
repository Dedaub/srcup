from datetime import datetime
from enum import Enum

from typing import Any, Annotated

from pydantic import ConfigDict, BaseModel, errors, PlainValidator, StringConstraints, PlainSerializer


def hex_bytes_validator(val: Any) -> bytes:
    if isinstance(val, bytes):
        return val
    elif isinstance(val, bytearray):
        return bytes(val)
    elif isinstance(val, str):
        return bytes.fromhex(val.removeprefix("0x"))
    raise errors.BytesError()


HexBytes = Annotated[bytes, PlainValidator(hex_bytes_validator), PlainSerializer(lambda bs: bs.hex())]
HexString = Annotated[str, StringConstraints(pattern=r"^(0x)?[0-9A-Fa-f]{2,}$"), ]


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
    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(json_encoders={bytes: lambda bs: f"0x{bs.hex()}"})

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
    debug_info: str | None
    immutable_references: str | None

class ProjectSource(ContractSource):
    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(json_encoders={bytes: lambda bs: f"0x{bs.hex()}"})

    project_id: int


class ContractBytecode(BaseModel):
    # TODO[pydantic]: The following keys were removed: `json_encoders`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(json_encoders={bytes: lambda bs: f"0x{bs.hex()}"})

    md5_bytecode: HexBytes
    codehash: HexBytes
    bytecode: HexBytes
    origin: str = "watchdog"
    _ts: datetime | None = None


class YulIRCode(BaseModel):
    model_config = ConfigDict(json_encoders={bytes: lambda bs: f"0x{bs.hex()}"})

    md5_bytecode: HexBytes
    codehash: HexBytes
    yul_ast: str
    origin: str = "watchdog"
    _ts: datetime | None = None

