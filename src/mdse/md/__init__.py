# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""
MDSE Core Molecular Dynamics Package.

This package contains the core components for running molecular dynamics
simulations and processing the results. It provides a high-level interface
to the Atomic Simulation Environment (ASE) for setting up, executing, and
analyzing simulations.

Modules
-------
- `simulationmanager`: Provides the `SimulationManager` class for setting up
  and running a single MD simulation based on a configuration dictionary.
- `resultMD`: Provides the `ResultMD` class for post-processing simulation
  trajectories to calculate various physical properties like MSD, DOS, and
  thermodynamic quantities.
- `visualize`: Provides the `VisualizeResult` class for creating comparative
  plots from multiple `ResultMD` objects.
"""

from . import resultMD as resultMD
from . import simulationmanager as simulationmanager
from . import visualize as visualize
