# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""
Visualization tools for post-processing molecular dynamics simulation results.

This module provides the `VisualizeResult` class, which is designed to take a
list of `ResultMD` objects and generate various comparative plots. It allows for
the visualization of properties like Mean Squared Displacement (MSD), Density of
States (DOS), and energy evolution across multiple simulations. It also supports
creating scatter plots and histograms to analyze relationships between different
calculated properties.
"""

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import logging

logger = logging.getLogger(__name__)

class VisualizeResult:
    """
    A class for visualizing and comparing results from multiple simulations.

    This class takes a list of `ResultMD` objects and provides methods to
    generate various plots, such as MSD, DOS, energy profiles, scatter plots,
    and histograms, allowing for easy comparison across different simulation runs.
    """

    def __init__(self,data):
        """Initialize VisualizeResult object.

        Parameters
        ----------
        data : list
            A list of `ResultMD` objects to be visualized.
        """
        self.results = data
        logger.debug(
            f"Initialized a VisualizeResult object with {len(self.results)} simulations"
            )
        self.available = {"self_diff" : "calc_self_diff",
                          "lindemann" : "calc_lindemann",
                          "debye" : "calc_debye_temperature",
                          "avg_a" : "estimate_average_a",
                          "DOS" : "calc_density_of_states"}

    def plot_MSD(self):
        """
        Plot the Mean Squared Displacement (MSD) for all stored simulations.

        This method iterates through each `ResultMD` object, calculates the MSD
        for the x, y, and z directions, and plots them on a single graph.
        Each simulation is distinguished by color.
        """
        logger.debug(f"Starting to plot MSD for {len(self.results)} simulations")
        colors = cm.viridis(np.linspace(0,1,len(self.results)))

        for i, result in enumerate(self.results):
            MSD_vs_tau = result._calc_msd_list()
            plt.plot(MSD_vs_tau[0],MSD_vs_tau[1],label = f"MSD_x ({result.name})",
                     marker = "o", color = colors[i] )
            plt.plot(MSD_vs_tau[0],MSD_vs_tau[2],label = f"MSD_y ({result.name})",
                     marker = "x", color = colors[i] )
            plt.plot(MSD_vs_tau[0],MSD_vs_tau[3],label = f"MSD_z ({result.name})",
                     marker = "^", color = colors[i] )
        logger.debug("Sucessfully got MSD data to plot")

        plt.xlabel("Time lag (fs)")
        plt.ylabel("MSD (Å²)")
        plt.legend()
        plt.show()

    def plot_scatter(self, prop1, prop2, prop3, size = 30):
        """
        Create a 3D scatter plot from three calculated properties.

        This method generates a scatter plot where the x and y axes represent
        two properties, and a third property is represented by the color of
        the data points.

        Parameters
        ----------
        prop1 : str
            The name of the property for the x-axis.
        prop2 : str
            The name of the property for the y-axis.
        prop3 : str
            The name of the property for the color scale.
        size : int, optional
            The size of the markers in the scatter plot. Defaults to 30.
        """
        logger.debug(f"Starting to plot scatter for {len(self.results)} simulations")

        properties = [prop1,prop2,prop3]

        missing = [p for p in properties if p not in self.available]

        if missing:
            logger.error(
                f"Was not able to scatter plot, invalid properties given, {missing}"
                )
            raise RuntimeError(f"Invalid properties {missing}")
        logger.debug("Scatter plot got valid properties")

        x_values = [getattr(result,self.available[prop1])() for result in self.results]
        plt.xlabel(prop1)
        y_values = [getattr(result,self.available[prop2])() for result in self.results]
        plt.ylabel(prop2)
        z_values = [getattr(result,self.available[prop3])() for result in self.results]
        logger.debug("Scatter plot got data for properties sucesfully")

        plt.scatter(x_values, y_values, s= size, c = z_values)
        plt.colorbar(label = prop3)

        plt.show()

    def plot_histogram(self,prop1, bins = 100):
        """
        Plot a histogram for a single property across all simulations.

        Parameters
        ----------
        prop1 : str
            The name of the property to be plotted.
        bins : int, optional
            The number of bins to use in the histogram. Defaults to 100.
        """
        if prop1 not in self.available:
            logger.error(
                f"Was not able to histogram plot, invalid property given, {prop1}"
                )
            raise RuntimeError(f"Invalid property {prop1}")

        logger.debug("Histogram plot got valid properties")

        x_values = [getattr(result,self.available[prop1])() for result in self.results]
        plt.xlabel(prop1)
        plt.ylabel("Count")
        plt.hist(x_values)
        plt.title(f"Histogram over {prop1}, from {len(self.results)} simulations")

        plt.show()

    def plot_DOS(self):
        """
        Plot the Density of States (DOS) for all stored simulations.

        This method calculates and plots the DOS vs. angular frequency for each
        `ResultMD` object on a single graph, labeling each curve with the
        simulation's name.
        """
        DOS, omega = zip(
            *[
                getattr(result,self.available["DOS"])() for result in self.results
                ]
                )
        names = [res.name for res in self.results]
        for DOS_i, omega_i,name in zip(DOS,omega,names):
            plt.plot(omega_i,DOS_i)
            plt.text(omega_i[-1],DOS_i[-1],f"{name}")

        logger.debug("DOS plot values were sucesfully fetched")
        plt.xlabel("Angular frequency")
        plt.ylabel("DOS")
        plt.title(f"DOS vs angular frequency, for {len(self.results)} simulations")
        plt.show()

    def plot_energy(self, energy_type = "kin"):
        """
        Plot the evolution of energy over time for all stored simulations.

        Parameters
        ----------
        energy_type : str, optional
            The type of energy to plot. Valid options are:
            - "kin": Kinetic energy (default)
            - "pot": Potential energy
            - "tot": Total energy
        """

        available_energies = {"kin" : "get_kin_energies", "pot" : "get_pot_energies",
                              "tot" : "get_tot_energies"}
        labels = {"kin" : "Kinetic energy (eV)", "pot" : "Potential energy (eV)",
                  "tot" : "Total energy (eV)"}

        if energy_type not in available_energies:
            logger.error(
                f"Was not able to histogram energy, invalid energy given, {energy_type}"
                )
            raise RuntimeError(f"Invalid energy {energy_type}")


        energies = [getattr(res, available_energies[energy_type])()
                    for res in self.results]
        times = [res.get_time_axis() for res in self.results]
        names = [res.name for res in self.results]

        for time, energy, name in zip(times,energies, names):
            plt.plot(time,energy)
            plt.text(time[-1],energy[-1], f"{name}")
        logger.debug("Energy and time where succsesfully fetched")
        plt.xlabel("Time (fs)")
        plt.ylabel(labels[energy_type])
        plt.title(f"{labels[energy_type]} for {len(self.results)} simulations")
        plt.show()
