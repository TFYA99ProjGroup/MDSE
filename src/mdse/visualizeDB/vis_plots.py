import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

def get_label_name(property):
    """For a property, like "MSD", get the correct label we can use in plot axis.
    
    """
    labels = {"MSD": "Means square displacement", "temperature": "Temperapure (K)", "Lindeman":"Lindeman",
              "self_diff":"Self diffusion", "energy": "Energy"}
    
    prop_label = labels.get(property)

    if not prop_label:
        raise ValueError(f"Could not find axis label/name for {property}")
    
    return prop_label


def scatter_plot(plot_name, plot_data,sim_data):
    """Function to make a scatter plot.
    Plot_data specifies what properties to put on x,y and z axis.
    z-axis is color coded onto the points. If missing, then only x and y is plotted.

    args:
        plot_name(str): Name of the plot
        plot_data(dic): Data about the plot. What axis etc.
        sim_data(dic): Where the data we plot is.
    
    """
    logger.debug(f"Starting to create scatter plot for {plot_name}")
    #Check what we whant to plot on axis
    x_prop = plot_data.get("x")
    y_prop = plot_data.get("y")
    z_prop = plot_data.get("z") #Optional

    if not x_prop or not y_prop:
        raise ValueError("Config not specifying x and/or y axis for scatterplot")

    #get the properties of simulations
    x_values = [sim.get(x_prop) for sim in sim_data]
    y_values = [sim.get(y_prop) for sim in sim_data]
    if z_prop:
        z_values = [sim.get(z_prop) for sim in sim_data]
        if None in z_values:
            raise ValueError(f"Some simulation is missing {z_prop}")

    if None in x_values:
        raise ValueError(f"Some simulation is missing {x_prop}")
    
    if None in y_values:
        raise ValueError(f"Some simulation is missing {y_prop}")
    
    if z_prop:
        plt.scatter(x_values, y_values, c= z_values)
        plt.colorbar(label = get_label_name(z_prop))
    else:
        plt.scatter(x_values, y_values)

    plt.xlabel(get_label_name(x_prop))
    plt.ylabel(get_label_name(y_prop))
    logger.debug(f"Saving {plot_name} to .png file")
    plt.gcf().savefig(f"{plot_name}.png")
    plt.close()
    
