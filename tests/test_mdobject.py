from pathlib import Path
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

    assert sim3.chem_notation == "Cu"
    assert sim3.structure == "fcc"
    assert sim3.a == 3.6
    assert sim3.temperature == 800

    sim3.simulate_nve()

    traj_file = Path("Cu_800.traj")
    assert Path.exists(traj_file)
    traj_file.unlink()


    sim["Temp"] = 801
    sim4 = SimulationManager(sim)

    assert sim4.chem_notation == "Cu"
    assert sim4.structure == "fcc"
    assert sim4.a == 3.6
    assert sim4.temperature == 801

    sim4.simulate_nvp()

    traj_file = Path("Cu_801.traj")
    assert Path.exists(traj_file)
    traj_file.unlink()

