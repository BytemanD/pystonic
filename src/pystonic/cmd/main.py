import click
import dotenv
from importlib import import_module

from pystonic import set_app_name
from pystonic.common.log import setup_logger


@click.group()
def root():
    dotenv.load_dotenv()
    set_app_name("pystonic")
    setup_logger(remove=True)


def main():
    for cmd in ["agent", "code", "gitstats", "pip"]:
        try:
            m = import_module(f"pystonic.cmd.{cmd}")
        except ImportError:
            continue
        subcmd = getattr(m, "root", None)

        if isinstance(subcmd, (click.Group, click.Command)):
            root.add_command(subcmd)

    root()


if __name__ == "__main__":
    main()
