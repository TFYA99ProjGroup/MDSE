from mdse.rm.runmanager import RunManager
from mdse.md.resultMD import ResultMD
from mdse.md.simulationmanager import SimulationManager
from mdse.parser.parse_yml import main_read



def main():
    #A fcc metal
    config = main_read("cohesive_data.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.get_cohesive_energy())

    #A MgCu2 crystal, using EMT with parameter
    config = main_read("cohesive_data_cif_MgCu2.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.get_cohesive_energy())



    #NaCl with LJ
    config = main_read("cohesive_data_cif.yaml")

    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.get_cohesive_energy())


if __name__ == "__main__":
    main()
