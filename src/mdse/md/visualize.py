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
        logger.debug(f"Initialized a VisualizeResult object with {len(self.results)} simulations")

    def plot_MSD(self):
        """Collects all MSD vs tau for the list of resultMD. Then plots them togheter
        
        """
        logger.debug(f"Starting to plot MSD for {len(self.results)} simulations")
        colors = cm.viridis(np.linspace(0,1,len(self.results)))

        for i, result in enumerate(self.results):
            MSD_vs_tau = result._calc_msd_list()
            plt.plot(MSD_vs_tau[0],MSD_vs_tau[1],label = f"MSD_x ({result.name})", marker = "o", color = colors[i] )
            plt.plot(MSD_vs_tau[0],MSD_vs_tau[2],label = f"MSD_y ({result.name})", marker = "x", color = colors[i] )
            plt.plot(MSD_vs_tau[0],MSD_vs_tau[3],label = f"MSD_z ({result.name})", marker = "^", color = colors[i] )
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
        available = {"self_diff" : "calc_self_diff", "lindemann" : "calc_lindemann", "debye" : "calc_debye_temperature",
                     "avg_a" : "estimate_average_a"}
        properties = [prop1,prop2,prop3]

        missing = [p for p in properties if p not in available]

        if missing:
            logger.debug(f"Was not able to scatter plot, invalid properties given, {missing}")
            raise RuntimeError(f"Invalid properties {missing}")
        logger.debug("Scatter plot got valid properties")

        x_values = [getattr(result,available[prop1])() for result in self.results]
        plt.xlabel(prop1)
        y_values = [getattr(result,available[prop2])() for result in self.results]
        plt.ylabel(prop2)
        z_values = [getattr(result,available[prop3])() for result in self.results]
        logger.debug("Scatter plot got data for properties sucesfully")

        plt.scatter(x_values, y_values, s= size, c = z_values)
        plt.colorbar(label = prop3)

        plt.show()

    def plot_histogram(self,prop1, bins = 100):
        """Plots a histogram    
        """
        available = {"self_diff" : "calc_self_diff", "lindemann" : "calc_lindemann", "debye" : "calc_debye_temperature",
                     "avg_a" : "estimate_average_a"}

        if prop1 not in available:
            logger.debug(f"Was not able to histogram plot, invalid property given, {prop1}")
            raise RuntimeError(f"Invalid property {prop1}")
        
        logger.debug("Histogram plot got valid properties")

        x_values = [getattr(result,available[prop1])() for result in self.results]
        plt.xlabel(prop1)
        plt.ylabel("Count")
        plt.hist(x_values)
        plt.title(f"Histogram over {prop1}, from {len(self.results)} simulations")

        plt.show()
