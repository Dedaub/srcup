import asyncio
from packaging import version
from pathlib import Path
from typer import Exit

import re
import importlib.metadata
import dotenv
import aiohttp

CONFIG_PATH = Path.home() / ".config" / "dedaub"
__version__ = importlib.metadata.version('srcup')

def create_config_dir():
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)


def load_envfile():
    dotenv.load_dotenv(CONFIG_PATH / "credentials")


def version_callback(show_version: bool):
    if show_version:
        print(__version__)
        raise Exit()


async def get_latest_app_version() -> str:
    async with aiohttp.ClientSession(
        headers={'Accept': 'application/vnd.github.v3+json'}, json_serialize=lambda x: x.json()
    ) as session:
        url = 'https://api.github.com/repos/Dedaub/srcup/tags'

        req = await session.get(url=url)

        if req.status == 200:
            data = await req.json()
            if data:
                return re.sub('[^0-9.]', '', data[0]['name'])
        return ''

def check_version():
    latest_app_version = asyncio.run(get_latest_app_version())
    if not latest_app_version:
        print("Warning: Failed to retrieve information about the latest release")

    elif version.parse(__version__) < version.parse(latest_app_version):
        print(f"Warning: A new version is available ({latest_app_version})\n")
        print("It's recommended that you upgrade to the latest version to get the latest features and bugfixes:")
        print("  For pipx installation run:      pipx upgrade srcup")
        print("  For plain pip installation run: pip install --upgrade git+https://github.com/Dedaub/srcup#egg=srcup")
