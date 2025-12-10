# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""
MDSE Command-Line Interface (CLI) Package.

This package provides the entry point and command-line parsing logic for the
MDSE (Molecular Dynamics Simulation Engine) application. It allows users to
interact with the simulation, analysis, and data management functionalities
from the terminal.

The primary module, `mdse.cli.cli`, defines the main parser and all available
subcommands, such as `simulate`, `view`, `clean`, and various analysis tools.
"""
from . import cli as cli
