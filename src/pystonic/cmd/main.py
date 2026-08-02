import argparse
import sys
from typing import Optional

import click

from pystonic.cmd import agent
from pystonic.core.plugin import CommandPlugin, load_plugins
from pystonic.log import setup_logger


@click.group()
def root():
    setup_logger(remove=True)
    pass


def main():
    root.add_command(agent.root)
    root()


if __name__ == "__main__":
    main()
