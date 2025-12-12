# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""
MDSE Run Management Package.

This package contains modules for managing and orchestrating simulation runs
and interacting with databases.

- `runmanager`: Provides the `RunManager` class for executing lists of
  simulations, with support for MPI distribution.
- `dbmanager`: Provides the `DBManager` class for writing and reading
  simulation results to and from a MongoDB database in an OPTIMADE-compliant
  format.
"""

from . import runmanager as runmanager
from . import dbmanager as dbmanager
