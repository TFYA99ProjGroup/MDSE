from mdse.rm.runmanager import RunManager
from mdse.md.resultMD import ResultMD
from mdse.md.simulationmanager import SimulationManager
from mdse.parser.parse_yml import main_read


def main():
    #A fcc metal, single element, EMT
    config = main_read("cohesive_data.yaml")

    sm = SimulationManager(list(config[0].values())[0])

    res = sm.simulate_nve()

    print(res.get_cohesive_energy())

    #Noble gas
    config = main_read("cohesive_data_Ar.yaml")
    
    sm = SimulationManager(list(config[0].values())[0])

    epsilon = [[0.0103]] 
    sigma   = [[3.4]]      
    
    import ase.data

    elements = ["Ar"]
    elements_Z = [ase.data.atomic_numbers[sym] for sym in elements]

    calc_parameters = {"elements" : elements_Z, "epsilon" : epsilon, "sigma" : sigma}

    res = sm.simulate_nve(calc_parameters)


    print(res.get_cohesive_energy())


    #Many elements
    config = main_read("cohesive_data_cif.yaml")

    sm = SimulationManager(list(config[0].values())[0])

    epsilon = [[0.0103, 0.0103],
            [0.0103, 0.0103]]  # 2x2
    sigma   = [[3.4, 3.4],
            [3.4, 3.4]]        # 2x2
    
    import ase.data

    elements = ["Na", "Cl"]
    elements_Z = [ase.data.atomic_numbers[sym] for sym in elements]

    calc_parameters = {"elements" : elements_Z, "epsilon" : epsilon, "sigma" : sigma}

    res = sm.simulate_nve(calc_parameters)

    print(res.get_cohesive_energy())


if __name__ == "__main__":
    main()
