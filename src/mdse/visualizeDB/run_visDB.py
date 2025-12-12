# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""Main entry point for the database visualization tool.

This module orchestrates the process of generating plots from simulation data.
It reads a YAML configuration file, fetches the corresponding data from a
specified source (e.g., JSON file or MongoDB), and then iterates through the
requested plots, generating each one.
"""

from mdse.visualizeDB.read_dataDB import read_data
from mdse.parser import read_yaml_simulations
from mdse.visualizeDB.make_plot import make_plot


def run_visualize_db(config_path):
    """Runs the visualization process based on a configuration file.

    This function reads a YAML configuration file which specifies both the data
    source and the plots to be generated. It then fetches the data and
    iterates through the plot configurations, calling the appropriate plotting
    function for each.

    Args:
        config_path (str or pathlib.Path): The path to the YAML configuration file.
    """
    #Read config file
    config_data = read_yaml_simulations(config_path)

    #Get the simulation data
    sim_data = read_data(config_data.get("data"))

    #Loop over plots to make
    plot_data = config_data.get("plots")
    for plot_name, plot_info in plot_data.items():
        make_plot(plot_name, plot_info, sim_data)
