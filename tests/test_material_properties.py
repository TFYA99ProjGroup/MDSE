import pytest
from mdse.rm.runmanager import RunManager
from mdse.md.resultMD import ResultMD
from mdse.parser.parse_yml import main_read
from pathlib import Path


@pytest.fixture(scope="session")
def results():
    """
    Run a small MD suite (NVE, NVT, NPT) and return parsed ResultMD objects.

    This fixture performs a full simulation run once per test session to avoid
    re-running expensive trajectories for every property test. The generated 
    trajectory files are then loaded into 'ResultMD' containers.

    Returns
    -------
    tuple(ResultMD, ResultMD, ResultMD)
        Result objects for NVE, NVT, NPT and trajectories respectively.
    """
    here = Path(__file__).parent
    config_path = here / "material_test.yaml"

    config = main_read(config_path)

    rm = RunManager(config)

    rm.run_simulations()

    nve = ResultMD.from_file("Cu_300.traj")
    nvt = ResultMD.from_file("Cu_301.traj")
    npt = ResultMD.from_file("Cu_302.traj")

    return nve, nvt, npt


@pytest.fixture
def nve_result(results):
    """
    Extract the NVE result from the simulation for better readability.

    Returns
    -------
    ResultMD
        Parsed data from the NVE simulation
    """
    return results[0]


@pytest.fixture
def nvt_result(results):
    """
    Extract the NVT result from the simulation for better readability.

    Returns
    -------
    ResultMD
        Parsed data from the NVT simulation
    """
    return results[1]


@pytest.fixture
def npt_result(results):
    """
    Extract the NPT result from the simulation for better readability.

    Returns
    -------
    ResultMD
        Parsed data from the NPT simulation
    """
    return results[2]


def test_msd(nve_result):
    """Check for a reasonable value of the mean square displacement"""
    msd = nve_result.calc_msd()
    assert msd < 0.01
    assert msd > 0


def test_lindemann(nve_result):
    """Check for reasonable value of the lindemann criterion,
    for copper at 300K it should be around 0.02"""
    lindemann = nve_result.calc_lindemann()
    assert lindemann < 0.03
    assert lindemann > 0.01


def test_self_diff(nve_result):
    """Check for reasonable value of the self diffusion. 
    Should be close to zero and positive."""
    self_diff = nve_result.calc_self_diff()
    assert self_diff < 1e-10
    assert self_diff > 0


def test_isobaric_specific_heat(npt_result):
    """Check for reasonable value of the isobaric specific heat.
    For copper the value should be 385 J / (kg * K), the test have wide boundaries 
    for the short simulation"""
    specific_heat = npt_result.calc_isobaric_specific_heat()
    assert specific_heat < 500
    assert specific_heat > 200


def test_isochoric_heat_capacity_per_atom(nvt_result):
    """Check for reasonable value of the isochoric heat capacity per atom.
    For copper this should average to around 3e-23"""
    isochoric_heat_per_atom = nvt_result.calc_isochoric_heat_capacity_per_atom()
    assert isochoric_heat_per_atom < 6e-23
    assert isochoric_heat_per_atom > 2e-23