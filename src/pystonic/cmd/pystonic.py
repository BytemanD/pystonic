import argparse
import sys
from typing import Optional

from pystonic.core.plugin import CommandPlugin, load_plugins


def main():
    parser = argparse.ArgumentParser(
        description="Pystonic Tools",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    pm = load_plugins(subparsers)

    args = parser.parse_args()
    plugin: Optional[CommandPlugin] = pm.get_plugin(args.command)
    if plugin is None:
        print(f"ERROR: Plugin {args.command} not found")
        sys.exit(1)
    plugin.run(args)


if __name__ == "__main__":
    main()
