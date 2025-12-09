# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


import matplotlib.pyplot as plt
import logging
import numpy as np

#pip install pandas matplotlib seaborn
import pandas as pd
import seaborn as sns


logger = logging.getLogger(__name__)

def get_label_name(property):
    """For a property, like "MSD", get the correct label we can use in scatter plot.

    args:
        propery(str): The property, in config format.
    returns:
        (str): The property in nice label format.
    """
    labels = {"MSD": "Means square displacement", "temperature": "Temperapure (K)",
              "Lindeman":"Lindeman",
              "self_diff":"Self diffusion", "energy": "Energy"}

    prop_label = labels.get(property)

    if not prop_label:
        raise ValueError(f"Could not find axis label/name for {property}")

    return prop_label

def get_defect_cat(defect_name):
    """Takes defect name, like "Int_Na" or "Na_C" and extracts what type(s)
    of defect it is, and what element(s)

    args:
        defect_name(str): The defect name

    returns:
        (str): Name of the defect
        (str): Name of the element
    """
    if defect_name.startswith("Int_"):
        return "interstitial", defect_name[len("Int_"):]
    if defect_name.endswith("_C") and "Vac" not in defect_name:
        return "substitution", defect_name[:-len("_C")]
    if "Vac_C" in defect_name:
        return "vacancy", "C"

    return "BAD defect"

