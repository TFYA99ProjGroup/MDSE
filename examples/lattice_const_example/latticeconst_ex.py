from mdse.md.simulationmanager import SimulationManager
from mdse.parser.parse_yml import main_read



def main():

    #CuO with mace, monoclinic
    config = main_read("cohesive_data_cif_CuO_mace.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.calc_lattice())

    #MgCu2 with mace, cubic
    config = main_read("cohesive_data_cif_MgCu2_mace.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.calc_lattice())


    #Fe with mace, cubic
    config = main_read("cohesive_data_Fe_mace.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.calc_lattice())


    #Cu with EMT, cubic
    config = main_read("cohesive_data_Cu.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.calc_lattice())

    #Zn, hexagonal
    config = main_read("cohesive_data_cif_Zn_mace.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.calc_lattice())


if __name__ == "__main__":
    main()
