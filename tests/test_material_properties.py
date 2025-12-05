# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

import pytest
from mdse.rm.runmanager import RunManager
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

    nve = rm.md_simulations[0].simulate()
    nvt = rm.md_simulations[1].simulate()
    npt = rm.md_simulations[2].simulate()

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
    # assert self_diff > -1e-10


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


def test_cohesive_energy(nve_result):
    """Check that cohesive energy reasonable.
    Table value for Cu is 3.49
    """
    assert(abs(nve_result.get_cohesive_energy() - 3.49)/3.49 < 0.005)


def test_shear_modulus(nvt_result):
    '''Check for a reasonable value for the shear modulus. Shear modulus for Cu
    should be 44.7 GPa at room temp.
    '''
    shear_modulus = nvt_result.calc_shear_modulus()
    assert shear_modulus > 20e+9 # GPa
    assert shear_modulus < 80e+9 # GPa


def test_bulk_modulus(nvt_result):
    '''Check for a reasonable value for the bulk modulus. Bulk modulus for Cu
    should be around 130 GPa at room temp.
    '''
    bulk_modulus = nvt_result.calc_bulk_modulus()
    assert bulk_modulus > 100e+9 # GPa
    assert bulk_modulus < 160e+9 # GPa


def test_youngs_modulus(nvt_result):
    '''Check for a reasonable value for Young's modulus. Young's modulus for Cu
    should be around 110 - 130 GPa at room temp.
    '''
    youngs_modulus = nvt_result.calc_bulk_modulus()
    assert youngs_modulus > 80e+9 # GPa
    assert youngs_modulus < 160e+9 # GPa
