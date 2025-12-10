# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


from mdse.md.simulationmanager import SimulationManager
from mdse.parser import main_read



def main():
    #-------A fcc metal. Cu with EMT
    config = main_read("cohesive_data_Cu.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.get_cohesive_energy())

    #---------Cu with Mace (Must have model_path i the .yaml)
    config = main_read("cohesive_data_Cu_mace.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.get_cohesive_energy())

    #---------MgCu2 with Mace (Must have model_path i the .yaml)
    config = main_read("cohesive_data_cif_MgCu2_mace.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.get_cohesive_energy())


    #--------A MgCu2 crystal, using EMT with parameter
    config = main_read("cohesive_data_cif_MgCu2.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.get_cohesive_energy())


    #--------NaCl with LJ
    config = main_read("cohesive_data_cif_NaCl.yaml")

    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.get_cohesive_energy())


if __name__ == "__main__":
    main()
