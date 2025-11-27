from mdse.md.simulationmanager import SimulationManager
from mdse.parser.parse_yml import main_read



def main():
    #A fcc metal
    config = main_read("cohesive_data.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.calc_lattice())


if __name__ == "__main__":
    main()