import pytest
import numpy as np
from mdse.rm.runmanager import RunManager
from mdse.md.resultMD import ResultMD
from mdse.parser.parse_yml import main_read
from pathlib import Path


@pytest.fixture(scope="session")
def results():
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
    return results[0]


@pytest.fixture
def nvt_result(results):
    return results[1]


@pytest.fixture
def npt_result(results):
    return results[2]


def test_msd(nve_result):
    msd = nve_result.calc_msd()
    assert msd < 0.01
    assert msd > 0


def test_lindemann(nve_result):
    lindemann = nve_result.calc_lindemann()
    assert lindemann < 0.03
    assert lindemann > 0.01


def test_self_diff(nve_result):
    self_diff = nve_result.calc_self_diff()
    assert self_diff < 1e-10
    assert self_diff > 0


def test_isobaric_specific_heat(npt_result):
    specific_heat = npt_result.calc_isobaric_specific_heat()
    assert specific_heat < 500
    assert specific_heat > 200


def test_isochoric_heat_capacity_per_atom(nvt_result):
    isochoric_heat_per_atom = nvt_result.calc_isochoric_heat_capacity_per_atom()
    assert isochoric_heat_per_atom < 6e-23
    assert isochoric_heat_per_atom > 2e-23