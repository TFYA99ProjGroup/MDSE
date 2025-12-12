# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


from mdse.md.resultMD import ResultMD
from mdse.md.visualize import VisualizeResult
from mdse.rm.runmanager import RunManager
from mdse.md.simulationmanager import SimulationManager
from mdse.parser.parse_yml import main_read

def main():

    config1 = main_read("fcc_metals_1.yaml")
    config2 = main_read("fcc_metals_2.yaml")
    config3 = main_read("fcc_metals_3.yaml")

    sm1 = SimulationManager(list(config1[0].values())[0])
    sm2 = SimulationManager(list(config2[0].values())[0])
    sm3 = SimulationManager(list(config3[0].values())[0])
    
    res1 = sm1.simulate_nve()
    res1.name = "Copper"
    res2 = sm2.simulate_nve()
    res2.name = "Gold"
    res3= sm3.simulate_nve()
    res3.name = "Nickel"

    vis = VisualizeResult([res1,res2,res3])
    vis.plot_energy("tot")
    vis.plot_DOS()
    vis.plot_energy("kin")
    vis.plot_MSD()
    vis.plot_scatter("lindemann","self_diff","avg_a")


if __name__ == "__main__":
    main()
