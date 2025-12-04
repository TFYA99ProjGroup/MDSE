import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import logging

logger = logging.getLogger(__name__) #Need to attach Handler?

class VisualizeResult:
    """Class for visualizing ResultMD objects
    """

    def __init__(self,data):
        """Initialize VisualizeResult object.

        Args:
            data (list): List containing ResultMD objects that are to be visualized.
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
        """Collects all MSD vs tau for the list of resultMD. Then plots them togheter.
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
        """ Takes 3 properties and plots all these in a scatterplot.
        First 2 properties are on x and y axis, while third is color of data point.

        args:
            prop1 (str): Property on x-axis
            prop2 (str): Property on y-axis
            prop3 (str): Property on color scaling.
            size (int): Size of data points
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
        """Plots a histogram, based on 1 property.

        args:
            prop1(str): The propertie to plot.
            bins(int): How many bins the property should be placed in.
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
        """Plots DOS vs angular frequency, for all results saved.
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
        """Plots specified energy for all the simulations stored
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

    def plot_temp(self):
        """Calls the get_temperatues on result object to get temperature over all frames.
        Generates plot with temperature vs time.
        """
        temps = []
        times = []
        for res in self.results:
            times.append(res.get_time_axis())

        names = [res.name for res in self.results]
        for res in self.results:
            temps.append(res.get_temperatures())




        for time, temp, name in zip(times,temps, names):
            plt.plot(time,temp)
            plt.text(time[-1],temp[-1], f"{name}")
        logger.debug("Energy and time where succsesfully fetched")
        plt.xlabel("Time (fs)")
        plt.ylabel("Temperature")
        plt.title(f"Temperature for {len(self.results)} simulations")
        plt.show()