def single_defect_plot(plot_name, plot_data, sim_data):
    """
    Plots 4 subplots, one for each defect.
    Each subplot should contain all the elements.
    Will get multiple points per element, because of starting positioning differs.
    4 plots because inter and sub, then these 2 but with vacancy added.

    args:
        plot_name(str): Name of the plot
        plot_data(dic): Data about the plot. What axis etc.
        sim_data(dic): Where the data we plot is.
    """
    logger.debug(f"Start to make single_defect_plot for {plot_name}")
    s_elements = ["Li","Na","K","Rb","Cs","Fr",
                "Be","Mg","Ca","Sr","Ba","Ra"]

    p_elements = ["B","Al","Ga","In","Tl","Nh",
                "C","Si","Ge","Sn","Pb","Fl",
                "N","P","As","Sb","Bi","Mc",
                "O","S","Se","Te","Po","Lv",
                "F","Cl","Br","I","At","Ts",
                "He","Ne","Ar","Kr","Xe","Rn","Og"]
    all_elements = sorted(s_elements+p_elements)

    sorted_data = {"interstitial" : {"element" : [], "energy" : [], "vacancy" : [],
                                     "spin": []},
     "substitution" : {"element" : [], "energy" : [], "vacancy" : [], "spin" : []}}
    logger.debug("Start to loop trough simulations")

    how_many_data_points = 0

    for sim in sim_data:
        #Pick out single defect
        amount = sim.get("DefectInfo")["defect_size"]
        def_type = sim.get("DefectInfo")["defect_type"]
        vacant = sim.get("DefectInfo")["vacancy"]

        if not vacant and amount == 2:
            continue

        if amount == 2: #Must be a vacancy + defect
            types = def_type.split(":")
            cat1, el1 = get_defect_cat(types[0])
            cat2, el2 = get_defect_cat(types[1])
            if cat1 == cat2 == "vacancy": #So skip this edge case in this plot
                continue
            #One vacant, one either sub or inter
            if cat1 == "vacancy":
                defect = sorted_data.get(cat2)
                defect["element"].append(el2)
                defect["energy"].append(sim.get("delta_E"))
                defect["spin"].append(sim.get("spin"))
                defect["vacancy"].append(True)
                how_many_data_points+=1
                continue

            if cat2 == "vacancy":
                defect = sorted_data.get(cat1)
                defect["element"].append(el1)
                defect["energy"].append(sim.get("delta_E"))
                defect["spin"].append(sim.get("spin"))
                defect["vacancy"].append(True)
                how_many_data_points+=1
                continue

        if amount == 1 and not vacant: #A single defect. Skip edge case of single vacant
            cat, el = get_defect_cat(def_type)
            defect = sorted_data.get(cat)
            defect["element"].append(el)
            defect["energy"].append(sim.get("delta_E"))
            defect["spin"].append(sim.get("spin"))
            defect["vacancy"].append(False)
            how_many_data_points+=1
            continue

    logger.debug("Done looping over simulations.")

    fig, axs = plt.subplots(nrows = 4, figsize = (10,10),
                            sharex = False, constrained_layout = True)
    #fig.tight_layout()

    #Fix axis of all subplots.
    print(how_many_data_points)
    avg = plot_data.get("average")
    fix_y = plot_data.get("fix_y")

    logger.debug("Fix axis for the 4 subplots")
    for axel in axs:
        axel.set_xlim(0,19)
        axel.set_xlabel("Element")
        axel.set_ylabel("ΔE (eV)")
        axel.axhline(y=0, color='gray', linestyle='--', linewidth=1)
        if fix_y:
            axel.set_ylim(-1,11)
            axel.set_yticks([0,10])

    s_elements = [""] + ["Li","Na","K","Rb","Cs","Fr",
                "Be","Mg","Ca","Sr","Ba","Ra"]

    p_elements = ["B","Al","Ga","In","Tl","Nh",
                "C","Si","Ge","Sn","Pb","Fl",
                "N","P","As","Sb","Bi","Mc",
                "O","S","Se","Te","Po","Lv",
                "F","Cl","Br","I","At","Ts",
                "He","Ne","Ar","Kr","Xe","Rn","Og"] + [""]

    all_elements = s_elements+p_elements

    #----------------Single, interstitial
    logger.debug("Start generating first subplot")
    ax1 = axs[0]
    x_pos = range(0,51)
    ax1.set_xticks(x_pos,all_elements)
    ax1.set_title("Interstitial")

    sc1 = None
    first_label = True
    avg_x = []
    avg_y = []

    #Map each element to a x-position
    elements = {el: idx for idx, el in enumerate(all_elements) if el != ""}
    candidates = sorted_data["interstitial"]
    for key,value in elements.items():

        # Indices where this element appears in interstitial data
        idxs = [i for i, e in enumerate(candidates["element"]) if e == key
                and not candidates["vacancy"][i]]
        if not idxs:
            if avg_x:
                ax1.plot(avg_x,avg_y, linestyle = "--", color="orange")
                avg_x = []
                avg_y = []
            continue

        energies = [candidates["energy"][i] for i in idxs]
        spins = [candidates["spin"][i] for i in idxs]
        lenght = len(energies)

        sc1 = ax1.scatter([value]*lenght, energies, c = spins, vmin = -0.5, vmax=2.5)

        if avg:
            avg_temp = plot_avg(ax1,value,energies)
            avg_y.append(avg_temp)
            avg_x.append(value)
            if first_label:
                ax1.legend(loc="upper right")
                first_label = False

    if sc1 is not None:
        fig.colorbar(sc1,ax=ax1, label = "Spin")
    if avg and avg_x:
        ax1.plot(avg_x,avg_y, linestyle = "--", color="orange")
    logger.debug("Done generarating first subplot")

    #----------------Interstitial + vacancy
    logger.debug("Generate second subplot")
    ax2 = axs[1]
    x_pos = range(0,51)
    ax2.set_xticks(x_pos,all_elements)
    ax2.set_title("Interstitial + vacancy")

    sc2 = None
    first_label = True
    avg_x = []
    avg_y = []

    #Map each element to a x-position
    elements = {el: idx for idx, el in enumerate(all_elements) if el != ""}
    candidates = sorted_data["interstitial"]
    for key,value in elements.items():

        # Indices where this element appears in interstitial data
        idxs = [i for i, e in enumerate(candidates["element"]) if e == key
                and candidates["vacancy"][i]]
        if not idxs:
            if avg_x:
                ax2.plot(avg_x,avg_y, linestyle = "--", color="orange")
                avg_x = []
                avg_y = []
            continue

        energies = [candidates["energy"][i] for i in idxs]
        spins = [candidates["spin"][i] for i in idxs]
        lenght = len(energies)

        sc2 = ax2.scatter([value]*lenght, energies, c = spins, vmin = -0.5, vmax=2.5)

        if avg:
            avg_temp = plot_avg(ax2,value,energies)
            avg_y.append(avg_temp)
            avg_x.append(value)
            if first_label:
                ax2.legend(loc="upper right")
                first_label = False

    if sc2 is not None:
        fig.colorbar(sc2,ax=ax2, label = "Spin")
    if avg and avg_x:
        ax2.plot(avg_x,avg_y, linestyle = "--", color="orange")
    logger.debug("Done generating second subplot")

    #----------------Substitution
    logger.debug("Start generating third subplot")
    ax3 = axs[2]
    x_pos = range(0,51)
    ax3.set_xticks(x_pos,all_elements)
    ax3.set_title("Substitution")

    sc3 = None
    first_label = True
    avg_x = []
    avg_y = []

    #Map each element to a x-position
    elements = {el: idx for idx, el in enumerate(all_elements) if el != ""}
    candidates = sorted_data["substitution"]
    for key,value in elements.items():

        # Indices where this element appears in interstitial data
        idxs = [i for i, e in enumerate(candidates["element"]) if e == key
                and not candidates["vacancy"][i]]
        if not idxs:
            if avg_x:
                ax3.plot(avg_x,avg_y, linestyle = "--", color="orange")
                avg_x = []
                avg_y = []
            continue

        energies = [candidates["energy"][i] for i in idxs]
        spins = [candidates["spin"][i] for i in idxs]
        lenght = len(energies)

        sc3 = ax3.scatter([value]*lenght, energies, c = spins, vmin = -0.5, vmax=2.5)

        if avg:
            avg_temp = plot_avg(ax3,value,energies)
            avg_y.append(avg_temp)
            avg_x.append(value)
            if first_label:
                ax3.legend(loc="upper right")
                first_label = False

    if sc3 is not None:
        fig.colorbar(sc3,ax=ax3, label = "Spin")
    if avg and avg_x:
        ax3.plot(avg_x,avg_y, linestyle = "--", color="orange")
    logger.debug("Done generating third subplot")

    #----------------Substitution + vacancy
    logger.debug("Start generating forth subplot")
    ax4 = axs[3]
    x_pos = range(0,51)
    ax4.set_xticks(x_pos,all_elements)
    ax4.set_title("Substitution + vacancy")

    sc4 = None
    first_label = True
    avg_x = []
    avg_y = []

    #Map each element to a x-position
    elements = {el: idx for idx, el in enumerate(all_elements) if el != ""}
    candidates = sorted_data["substitution"]
    for key,value in elements.items():

        # Indices where this element appears in interstitial data
        idxs = [i for i, e in enumerate(candidates["element"]) if e == key
                and candidates["vacancy"][i]]
        if not idxs:
            if avg_x:
                ax4.plot(avg_x,avg_y, linestyle = "--", color="orange")
                avg_x = []
                avg_y = []
            continue

        energies = [candidates["energy"][i] for i in idxs]
        spins = [candidates["spin"][i] for i in idxs]
        lenght = len(energies)

        sc4 = ax4.scatter([value]*lenght, energies, c = spins, vmin = -0.5, vmax=2.5)

        if avg:
            avg_temp = plot_avg(ax4,value,energies)
            avg_y.append(avg_temp)
            avg_x.append(value)
            if first_label:
                ax4.legend(loc="upper right")
                first_label = False

    if sc4 is not None:
        fig.colorbar(sc4,ax=ax4, label = "Spin")
    if avg and avg_x:
        ax4.plot(avg_x,avg_y, linestyle = "--", color="orange")
    logger.debug("Done generating forth subplot")

    logger.debug(f"Sucesfully created all subplots for {plot_name}")
    plt.gcf().savefig(f"{plot_name}.png")
    plt.close()
    logger.debug(f"Saved doping plot for {plot_name}")



