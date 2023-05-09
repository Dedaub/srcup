from pathlib import Path

import dotenv

CONFIG_PATH = Path.home() / ".config" / "dedaub"


def create_config_dir():
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)


def load_envfile():
    dotenv.load_dotenv(CONFIG_PATH / "credentials")
