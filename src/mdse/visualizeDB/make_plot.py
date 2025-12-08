# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


import logging
from mdse.visualizeDB.vis_plots import (scatter_plot, doping_plot,
heatmap_plot, single_defect_plot)

logger = logging.getLogger(__name__)




def make_plot(plot_name, plot_info, sim_data):
    """Takes information about a plot, and makes it.
    If unsuccesfull, i.e bad information etc, should simply continue with next plot.
    The 'main' plotting function.

    args:
        plot_name(str): The name of the plot
        plot_info(dict): Contains what type of plot, parameters etc.
        sim_data(dict): The data from simulations. What is getting plotted
    """


    try:
        plot_func = valid_plot(plot_info.get("type"))

        plot_func(plot_name, plot_info,sim_data)



    except Exception as e:
        print(f"Could not plot {plot_name} due to: {str(e)}")
        logger.debug(f"Could not plot {plot_name} due to: {str(e)}")


def valid_plot(plot_type):
    """Checks that the type of plot is valid and supported.
    If not, will raise error. If good, then returns name of corresponding
    plot function.

    args:
        plot_type(str): The type of plot

    returns:
        ?: The name of the function that plots this type
    """

    available_types = {"scatter" : scatter_plot, "doping" : doping_plot,
                       "heatmap" : heatmap_plot,
                       "single" : single_defect_plot}

    if plot_type not in available_types:
        raise ValueError("The plot is not supported")

    return available_types[plot_type]

