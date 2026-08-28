import click

from pystonic.cmd import agent, code, gitstats
from pystonic.log import setup_logger


@click.group()
def root():
    setup_logger(remove=True)
    pass


def main():
    root.add_command(agent.root)
    root.add_command(gitstats.root)
    root.add_command(code.root)
    root()


if __name__ == "__main__":
    main()