def doping_plot(plot_name, plot_data,sim_data):
    """Does a plot where:
        x-axis is what element we are doping with.
        y-axis is energy difference (formation energy?).
        z-axis is "mean a" (use avg_a here).

    args:
        plot_name(str): Name of the plot, from config file. Used as naming when plot is saved.
        plot_data(dic): Info about the plot. Empty when doping plot, and not used.
        sim_data(dic): Data about the simulations.
    """
    logger.debug(f"Starting to create doping plot for {plot_name}")
    sorted_data = {}
    for sim in sim_data:
        element = sim.get("doping")
        if not element:
            raise ValueError("Some simulation doesnt have doping field")
        
        if element not in sorted_data:
            sorted_data[element] = {"formation_energy" : [], "avg_a" : [ ]}
        
        if "formation_energy" not in sim:
            raise ValueError("Some simulation doesnt have formation_energy field")
        
        if "avg_a" not in sim:
            raise ValueError("Some simulation doesnt have avg_a field")

        sorted_data[element]["formation_energy"].append(sim["formation_energy"])
        sorted_data[element]["avg_a"].append(sim["avg_a"])
    
    fig, axs = plt.subplots(nrows = 4, figsize = (10,12), sharex = False)

    #First subplot. H and He
    logger.debug(f"Creating first defect-subplot in {plot_name}")
    ax1 = axs[0]
    x_pos = range(0,20)
    labels =  [""] + ["H"] + [""]*16 + ["He"] + [""]
    ax1.set_xticks(x_pos,labels)
    ax1.set_xlim(0,19)
    ax1.set_xlabel("Element of doping")
    ax1.set_ylabel("ΔE (eV)")
    
    sc1 = None

    if "H" in sorted_data:
        sc1 = ax1.scatter([1]*len(sorted_data["H"]["formation_energy"]),
                    sorted_data["H"]["formation_energy"],
                    c = sorted_data["H"]["avg_a"])
    if "He" in sorted_data:
        sc1 = ax1.scatter([18]*len(sorted_data["He"]["formation_energy"]),
                    sorted_data["He"]["formation_energy"],
                    c = sorted_data["He"]["avg_a"])
    
    if sc1 is not None:
        fig.colorbar(sc1,ax=ax1, label = "Mean a")
    logger.debug(f"Sucessfully created first defect-subplot in {plot_name}")

    #Second subplot. Li, Be, B, C, N, O, F, Ne
    logger.debug(f"Creating second defect-subplot in {plot_name}")
    ax2 = axs[1]
    x_pos = range(0,20)
    labels =  [""] + ["Li"] + ["Be"] + [""]*10 + ["B"] +  ["C"] +  ["N"] +  ["O"] +  ["F"] + ["Ne"] + [""]
    ax2.set_xticks(x_pos,labels)
    ax2.set_xlim(0,19)
    ax2.set_xlabel("Element of doping")
    ax2.set_ylabel("ΔE (eV)")
    sc2 = None

    elements = {"Li" : 1, "Be" : 2, "B" : 13, "C" : 14, "N" : 15, "O" : 16, "F" : 17, "Ne" : 18}
    for key,value in elements.items():
        if key not in sorted_data:
            continue
        lenght = len(sorted_data[key]["formation_energy"])
        energy = sorted_data[key]["formation_energy"]
        avg_a = sorted_data[key]["avg_a"]

        sc2 = ax2.scatter([value]*lenght, energy, c = avg_a)

    if sc2 is not None:
        fig.colorbar(sc2,ax=ax2, label = "Mean a")
    logger.debug(f"Sucessfully created second defect-subplot in {plot_name}")

    #Third subplot. Li, Be, B, C, N, O, F, Ne
    logger.debug(f"Creating third defect-subplot in {plot_name}")
    ax3 = axs[2]
    x_pos = range(0,20)
    labels =  [""] + ["Na"] + ["Mg"] + [""]*10 + ["Al"] +  ["Si"] +  ["P"] +  ["S"] +  ["Cl"] + ["Ar"] + [""]
    ax3.set_xticks(x_pos,labels)
    ax3.set_xlim(0,19)
    ax3.set_xlabel("Element of doping")
    ax3.set_ylabel("ΔE (eV)")
    sc3 = None

    elements = {"Na" : 1, "Mg" : 2, "Al" : 13, "Si" : 14, "P" : 15, "S" : 16, "Cl" : 17, "Ar" : 18}
    for key,value in elements.items():
        if key not in sorted_data:
            continue
        lenght = len(sorted_data[key]["formation_energy"])
        energy = sorted_data[key]["formation_energy"]
        avg_a = sorted_data[key]["avg_a"]

        sc3 = ax3.scatter([value]*lenght, energy, c = avg_a)

    if sc3 is not None:
        fig.colorbar(sc3,ax=ax3, label = "Mean a")
    logger.debug(f"Sucessfully created third defect-subplot in {plot_name}")

    #Forth subplot.
    logger.debug(f"Creating forth defect-subplot in {plot_name}")
    ax4 = axs[3]
    x_pos = range(0,20)
    labels =["", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga"
             ,"Ge", "As", "Sc", "Br", "Kr", ""]
    ax4.set_xticks(x_pos,labels)
    ax4.set_xlim(0,19)
    ax4.set_xlabel("Element of doping")
    ax4.set_ylabel("ΔE (eV)")
    sc4 = None

    elements = {"K" : 1, "Ca" : 2, "Sc" : 3, "Ti" : 4, "V" : 5, "Cr" : 6, "Mn" : 7, "Fe" : 8, "Co" : 9, "Ni" : 10, "Cu" : 11, "Zn" : 12, "Ga" : 13
             ,"Ge" : 14, "As" : 15, "Sc" : 16, "Br" : 17, "Kr" : 19, }
    for key,value in elements.items():
        if key not in sorted_data:
            continue
        lenght = len(sorted_data[key]["formation_energy"])
        energy = sorted_data[key]["formation_energy"]
        avg_a = sorted_data[key]["avg_a"]

        sc4 = ax4.scatter([value]*lenght, energy, c = avg_a)

    if sc4 is not None:
        fig.colorbar(sc4,ax=ax4, label = "Mean a")
    logger.debug(f"Sucessfully created forth defect-subplot in {plot_name}")




    logger.debug(f"Sucesfully created all subplots for {plot_name}")
    plt.gcf().savefig(f"{plot_name}.png")
    plt.close()
    logger.debug(f"Saved doping plot for {plot_name}")
    