from pathlib import Path

import aiohttp
import dotenv
import re

CONFIG_PATH = Path.home() / ".config" / "dedaub"


def create_config_dir():
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)


def load_envfile():
    dotenv.load_dotenv(CONFIG_PATH / "credentials")


async def get_latest_app_version() -> str:

    async with aiohttp.ClientSession(
        headers={'Accept': 'application/vnd.github.v3+json'}, json_serialize=lambda x: x.json()
    ) as session:
        url = 'https://api.github.com/repos/Dedaub/srcup/tags'

        req = await session.get(url=url)

        data = await req.json()
        version = data[0]['name']

        if req.status == 200:
            return re.sub('[^0-9.]', '', version)
        else:
            return ''
