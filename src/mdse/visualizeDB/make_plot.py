# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""This module provides the main entry point for creating various plots.

It contains a dispatcher function that selects the appropriate plotting
function based on the configuration and executes it with the provided data.
"""


import logging
from mdse.visualizeDB.vis_plots import (scatter_plot, doping_plot,
heatmap_plot, single_defect_plot, sub_sub_plot)

logger = logging.getLogger(__name__)




def make_plot(plot_name, plot_info, sim_data):
    """Takes information about a plot and creates it.

    This function serves as the main entry point for plotting. It attempts to
    create a plot based on the provided information. If it fails (e.g., due to
    bad information), it logs the error and continues without crashing.

    Args:
        plot_name (str): The name of the plot, used for saving the file.
        plot_info (dict): Contains plot-specific information, such as the plot
            type and other parameters.
        sim_data (list[dict]): The simulation data to be plotted.
    """

    try:
        plot_func = valid_plot(plot_info.get("type"))

        plot_func(plot_name, plot_info,sim_data)



    except Exception as e:
        print(f"Could not plot {plot_name} due to: {str(e)}")
        logger.debug(f"Could not plot {plot_name} due to: {str(e)}")


def valid_plot(plot_type):
    """Checks if the plot type is valid and returns the corresponding plot function.

    Args:
        plot_type (str): The type of plot to validate.

    Returns:
        callable: The function that creates the specified plot type.

    Raises:
        ValueError: If the plot_type is not supported.
    """

    available_types = {"scatter" : scatter_plot, "doping" : doping_plot,
                       "heatmap" : heatmap_plot,
                       "single" : single_defect_plot,
                       "sub-sub" : sub_sub_plot}

    if plot_type not in available_types:
        raise ValueError("The plot is not supported")

    return available_types[plot_type]
