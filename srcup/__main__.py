#!/usr/bin/env python3

from srcup.cli import app
from srcup.utils import create_config_dir, load_envfile


def main():
    create_config_dir()
    load_envfile()
    app()


if __name__ == "__main__":
    main()
