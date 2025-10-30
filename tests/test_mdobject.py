from pathlib import Path
from mdse.md.simulationmanager import SimulationManager

from pytest import raises


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

# TODO:
# Unsure how to test this properly
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

    # Should the program continue with other settings or crash?
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

