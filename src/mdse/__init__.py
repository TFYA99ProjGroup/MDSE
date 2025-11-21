"""
Molecular Dynamics Simulation Environment
=========================================

The mdse package provides tools for running molecular dynamics simulations,
managing simulation results, parsing YAML input files, logging, and
command-line utilities.

Subpackages
-----------

- mdse.cli       : Command-line interface functions
- mdse.logging   : Logging configuration and utilities
- mdse.md        : Core molecular dynamics simulations
- mdse.parser    : YAML parsing and parameter handling
- mdse.rm        : Runmanagers

For detailed documentation, see the submodules below.
"""

from . import cli as cli
from . import logging as logging
from . import md as md
from . import parser as parser
from . import rm as rm
