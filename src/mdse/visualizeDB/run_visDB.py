# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

from mdse.visualizeDB.read_dataDB import read_data
from mdse.parser.parse_yml import read_yaml_simulations
from mdse.visualizeDB.make_plot import make_plot




def run_visualize_db(config_path):
    #Read config file
    config_data = read_yaml_simulations(config_path)

    #Get the simulation data
    sim_data = read_data(config_data.get("data"))

    #Loop over plots to make
    plot_data = config_data.get("plots")
    for plot_name, plot_info in plot_data.items():
        make_plot(plot_name, plot_info, sim_data)
