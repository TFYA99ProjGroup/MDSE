from mdse.md.simulationmanager import SimulationManager
from mdse.parser.parse_yml import main_read
from mdse.md.visualize import VisualizeResult
from mdse.md.resultMD import ResultMD



def main():
    """
    #--------------Simulation1, Copper, EMT------------
    print("*"*10 + "Simulation 1" + "*"*10)
    config = main_read("S1.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    resS1 = sm.simulate_nve()
    resS1.name = "S1"

    
    print(f"Bulk modulus: {resS1.calc_bulk_modulus()}")
    print(f"Shear modulus: {resS1.calc_shear_modulus()}")
    print(f"Lattice constant: {resS1.calc_lattice()}")
    print(f"Cohesive energy: {resS1.get_cohesive_energy()}")
    print(f"Lindemann: {resS1.calc_lindemann()}")
    print(f"Self diffusion: {resS1.calc_self_diff()}")
    print(f"Debye temp: {resS1.calc_debye_temperature()}")

    resS1.dos = None

    print("*"*32)

    #--------------Simulation2, Copper, Mace-Model-0 ------------
    print("*"*10 + "Simulation 2" + "*"*10)
    config = main_read("S2.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    resS2 = sm.simulate_nve()
    resS2.name = "S2"

    print(f"Bulk modulus: {resS2.calc_bulk_modulus()}")
    print(f"Shear modulus: {resS2.calc_shear_modulus()}")
    print(f"Lattice constant: {resS2.calc_lattice()}")
    print(f"Cohesive energy: {resS2.get_cohesive_energy()}")
    print(f"Lindemann: {resS2.calc_lindemann()}")
    print(f"Self diffusion: {resS2.calc_self_diff()}")
    print(f"Debye temp: {resS2.calc_debye_temperature()}")


    print("*"*32)
    
    #--------------Simulation3, MgCu2, EMT(MetalGlass)------------
    print("*"*10 + "Simulation 3" + "*"*10)
    config = main_read("S3.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    resS3 = sm.simulate_nve()
    resS3.name = "S3"

    print(f"Bulk modulus: {resS3.calc_bulk_modulus()}")
    print(f"Shear modulus: {resS3.calc_shear_modulus()}")
    print(f"Lattice constant: {resS3.calc_lattice()}")
    print(f"Cohesive energy: {resS3.get_cohesive_energy()}")
    print(f"Lindemann: {resS3.calc_lindemann()}")
    print(f"Self diffusion: {resS3.calc_self_diff()}")
    print(f"Debye temp: {resS3.calc_debye_temperature()}")

    print("*"*32)
    
    #--------------Simulation4, Au, EMT------------
    print("*"*10 + "Simulation 4" + "*"*10)
    config = main_read("S4.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    resS4 = sm.simulate_nve()
    resS4.name = "S4"
    resS4.dos = None
    resS4.omega = 0

    #print(f"Bulk modulus: {resS4.calc_bulk_modulus()}")
    #print(f"Shear modulus: {resS4.calc_shear_modulus()}")
    #print(f"Lattice constant: {resS4.calc_lattice()}")
    #print(f"Cohesive energy: {resS4.get_cohesive_energy()}")
    #print(f"Lindemann: {resS4.calc_lindemann()}")
    #print(f"Self diffusion: {resS4.calc_self_diff()}")
    print(f"Debye temp: {resS4.calc_debye_temperature()}")

    print("*"*32)
    
    #--------------Simulation5, Zn, Mace------------
    print("*"*10 + "Simulation 5" + "*"*10)
    config = main_read("S5.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    resS5 = sm.simulate_nve()
    resS5.name = "S5"

    print(f"Bulk modulus: {resS5.calc_bulk_modulus()}")
    print(f"Shear modulus: {resS5.calc_shear_modulus()}")
    print(f"Lattice constant: {resS5.calc_lattice()}")
    print(f"Cohesive energy: {resS5.get_cohesive_energy()}")
    print(f"Lindemann: {resS5.calc_lindemann()}")
    print(f"Self diffusion: {resS5.calc_self_diff()}")
    print(f"Debye temp: {resS5.calc_debye_temperature()}")

    print("*"*32)
    
    #------Visualize-----
    print("*"*10 + "Generate plot" + "*"*10)
    vis_S = VisualizeResult([resS1,resS2,resS3,resS4, resS5])

    vis_S.plot_DOS()

    """

    #--------------Ensemble1, Al, EMT------------
    
    print("*"*10 + "Ensemble 1" + "*"*10)
    config = main_read("E1.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res1 = sm.simulate_nve()
    print("*"*32)
    
    #--------------Ensemble2, Al, EMT------------
    
    print("*"*10 + "Ensemble 2" + "*"*10)
    config = main_read("E2.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res2 = sm.simulate_nvt()
    print("*"*32)
    
    #--------------Ensemble3, Al, EMT------------
    
    print("*"*10 + "Ensemble 3" + "*"*10)
    config = main_read("E3.yaml")
    sm = SimulationManager(list(config[0].values())[0])

    res3 = sm.simulate_npt()
    print("*"*32)

    #------Visualize-----
    print("*"*10 + "Generate plot" + "*"*10)
    res1.name = "E1"
    res2.name = "E2"
    res3.name = "E3"
    vis_e1 = VisualizeResult([res1])
    vis_e2 = VisualizeResult([res2])
    vis_e3 = VisualizeResult([res3])

    #vis_e1.plot_pressure()
    #vis_e2.plot_pressure()
    #vis_e3.plot_pressure()

    #vis_e1.plot_pressure()
    #vis_e1.plot_energy("tot")
    #vis_e1.plot_energy("kin")
    #vis_e1.plot_energy("pot")
    vis_e1.plot_temp()

    #vis_e2.plot_energy("tot")
    #vis_e2.plot_energy("kin")
    #vis_e2.plot_energy("pot")
    vis_e2.plot_temp()

    #vis_e3.plot_energy("tot")
    #vis_e3.plot_energy("kin")
    #vis_e3.plot_energy("pot")
    vis_e3.plot_temp()


def rel_error(value1,ref):
    return abs(value1 - ref)/abs(ref)*100

if __name__ == "__main__":
    main()