def symmetrize(df):
    """Make a symmetric matrix from a grouped DataFrame."""
    return df.combine_first(df.T)

def heatmap_plot(plot_name,plot_data,sim_data):
    """
    Heatmap of substitution-interstition or
    substitution-substition + interstition-interstion defect.
    """
    data_points = []

    #What to plot. Get from sim_data later
    prop1 = plot_data.get("x")
    prop2 = plot_data.get("y")
    how_many_points = 0
    if not prop1 or not prop2:
        raise ValueError("Config is missing x or y field in config file")

    for sim in sim_data:
        #Pick out double defect,
        amount = sim.get("DefectInfo")["defect_size"]
        def_type = sim.get("DefectInfo")["defect_type"]
        if amount != 2:
            continue

        types = def_type.split(":")
        cat1, el1 = get_defect_cat(types[0])
        cat2, el2 = get_defect_cat(types[1])

        if prop1==prop2:
            if cat1 == "interstitial" and cat2 == "interstitial":
                el_sorted = sorted([el1, el2])
                data_points.append({"interstitial1" : el_sorted[0],
                                    "interstitial2" : el_sorted[1],
                                    "Energy" : sim.get("delta_E")})
                how_many_points+=1
                continue

            if cat1 == "substitution" and cat2 == "substitution":
                el_sorted = sorted([el1, el2])
                data_points.append({"substitution1" : el_sorted[0],
                                    "substitution2" : el_sorted[1],
                                    "Energy" : sim.get("delta_E")})
                how_many_points+=1
                continue
            
            continue

        if {cat1,cat2} == {"substitution", "interstitial"}:
            data_points.append({cat1 : el1,
                                cat2 : el2,
                                "Energy" : sim.get("delta_E")})
            how_many_points+=1
            continue


    s_elements = ["Li","Na","K","Rb","Cs","Fr",
                "Be","Mg","Ca","Sr","Ba","Ra"]

    p_elements = ["B","Al","Ga","In","Tl","Nh",
                "C","Si","Ge","Sn","Pb","Fl",
                "N","P","As","Sb","Bi","Mc",
                "O","S","Se","Te","Po","Lv",
                "F","Cl","Br","I","At","Ts",
                "He","Ne","Ar","Kr","Xe","Rn","Og"]
    all_elements = sorted(s_elements+p_elements)

    dataframe = pd.DataFrame(data_points)
    #heatmap_data = dataframe.pivot(index="interstitial",
    #columns="substitution", values="Energy")
    print(how_many_points)
    if prop1 == prop2:
        #So a single heatmap, that combines inter-inter with sub-sub

        df_sub = dataframe[[c for c in dataframe.columns
                            if "substitution" in c or c=="Energy"]]
        df_int = dataframe[[c for c in dataframe.columns
                            if "interstitial" in c or c=="Energy"]]
        if "interstitial1" in df_int and "interstitial2" in df_int:
            heatmap_int = df_int.groupby(['interstitial1',
                            'interstitial2'])['Energy'].mean().unstack()
        else:
            heatmap_int = pd.DataFrame(index=all_elements, columns=all_elements)
        if "substitution1" in df_sub and "substitution2" in df_sub:
            heatmap_sub = df_sub.groupby(['substitution1',
                                        'substitution2'])['Energy'].mean().unstack()
        else:
            heatmap_sub = pd.DataFrame(index=all_elements, columns=all_elements)

        #Symmetrize so both halves are filled
        heatmap_sub = symmetrize(heatmap_sub).reindex(index=all_elements,
                                                      columns=all_elements)
        heatmap_int = symmetrize(heatmap_int).reindex(index=all_elements,
                                                      columns=all_elements)

        #Combine the two into 1
        n = len(all_elements)
        upper_mask = np.triu(np.ones((n, n), dtype=bool), k=1)
        lower_mask = np.tril(np.ones((n, n), dtype=bool), k=-1)

        upper = heatmap_sub.where(upper_mask)
        lower = heatmap_int.where(lower_mask)
        heatmap_data = upper.combine_first(lower)

        #Blank diagonal
        np.fill_diagonal(heatmap_data.values, np.nan)


        #Save both diagonals separately into seperate plots
        diag_sub = pd.Series(
            [heatmap_sub.loc[e, e] if (e in heatmap_sub.index and
                                       e in heatmap_sub.columns)
             else np.nan for e in all_elements],
            index=all_elements
        )
        diag_int = pd.Series(
            [heatmap_int.loc[e, e] if (e in heatmap_int.index and
                                       e in heatmap_int.columns)
             else np.nan for e in all_elements],
            index=all_elements
        )

        #Plot
        fig, axes = plt.subplots(1, 3, figsize=(36,16),
                                 gridspec_kw={'width_ratios':[4,1,1]})


        sns.heatmap(heatmap_data, annot=False, cmap="viridis",
                    cbar_kws={'label': 'Energy'}, ax=axes[0])
        axes[0].plot(np.arange(n)+0.5, np.arange(n)+0.5, color='black', linewidth=2)
        axes[0].set_title("Double Defect Energy Heatmap (Sub-Sub upper, Int-Int lower)")
        axes[0].set_xlabel("Element 2")
        axes[0].set_ylabel("Element 1")

        #Sub-Sub
        diag_sub.plot(kind="bar", ax=axes[1], color="steelblue")
        axes[1].set_title("Diagonal (Sub-Sub)")
        axes[1].set_ylabel("Energy")
        axes[1].tick_params(axis='x', rotation=90)

        #Int-Int
        diag_int.plot(kind="bar", ax=axes[2], color="darkorange")
        axes[2].set_title("Diagonal (Int-Int)")
        axes[2].set_ylabel("Energy")
        axes[2].tick_params(axis='x', rotation=90)

        plt.tight_layout()
        plt.savefig(f"{plot_name}.png")
        plt.close()

        logger.debug(f"Created combined heatmap for {plot_name}")

    else:
        #If inter-sub
        heatmap_data = dataframe.groupby(["interstitial",
                                          "substitution"])["Energy"].mean().unstack()
        x_label = "interstitial"
        y_label = "substitution"
        heatmap_data = heatmap_data.reindex(index=p_elements+s_elements,
                                            columns=s_elements+p_elements)

        plt.figure(figsize=(20,16))
        sns.heatmap(heatmap_data, annot=True, fmt=".2f", cmap="viridis",
                    cbar_kws={'label': 'Energy'})
        plt.title("Double Defect Energy Heatmap")
        plt.xlabel(x_label)
        plt.ylabel(y_label)

        plt.gcf().savefig(f"{plot_name}.png")
        plt.close()

        logger.debug(f"Created inter-sub heatmap for {plot_name}")


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

        If config containts "average" field, will
        plot the average for each element also.

    args:
        plot_name(str): Name of the plot, from config file.
        Used as naming when plot is saved.
        plot_data(dic): Info about the plot. Empty when doping plot, and not used.
        sim_data(dic): Data about the simulations.
    """
    logger.debug(f"Starting to create doping plot for {plot_name}")
    sorted_data = {}

    avg = plot_data.get("average")
    fix_y = plot_data.get("fix_y")

    #Sort data after doping type. {"H" : {...}, "Li" : {...}}
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

    fig, axs = plt.subplots(nrows = 5, figsize = (10,12), sharex = False)

    #Fix axis of all subplots.

    for axel in axs:
        axel.set_xlim(0,19)
        axel.set_xlabel("Element of doping")
        axel.set_ylabel("ΔE (eV)")
        axel.axhline(y=0, color='gray', linestyle='--', linewidth=1)
        if fix_y:
            axel.set_ylim(-1,11)
            axel.set_yticks([0,10])



    #First subplot. H and He
    first_label = True
    logger.debug(f"Creating first defect-subplot in {plot_name}")
    ax1 = axs[0]
    x_pos = range(0,20)
    labels =  [""] + ["H"] + [""]*16 + ["He"] + [""]
    ax1.set_xticks(x_pos,labels)

    avg_x=[]
    avg_y=[]

    sc1 = None

    if "H" in sorted_data:
        sc1 = ax1.scatter([1]*len(sorted_data["H"]["formation_energy"]),
                    sorted_data["H"]["formation_energy"],
                    c = sorted_data["H"]["avg_a"])
        if avg:
            avg_temp = plot_avg(ax1,1,sorted_data["H"]["formation_energy"])
            avg_y.append(avg_temp)
            avg_x.append(1)
            if first_label:
                ax1.legend(loc="upper right")
                first_label = False


    if "He" in sorted_data:
        sc1 = ax1.scatter([18]*len(sorted_data["He"]["formation_energy"]),
                    sorted_data["He"]["formation_energy"],
                    c = sorted_data["He"]["avg_a"])
        if avg:
            plot_avg(ax1,18,sorted_data["He"]["formation_energy"])
            avg_y.append(avg_temp)
            avg_x.append(18)
            if first_label:
                ax1.legend(loc="upper right")
                first_label = False

    if sc1 is not None:
        fig.colorbar(sc1,ax=ax1, label = "Mean a")
    if avg:
        ax1.plot(avg_x,avg_y, linestyle = "--", color="orange")
    logger.debug(f"Sucessfully created first defect-subplot in {plot_name}")

    #Second subplot. Li, Be, B, C, N, O, F, Ne
    logger.debug(f"Creating second defect-subplot in {plot_name}")
    ax2 = axs[1]
    x_pos = range(0,20)
    labels =  [""] + ["Li"] + ["Be"] + [""]*10 + ["B"] +  ["C",
                "N"] +  ["O"] +  ["F"] + ["Ne"] + [""]
    ax2.set_xticks(x_pos,labels)

    sc2 = None
    first_label = True
    avg_x = []
    avg_y = []

    elements = {"Li" : 1, "Be" : 2, "dummy": 3, "B" : 13, "C" : 14,
                "N" : 15, "O" : 16, "F" : 17, "Ne" : 18}
    for key,value in elements.items():
        if key not in sorted_data:
            if avg_x:
                ax2.plot(avg_x,avg_y, linestyle = "--", color="orange")
                avg_x = []
                avg_y = []
            continue
        lenght = len(sorted_data[key]["formation_energy"])
        energy = sorted_data[key]["formation_energy"]
        avg_a = sorted_data[key]["avg_a"]

        sc2 = ax2.scatter([value]*lenght, energy, c = avg_a)

        if avg:
            avg_temp = plot_avg(ax2,value,energy)
            avg_y.append(avg_temp)
            avg_x.append(value)
            if first_label:
                ax2.legend(loc="upper right")
                first_label = False

    if sc2 is not None:
        fig.colorbar(sc2,ax=ax2, label = "Mean a")
    if avg and avg_x:
        ax2.plot(avg_x,avg_y, linestyle = "--", color="orange")
    logger.debug(f"Sucessfully created second defect-subplot in {plot_name}")

    #Third subplot. Li, Be, B, C, N, O, F, Ne
    logger.debug(f"Creating third defect-subplot in {plot_name}")
    ax3 = axs[2]
    x_pos = range(0,20)
    labels =  [""] + ["Na"] + ["Mg"] + [""]*10 + ["Al"] +  ["Si"] +  ["P"] +  ["S",
                "Cl"] + ["Ar"] + [""]
    ax3.set_xticks(x_pos,labels)

    sc3 = None
    first_label = True
    avg_x = []
    avg_y = []

    elements = {"Na" : 1, "Mg" : 2, "dummy" : 3, "Al" : 13, "Si" : 14, "P" : 15,
                "S" : 16, "Cl" : 17, "Ar" : 18}
    for key,value in elements.items():
        if key not in sorted_data:
            if avg_x:
                ax3.plot(avg_x,avg_y, linestyle = "--", color="orange")
                avg_x = []
                avg_y = []
            continue
        lenght = len(sorted_data[key]["formation_energy"])
        energy = sorted_data[key]["formation_energy"]
        avg_a = sorted_data[key]["avg_a"]

        sc3 = ax3.scatter([value]*lenght, energy, c = avg_a)

        if avg:
            avg_temp = plot_avg(ax3,value,energy)
            avg_y.append(avg_temp)
            avg_x.append(value)
            if first_label:
                ax3.legend(loc="upper right")
                first_label = False

    if sc3 is not None:
        fig.colorbar(sc3,ax=ax3, label = "Mean a")
    if avg and avg_x:
        ax3.plot(avg_x,avg_y, linestyle = "--", color="orange")
    logger.debug(f"Sucessfully created third defect-subplot in {plot_name}")

    #Forth subplot.
    logger.debug(f"Creating forth defect-subplot in {plot_name}")
    ax4 = axs[3]
    x_pos = range(0,20)
    labels =["", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co",
             "Ni", "Cu", "Zn", "Ga"
             ,"Ge", "As", "Sc", "Br", "Kr", ""]
    ax4.set_xticks(x_pos,labels)

    sc4 = None
    first_label = True
    avg_x = []
    avg_y = []

    elements = {"K" : 1, "Ca" : 2, "Sc" : 3, "Ti" : 4, "V" : 5, "Cr" : 6, "Mn" : 7,
                "Fe" : 8, "Co" : 9, "Ni" : 10, "Cu" : 11, "Zn" : 12, "Ga" : 13
             ,"Ge" : 14, "As" : 15, "Se" : 16, "Br" : 17, "Kr" : 18, }
    for key,value in elements.items():
        if key not in sorted_data:
            if avg_x:
                ax4.plot(avg_x,avg_y, linestyle = "--", color="orange")
                avg_x = []
                avg_y = []
            continue
        lenght = len(sorted_data[key]["formation_energy"])
        energy = sorted_data[key]["formation_energy"]
        avg_a = sorted_data[key]["avg_a"]

        sc4 = ax4.scatter([value]*lenght, energy, c = avg_a)

        if avg:
            avg_temp = plot_avg(ax4,value,energy)
            avg_y.append(avg_temp)
            avg_x.append(value)
            if first_label:
                ax4.legend(loc="upper right")
                first_label = False

    if sc4 is not None:
        fig.colorbar(sc4,ax=ax4, label = "Mean a")
    if avg and avg_x:
        ax4.plot(avg_x,avg_y, linestyle = "--", color="orange")
    logger.debug(f"Sucessfully created forth defect-subplot in {plot_name}")

    #Fifth subplot.
    logger.debug(f"Creating fifth defect-subplot in {plot_name}")
    ax5 = axs[4]
    x_pos = range(0,20)
    labels =["", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd",
             "Ag", "Cd", "In"
             ,"Sn", "Sb", "Te", "I", "Xe", ""]
    ax5.set_xticks(x_pos,labels)

    sc5 = None
    first_label = True
    avg_x = []
    avg_y = []

    elements = {"Rb" : 1, "Sr" : 2, "Y" : 3, "Zr" : 4, "Nb" : 5, "Mo" : 6, "Tc" : 7,
                "Ru" : 8,
                "Rh" : 9, "Pd" : 10, "Ag" : 11, "Cd" : 12, "In" : 13
             ,"Sn" : 14, "Sb" : 15, "Te" : 16, "I" : 17, "Xe" : 18, }
    for key,value in elements.items():
        if key not in sorted_data:
            if avg_x:
                ax5.plot(avg_x,avg_y, linestyle = "--", color="orange")
                avg_x = []
                avg_y = []
            continue
        lenght = len(sorted_data[key]["formation_energy"])
        energy = sorted_data[key]["formation_energy"]
        avg_a = sorted_data[key]["avg_a"]

        sc5 = ax5.scatter([value]*lenght, energy, c = avg_a)

        if avg:
            avg_temp = plot_avg(ax5,value,energy)
            avg_y.append(avg_temp)
            avg_x.append(value)
            if first_label:
                ax5.legend(loc="upper right")
                first_label = False

    if sc5 is not None:
        fig.colorbar(sc5,ax=ax5, label = "Mean a")
    if avg and avg_x:
        ax5.plot(avg_x,avg_y, linestyle = "--", color="orange")
    logger.debug(f"Sucessfully created fifth defect-subplot in {plot_name}")



    logger.debug(f"Sucesfully created all subplots for {plot_name}")
    plt.gcf().savefig(f"{plot_name}.png")
    plt.close()
    logger.debug(f"Saved doping plot for {plot_name}")


def plot_avg(axial, x_pos, y_values):
    """Plots a orange square to mark average of the y values.
    Returns the average value, so can draw line between them all laters

    args:
        axial: The axis (ax1,ax2) returned from when we created the subplot. Axial
               is the subplot we whant to attach this average.
        x_pos(int): What x position to place the average on.
        y_values(list): The values we calc. average of and mark.

    returns:
        average(float): The average of y_values
    """
    average = np.mean(y_values)
    axial.scatter([x_pos], average, color = "orange",
                marker = "s", label="average", facecolors = "none", s = 80)
    return average
