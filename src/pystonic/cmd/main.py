import click

from pystonic.cmd import agent, gitstats
from pystonic.log import setup_logger


@click.group()
def root():
    setup_logger(remove=True)
    pass


def main():
    root.add_command(agent.root)
    root.add_command(gitstats.root)
    root()


if __name__ == "__main__":
    main()
