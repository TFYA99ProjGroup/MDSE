from pathlib import Path
import numpy as np
from pytest import raises
from mdse.md.simulationmanager import SimulationManager
from unittest.mock import patch
from ase import units


def test_mdobject():
    sim = {
        "CRYSTAL": {
            "TYPE": "BULK",
            "Name": "Cu",
            "Structure": "fcc",
            "Lattice_a": 3.6,
            "Cubic": True,
        },
        "ENSAMBLE": {"Ensamble": "NVE", "Temp": 800},
        "SIMULATION": {
            "Timestep": 2,
            "Length": 800,
            "TrajInterval": 10,
            "Calculator": "EMT",
            "Create_traj": True,
        },
    }

    sim3 = SimulationManager(sim)

    assert sim3.crystal.symbols[0] == "Cu"
    assert (sim3.crystal.cell.lengths() == 3.6).all()
    assert sim3.temperature == 800

    sim3.simulate_nve()

    traj_file = Path("Cu_800.traj")
    assert Path.exists(traj_file)
    traj_file.unlink()

    sim2 = {
        "CRYSTAL": {
            "TYPE": "BULK",
            "Name": "Cu",
            "Structure": "fcc",
            "Lattice_a": 3.6,
            "Cubic": True,
        },
        "ENSAMBLE": {
            "Ensamble": "NPT",
            "Temp": 801,
            "Pressure": 3.85e-2,
            "ThermoTime": 100 * units.fs,
            "BaroTime": 1000 * units.fs,
        },
        "SIMULATION": {
            "Timestep": 2,
            "Length": 800,
            "TrajInterval": 10,
            "Calculator": "EMT",
            "Create_traj": True,
        },
    }
    sim4 = SimulationManager(sim2)

    assert sim4.crystal.symbols[0] == "Cu"
    assert (sim4.crystal.cell.lengths() == 3.6).all()
    assert sim4.temperature == 801

    sim4.simulate_npt()

    traj_file = Path("Cu_801.traj")
    assert Path.exists(traj_file)
    traj_file.unlink()


def test_nve_ensamble():
    config = {
        "CRYSTAL": {
            "TYPE": "BULK",
            "Name": "Cu",
            "Structure": "fcc",
            "Lattice_a": 3.6149,
            "Cubic": True,
        },
        "ENSAMBLE": {"Ensamble": "NVE", "Temp": 100},
        "SIMULATION": {
            "Timestep": 2,
            "Length": 20000,
            "TrajInterval": 5,
            "Calculator": "EMT",
            "Create_traj": True,
        },
    }

    sim = SimulationManager(config)
    assert sim.ensamble.lower() == "nve"
    with patch.object(sim, "simulate_nve") as mock_nve:
        sim.simulate(calculator="EMT")
        mock_nve.assert_called_once()


def test_nvt_ensamble():
    config = {
        "CRYSTAL": {
            "TYPE": "BULK",
            "Name": "Cu",
            "Structure": "fcc",
            "Lattice_a": 3.6149,
            "Cubic": True,
        },
        "ENSAMBLE": {
            "Ensamble": "NVT",
            "Temp": 100,
            "ThermoTime": 100 * units.fs,
        },
        "SIMULATION": {
            "Timestep": 2,
            "Length": 20000,
            "TrajInterval": 5,
            "Calculator": "EMT",
            "Create_traj": True,
        },
    }

    sim = SimulationManager(config)
    assert sim.ensamble.lower() == "nvt"
    with patch.object(sim, "simulate_nvt") as mock_nvt:
        sim.simulate(calculator="EMT")
        mock_nvt.assert_called_once()


def test_npt_ensamble():
    config = {
        "CRYSTAL": {
            "TYPE": "BULK",
            "Name": "Cu",
            "Structure": "fcc",
            "Lattice_a": 3.6149,
            "Cubic": True,
        },
        "ENSAMBLE": {
            "Ensamble": "NPT",
            "Temp": 100,
            "ThermoTime": 100,
            "Pressure": 100,
            "BaroTime": 100,
        },
        "SIMULATION": {
            "Timestep": 2,
            "Length": 20000,
            "TrajInterval": 5,
            "Calculator": "EMT",
            "Create_traj": True,
        },
    }

    sim = SimulationManager(config)
    assert sim.ensamble.lower() == "npt"
    with patch.object(sim, "simulate_npt") as mock_npt:
        sim.simulate()
        mock_npt.assert_called_once()


def test_invalid_ensamble():
    config = {
        "CRYSTAL": {
            "TYPE": "BULK",
            "Name": "Cu",
            "Structure": "fcc",
            "Lattice_a": 3.6149,
            "Cubic": True,
        },
        "ENSAMBLE": {"Ensamble": "INVALID"},
        "SIMULATION": {
            "Timestep": 2,
            "Length": 20000,
            "TrajInterval": 5,
            "Calculator": "EMT",
            "Create_traj": True,
        },
    }

    with raises(RuntimeError):
        sim = SimulationManager(config)


def test_init_from_file():
    config = {
        "CRYSTAL": {"TYPE": "FILE", "Filepath": "not_a_real_file.cif"},
        "ENSAMBLE": {"Ensamble": "NVE", "Temp": 100},
        "SIMULATION": {
            "Timestep": 2,
            "Length": 20000,
            "TrajInterval": 5,
            "Calculator": "EMT",
            "Create_traj": True,
        },
    }

    with raises(RuntimeError):
        SimulationManager(config)

    # HERE WE SHOULD ADD SOME TEST FOR REAL FILES


def test_calculators():
    config = {
        "CRYSTAL": {
            "TYPE": "BULK",
            "Name": "Cu",
            "Structure": "fcc",
            "Lattice_a": 3.6149,
            "Cubic": True,
        },
        "ENSAMBLE": {"Ensamble": "NVE", "Temp": 100},
        "SIMULATION": {
            "Timestep": 2,
            "Length": 20000,
            "TrajInterval": 5,
            "Calculator": "EMT",
            "Create_traj": True,
        },
    }
    sim1 = SimulationManager(config)

    sim1.simulate_nve()

    numbers = list(set(sim1.crystal.numbers))
    np.random.seed(42)
    n = len(numbers)
    sigma = np.random.rand(n)
    epsilon = np.random.rand(n)

    config = {
        "CRYSTAL": {
            "TYPE": "BULK",
            "Name": "Cu",
            "Structure": "fcc",
            "Lattice_a": 3.6149,
            "Cubic": True,
        },
        "ENSAMBLE": {"Ensamble": "NVE", "Temp": 100},
        "SIMULATION": {
            "Timestep": 2,
            "Length": 20000,
            "TrajInterval": 5,
            "Calculator": "LennardJones",
            "Create_traj": True,
        },
    }
    sim1 = SimulationManager(config)
    calc_params = {"elements": numbers, "sigma": sigma, "epsilon": epsilon}

    result = sim1.simulate_nve(calc_params=calc_params)

    assert len(result.frames) > 0

    config = {
        "CRYSTAL": {
            "TYPE": "BULK",
            "Name": "Cu",
            "Structure": "fcc",
            "Lattice_a": 3.6149,
            "Cubic": True,
        },
        "ENSAMBLE": {"Ensamble": "hej123", "Temp": 100},
        "SIMULATION": {
            "Timestep": 2,
            "Length": 20000,
            "TrajInterval": 5,
            "Calculator": "LennardJones",
            "Create_traj": True,
        },
    }

    with raises(RuntimeError):
        sim1 = SimulationManager(config)
