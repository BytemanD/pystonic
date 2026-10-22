import click
import dotenv

from pystonic.cmd import agent, code, gitstats, pip
from pystonic.common.log import setup_logger


@click.group()
def root():
    dotenv.load_dotenv()
    setup_logger(remove=True)


def main():
    root.add_command(agent.root)
    root.add_command(gitstats.root)
    root.add_command(pip.root)
    root.add_command(code.root)
    root()


if __name__ == "__main__":
    main()
