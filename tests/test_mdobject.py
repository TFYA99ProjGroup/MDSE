from pathlib import Path
import numpy as np
from pytest import raises
from mdse.md.simulationmanager import SimulationManager
from unittest.mock import patch


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

    sim3 = SimulationManager(sim, create_trajectory=True)

    assert sim3.crystal.symbols[0] == "Cu"
    assert (sim3.crystal.cell.lengths() == 3.6).all()
    assert sim3.temperature == 800

    sim3.simulate_nve()

    traj_file = Path("Cu_800.traj")
    assert Path.exists(traj_file)
    traj_file.unlink()

    sim["Temp"] = 801
    sim4 = SimulationManager(sim, create_trajectory=True)

    assert sim4.crystal.symbols[0] == "Cu"
    assert (sim4.crystal.cell.lengths() == 3.6).all()
    assert sim4.temperature == 801

    sim4.simulate_npt()

    traj_file = Path("Cu_801.traj")
    assert Path.exists(traj_file)
    traj_file.unlink()


def test_default_ensamble():
    config = {
        "Type": "Cu",
        "Structure": "fcc",
        "Lattice_a": 3.6149,
        "Cubic": True,
        "Temp": 100,
        "Length": 20000,
        "TrajInterval": 5, }
    sim = SimulationManager(config)
    assert (sim.ensamble.lower() == "nve")
    with patch.object(sim, 'simulate_nve') as mock_nve:
        sim.simulate()
        mock_nve.assert_called_once()

    config["Ensamble"] = "NVE"
    sim = SimulationManager(config)
    assert (sim.ensamble.lower() == "nve")
    with patch.object(sim, 'simulate_nve') as mock_nve:
        sim.simulate()
        mock_nve.assert_called_once()

    config["Ensamble"] = "NVT"
    sim = SimulationManager(config)
    assert (sim.ensamble.lower() == "nvt")
    with patch.object(sim, 'simulate_nvt') as mock_nvt:
        sim.simulate()
        mock_nvt.assert_called_once()


def test_nve_ensamble():
    config = {
        "Type": "Cu",
        "Structure": "fcc",
        "Lattice_a": 3.6149,
        "Cubic": True,
        "Temp": 100,
        "Length": 20000,
        "TrajInterval": 5,
        "Ensamble": "NVE"}
    sim = SimulationManager(config)
    assert (sim.ensamble.lower() == "nve")
    with patch.object(sim, 'simulate_nve') as mock_nve:
        sim.simulate()
        mock_nve.assert_called_once()


def test_nvt_ensamble():
    config = {
        "Type": "Cu",
        "Structure": "fcc",
        "Lattice_a": 3.6149,
        "Cubic": True,
        "Temp": 100,
        "Length": 20000,
        "TrajInterval": 5,
        "Ensamble": "NVT"}
    sim = SimulationManager(config)
    assert (sim.ensamble.lower() == "nvt")
    with patch.object(sim, 'simulate_nvt') as mock_nvt:
        sim.simulate()
        mock_nvt.assert_called_once()


def test_npt_ensamble():
    config = {
        "Type": "Cu",
        "Structure": "fcc",
        "Lattice_a": 3.6149,
        "Cubic": True,
        "Temp": 100,
        "Length": 20000,
        "TrajInterval": 5,
        "Ensamble": "NPT"}
    sim = SimulationManager(config)
    assert (sim.ensamble.lower() == "npt")
    with patch.object(sim, 'simulate_npt') as mock_npt:
        sim.simulate()
        mock_npt.assert_called_once()


def test_invalid_ensamble():
    config = {
        "Type": "Cu",
        "Structure": "fcc",
        "Lattice_a": 3.6149,
        "Cubic": True,
        "Temp": 100,
        "Length": 20000,
        "TrajInterval": 5,
        "Ensamble": "INVALID"}
    sim = SimulationManager(config)
    with raises(ValueError, match="ensamble"):
        sim.simulate()


def test_init_from_file():
    config = {
        "Crystal": "crystal.cif",
        "Temp": 800,
        "Timestep": 2,
        "Length": 800,
        "TrajInterval": 10,
    }

    with raises(FileNotFoundError):
        SimulationManager(config)

    config2 = {
        "Crystal": "crystal.cif",
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

    result = sim1.simulate_nve(calculator=calculator, calc_params=calc_params)

    assert len(result.frames) > 0

    with raises(NotImplementedError,
                match=("Calculator hej123 not implemented,"
                       " valid calculators are: EMT, LennardJones")):
        sim1.simulate_nve(calculator="hej123")
