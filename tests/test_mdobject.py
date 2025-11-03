from pathlib import Path
import numpy as np
from pytest import raises
from mdse.md.simulationmanager import SimulationManager



def test_mdobject():
    sim = {
        "Type": "Cu",
        "Structure": "fcc",
        "Lattice_a": 3.6,
        "Cubic": True,
        "Temp": 800,
        "Timestep": 2,
        "Length": 800,
        "TrajInterval": 10,
    }

    sim3 = SimulationManager(sim)

    assert sim3.crystal.symbols[0] == "Cu"
    assert (sim3.crystal.cell.lengths() == 3.6).all()
    assert sim3.temperature == 800

    sim3.simulate_nve()

    traj_file = Path("Cu_800.traj")
    assert Path.exists(traj_file)
    traj_file.unlink()


    sim["Temp"] = 801
    sim4 = SimulationManager(sim)

    assert sim4.crystal.symbols[0] == "Cu"
    assert (sim4.crystal.cell.lengths() == 3.6).all()
    assert sim4.temperature == 801

    sim4.simulate_npt()

    traj_file = Path("Cu_801.traj")
    assert Path.exists(traj_file)
    traj_file.unlink()

def test_init_from_file():
    config = {
        "Crystal" : "crystal.cif",
        "Temp": 800,
        "Timestep": 2,
        "Length": 800,
        "TrajInterval": 10,
    }

    with raises(FileNotFoundError):
        SimulationManager(config)

    config2 = {
        "Crystal" : "crystal.cif",
        "Temp": 800,
        "Timestep": 2,
        "Length": 800,
        "TrajInterval": 10,
        "Type": "Cu",
        "Structure": "fcc",
        "Lattice_a": 3.6,
        "Cubic": True,
    }

    with raises(FileNotFoundError):
        SimulationManager(config2)

def test_calculators():
    calculator = "EMT"

    sim = {
        "Type": "Ni",
        "Structure": "fcc",
        "Lattice_a": 3.6,
        "Cubic": True,
        "Temp": 400,
        "Timestep": 2,
        "Length": 800,
        "TrajInterval": 10,
    }
    sim1 = SimulationManager(sim)

    sim1.simulate_nve(calculator=calculator)

    numbers = list(set(sim1.crystal.numbers))
    np.random.seed(42)
    n = len(numbers)
    sigma = np.random.rand(n)
    epsilon = np.random.rand(n)

    calc_params = {"elements": numbers,
                   "sigma": sigma,
                   "epsilon": epsilon
                   }

    calculator = "LennardJones"

    sim1.simulate_nve(calculator=calculator, calc_params=calc_params)

    with raises(NotImplementedError,
                match=("Calculator hej123 not implemented,"
                        " valid calculators are: EMT, LennardJones")):
        sim1.simulate_nve(calculator="hej123")

    traj_file = Path("Ni_400.traj")
    assert Path.exists(traj_file)
    traj_file.unlink()
