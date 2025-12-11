# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""
MDSE Configuration Parsing Package.

This package is responsible for reading and processing YAML configuration files
that define molecular dynamics simulations. It can expand concise definitions
(e.g., using parameter lists or ranges) into a full set of individual
simulation configurations.

- `parse_yml`: Contains the core logic for reading YAML files, un-nesting
  parameters like temperature or pressure, and resolving file paths. The main
  entry point is `main_read`.
"""
from . import parse_yml as parse_yml
