import argparse
import re

from pystonic.utils.plugin import CommandPlugin, hookimpl
from pystonic.plugins.website import utils


class Command(CommandPlugin):
    name = "website"

    @hookimpl
    def register_subcommand(self, subparsers: argparse._SubParsersAction):
        parser_root = subparsers.add_parser(
            self.name, formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        parser_root.add_argument("url", help="url of http server")
        parser_root.add_argument("output", help="Output directory")
        parser_root.add_argument("-m", "--match", default=".*", help="Match with regex")

    def run(self, args):
        utils.sync_files_from_http_server(
            args.url, args.output, parttern=re.compile(args.match)
        )
