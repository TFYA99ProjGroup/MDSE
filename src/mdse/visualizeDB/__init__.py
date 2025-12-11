# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""
A tool for visualizing simulation data from various sources.

This package provides a framework for generating plots from simulation data stored
in sources like JSON files or MongoDB databases. It is driven by a YAML
configuration file that specifies the data source and the desired plots.

The main entry point is :py:meth:`run_visDB.run_visualize_db`, which
orchestrates the entire process of data reading and plot generation.
"""

from . import make_plot as make_plot
from . import read_dataDB as read_dataDB
from . import run_visDB as run_visDB
from . import vis_plots as vis_plots
