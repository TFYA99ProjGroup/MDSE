from mdse.rm.runmanager import RunManager
from mdse.md.resultMD import ResultMD
from mdse.md.simulationmanager import SimulationManager
from mdse.parser.parse_yml import main_read



def main():
    config = main_read("cohesive_data.yaml")

    sm = SimulationManager(list(config[0].values())[0])

    sm.simulate_nve()

    res = ResultMD.from_file("Cu_100.traj")


    print(sm.single_atom_energy() - res.get_bulk_energi_per_atom())


if __name__ == "__main__":
    main()