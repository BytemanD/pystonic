import abc
import argparse
import importlib
import pkgutil

import pluggy
from loguru import logger

import pystonic.plugins

hookspec = pluggy.HookspecMarker("pystonic")
hookimpl = pluggy.HookimplMarker("pystonic")


class SubparserSpec:
    """
    Base class for subparser plugins.
    """

    @hookspec
    def register_subcommand(self, subparsers: argparse._SubParsersAction) -> None:
        """Register a subparser for this plugin."""
        pass


class CommandPlugin(abc.ABC):
    name = ""

    @abc.abstractmethod
    def run(self, args: argparse.Namespace):
        pass


def load_plugins(subparsers: argparse._SubParsersAction):
    pm = pluggy.PluginManager("pystonic")
    pm.add_hookspecs(SubparserSpec)

    plugin_modules = [
        x
        for _, x, _ in pkgutil.iter_modules(pystonic.plugins.__path__)
        if x[1] != "__init__"
    ]

    for x in plugin_modules:
        try:
            model = importlib.import_module(f"pystonic.plugins.{x}")
        except ImportError as e:
            logger.warning("Failed to import plugin {}: {}", f"pystonic.plugins.{x}", e)
            continue
        plugin_class = getattr(model, "Command", None)
        if (
            not plugin_class
            or not issubclass(plugin_class, CommandPlugin)
            or (not plugin_class.name)
        ):
            continue
        pm.register(plugin_class(), name=plugin_class.name)

    pm.hook.register_subcommand(subparsers=subparsers)

    return pm
