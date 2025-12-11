#
#    Automatic Defect Analysis and Qualification (ADAQ)
#    Copyright (C) 2016-2021 Joel Davidsson
#    Implemented using the high-throughput toolkit (httk) (see README.md)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, division

try:
    import httk
except Exception:
    import sys
    import os.path
    import inspect

    _realpath = os.path.realpath(
        os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])
    )
    sys.path.insert(1, os.path.join(_realpath, "../.."))
    import httk

from httk.atomistic import Structure
from httk.core.vectors import FracVector


# This class for the host material properties
class HostUnitCellResult(httk.Result):
    @httk.httk_typed_init(
        {
            "host_name": str,
            "computation": httk.Computation,
            "structure": Structure,
            "formation_entalpy": float,
            "mp_id": str,
            "dielectric_tensor_electric": [float],
            "dielectric_tensor_ionic": [float],
            "refractive_index": float,
        },
        index=["host_name"],
    )
    def __init__(
        self,
        host_name,
        computation,
        structure,
        mp_id,
        formation_entalpy,
        dielectric_tensor_electric,
        dielectric_tensor_ionic,
        refractive_index,
    ):
        self.host_name = host_name
        self.computation = computation
        self.structure = structure
        self.mp_id = mp_id
        self.formation_entalpy = formation_entalpy  # eV/atom
        self.dielectric_tensor_electric = dielectric_tensor_electric  # dimensionless
        self.dielectric_tensor_ionic = dielectric_tensor_ionic  # dimensionless
        self.refractive_index = refractive_index  # dimensionless


# This class for the Host material
class HostSuperCell(httk.HttkObject):
    @httk.httk_typed_init(
        {
            "unit_cell": Structure,
            "host_supercell": Structure,
            "description": str,
            "data": [int],
            "dimension": str,
            "material": str,
            "functional": str,
        }
    )
    def __init__(
        self,
        unit_cell,
        host_supercell,
        description,
        data,
        dimension,
        material,
        functional,
    ):
        self.unit_cell = unit_cell
        self.host_supercell = host_supercell
        self.description = description
        self.data = data
        self.dimension = dimension
        # which material is it
        self.material = material
        # which functional was used to determine the lattice parameters
        self.functional = functional

    def name(self):
        return self.material + "_" + self.functional


class HostSuperCellResult(httk.Result):
    @httk.httk_typed_init(
        {
            "host_name": str,
            "computation": httk.Computation,
            "screen_energy": float,
            "screen_valance_band_max": float,
            "screen_conduction_band_min": float,
            "total_energy_coarse": float,
            "coarse_valance_band_max": float,
            "coarse_conduction_band_min": float,
            "total_energy": float,
            "full_valance_band_max": float,
            "full_conduction_band_min": float,
            "madelung_potential": float,
        },
        index=["host_name"],
    )
    def __init__(
        self,
        host_name,
        computation,
        screen_energy,
        screen_valance_band_max,
        screen_conduction_band_min,
        total_energy_coarse,
        coarse_valance_band_max,
        coarse_conduction_band_min,
        total_energy,
        full_valance_band_max,
        full_conduction_band_min,
        madelung_potential,
    ):
        self.host_name = host_name
        self.computation = computation
        # screen
        self.screen_energy = screen_energy
        self.screen_valance_band_max = screen_valance_band_max
        self.screen_conduction_band_min = screen_conduction_band_min
        # full
        self.total_energy_coarse = total_energy_coarse
        self.coarse_valance_band_max = coarse_valance_band_max
        self.coarse_conduction_band_min = coarse_conduction_band_min
        self.total_energy = total_energy
        self.full_valance_band_max = full_valance_band_max
        self.full_conduction_band_min = full_conduction_band_min

        # charge correction
        self.madelung_potential = madelung_potential


# These two classes contain the info about the defect:
# defectinfo -  contain overview info, fast class to search
# defectcell - contain the structure
class DefectInfo(httk.HttkObject):
    @httk.httk_typed_init(
        {
            "key": int,
            "host_name": str,
            "defect_name": str,
            "defect_stoichiometry": str,
            "defect_type": str,
            "configuration": str,
            "defect_size": int,
            "vacancy": bool,
            "substitutional": bool,
            "interstitial": bool,
            "S": bool,
            "P": bool,
            "D": bool,
            "F": bool,
        },
        index=[
            "key",
            "defect_name",
            "defect_stoichiometry",
            "defect_type",
            "defect_size",
            "vacancy",
            "substitutional",
            "interstitial",
            "S",
            "P",
            "D",
            "F",
        ],
    )
    def __init__(
        self,
        key,
        host_name,
        defect_name,
        defect_stoichiometry,
        defect_type,
        configuration,
        defect_size,
        vacancy,
        substitutional,
        interstitial,
        S,
        P,
        D,
        F,
    ):
        self.key = key
        self.host_name = host_name
        # unique name for the defect
        self.defect_name = defect_name
        # what stoichiometry the defect has
        self.defect_stoichiometry = defect_stoichiometry
        # and where in the supercell it is localated
        self.defect_type = defect_type
        # unique hash for the defect
        self.configuration = configuration
        self.defect_size = defect_size
        # defect info
        self.vacancy = vacancy
        self.substitutional = substitutional
        self.interstitial = interstitial
        self.S = S
        self.P = P
        self.D = D
        self.F = F


class DefectCell(httk.HttkObject):
    @httk.httk_typed_init(
        {
            "host_name": str,
            "defect_structure": Structure,
            "defect_name": str,
            "defect_types": [str],
            "defect_positions": (FracVector, 0, 3),
            "key": int,
            "priority": int,
            "description": str,
        },
        index=["defect_name", "key", "priority"],
    )
    def __init__(
        self,
        host_name,
        defect_structure,
        defect_name,
        defect_types,
        defect_positions,
        key,
        priority,
        description,
    ):
        self.host_name = host_name
        self.defect_structure = defect_structure
        # unique name for the defect
        self.defect_name = defect_name
        # what defect is it
        self.defect_types = defect_types
        # and where in the supercell it is localated
        self.defect_positions = defect_positions
        # unique hash for the defect
        self.key = key
        # priority for the defect
        self.priority = priority
        # general description of the defect
        self.description = description


# These two classes contain the screening results for a defect:
# ScreenResult - just the results from the screening workflow, fast class to search
# ScreenCell - structures and relaxation from starting geometry
class ScreenResult(httk.Result):
    @httk.httk_typed_init(
        {
            "defect_key": int,
            "computation": httk.Computation,
            "charge": int,
            "spin": float,
            "defect_folder_name": str,
            "total_energy_coarse": float,
            "smallest_abs_estimate": float,
            "smallest_abs_transition_intensity": float,
            "smallest_abs_partial_density_difference": float,
            "smallest_abs_polarization_x": float,
            "smallest_abs_polarization_y": float,
            "smallest_abs_polarization_z": float,
            "excitation": str,
            "abs_estimate": float,
            "abs_transition_intensity": float,
            "abs_partial_density_difference": float,
            "abs_polarization_x": float,
            "abs_polarization_y": float,
            "abs_polarization_z": float,
            "abs_radiative_lifetime": float,
            "ZPL_converged": bool,
            "ZPL_estimate": float,
            "ZPL_transition_intensity": float,
            "ZPL_partial_density_difference": float,
            "ZPL_polarization_x": float,
            "ZPL_polarization_y": float,
            "ZPL_polarization_z": float,
            "ZPL_radiative_lifetime": float,
            "max_relaxation": float,
            "average_relaxation": float,
            "delta_R": float,
            "delta_Q": float,
            "huang_rhys": float,
            "debye_waller": float,
            "omega": float,
            "time": float,
        },
        index=["defect_key"],
    )
    def __init__(
        self,
        defect_key,
        computation,
        charge,
        spin,
        defect_folder_name,
        total_energy_coarse,
        smallest_abs_estimate,
        smallest_abs_transition_intensity,
        smallest_abs_partial_density_difference,
        smallest_abs_polarization_x,
        smallest_abs_polarization_y,
        smallest_abs_polarization_z,
        excitation,
        abs_estimate,
        abs_transition_intensity,
        abs_partial_density_difference,
        abs_polarization_x,
        abs_polarization_y,
        abs_polarization_z,
        abs_radiative_lifetime,
        ZPL_converged,
        ZPL_estimate,
        ZPL_transition_intensity,
        ZPL_partial_density_difference,
        ZPL_polarization_x,
        ZPL_polarization_y,
        ZPL_polarization_z,
        ZPL_radiative_lifetime,
        max_relaxation,
        average_relaxation,
        delta_R,
        delta_Q,
        huang_rhys,
        debye_waller,
        omega,
        time,
    ):
        self.defect_key = defect_key
        self.computation = computation
        self.charge = charge
        self.spin = spin
        self.defect_folder_name = defect_folder_name
        self.total_energy_coarse = total_energy_coarse
        # smallest optical estimates, from ground state only
        self.smallest_abs_estimate = smallest_abs_estimate
        self.smallest_abs_transition_intensity = smallest_abs_transition_intensity
        self.smallest_abs_partial_density_difference = (
            smallest_abs_partial_density_difference
        )
        self.smallest_abs_polarization_x = smallest_abs_polarization_x
        self.smallest_abs_polarization_y = smallest_abs_polarization_y
        self.smallest_abs_polarization_z = smallest_abs_polarization_z
        # optical estimates from ground and excited state
        self.excitation = excitation
        # abs
        self.abs_estimate = abs_estimate
        self.abs_transition_intensity = abs_transition_intensity
        self.abs_partial_density_difference = abs_partial_density_difference
        self.abs_polarization_x = abs_polarization_x
        self.abs_polarization_y = abs_polarization_y
        self.abs_polarization_z = abs_polarization_z
        self.abs_radiative_lifetime = abs_radiative_lifetime
        # zpl
        self.ZPL_converged = ZPL_converged
        self.ZPL_estimate = ZPL_estimate
        self.ZPL_transition_intensity = ZPL_transition_intensity
        self.ZPL_partial_density_difference = ZPL_partial_density_difference
        self.ZPL_polarization_x = ZPL_polarization_x
        self.ZPL_polarization_y = ZPL_polarization_y
        self.ZPL_polarization_z = ZPL_polarization_z
        self.ZPL_radiative_lifetime = ZPL_radiative_lifetime
        # relaxation from ground to excited geometry
        self.max_relaxation = max_relaxation
        self.average_relaxation = average_relaxation
        self.delta_R = delta_R
        self.delta_Q = delta_Q
        # one-phonon approximation
        self.huang_rhys = huang_rhys
        self.debye_waller = debye_waller
        self.omega = omega  # E(Q) = 1/2 Omega^2 Q^2, saved in eV
        # calculation time
        self.time = time


class ScreenCell(httk.Result):
    @httk.httk_typed_init(
        {
            "defect_key": int,
            "computation": httk.Computation,
            "charge": int,
            "spin": float,
            "defect_folder_name": str,
            "workflow": str,
            "state": str,
            "name": str,
            "structure": Structure,
        },
        index=["defect_key", "workflow", "state"],
    )
    def __init__(
        self,
        defect_key,
        computation,
        charge,
        spin,
        defect_folder_name,
        workflow,
        state,
        name,
        structure,
    ):
        self.defect_key = defect_key
        self.computation = computation
        self.charge = charge
        self.spin = spin
        self.defect_folder_name = defect_folder_name
        self.workflow = workflow
        self.state = state
        self.name = name
        self.structure = structure


# this class is for the chemical potential for each material
class ChemicalPotential(httk.Result):
    @httk.httk_typed_init(
        {
            "material": str,
            "computation": httk.Computation,
            "chemical_potential_coarse": float,
            "chemical_potential": float,
            "functional": str,
        },
        index=["material"],
    )
    def __init__(
        self,
        material,
        computation,
        chemical_potential_coarse,
        chemical_potential,
        functional,
    ):
        self.material = material
        self.computation = computation
        self.chemical_potential_coarse = chemical_potential_coarse
        self.chemical_potential = chemical_potential
        self.functional = functional


# this class stores the only defects on the defect hull
class DefectHull(httk.HttkObject):
    @httk.httk_typed_init(
        {
            "host_name": str,
            "defect_stoichiometry": str,
            "defect_key": int,
            "defect_charge": int,
            "defect_spin": float,
            "fermi_levels": [float],
            "formation_energies": [float],
        },
        index=["host_name", "defect_stoichiometry", "defect_key"],
    )
    def __init__(
        self,
        host_name,
        defect_stoichiometry,
        defect_key,
        defect_charge,
        defect_spin,
        fermi_levels,
        formation_energies,
    ):
        # host material and defect stoichiometry
        self.host_name = host_name
        self.defect_stoichiometry = defect_stoichiometry
        # defect data
        self.defect_key = defect_key
        self.defect_charge = defect_charge
        self.defect_spin = defect_spin
        # formation energy data
        self.fermi_levels = fermi_levels
        self.formation_energies = formation_energies


# this class stores the the distance to the defect hull for all defects
class HullDistance(httk.HttkObject):
    @httk.httk_typed_init(
        {
            "host_name": str,
            "defect_stoichiometry": str,
            "defect_key": int,
            "defect_charge": int,
            "defect_spin": float,
            "formation_energy_const": float,
            "min_distance": float,
            "interval": [float],
            "span": float,
        },
        index=["host_name", "defect_stoichiometry", "defect_key"],
    )
    def __init__(
        self,
        host_name,
        defect_stoichiometry,
        defect_key,
        defect_charge,
        defect_spin,
        formation_energy_const,
        min_distance,
        interval,
        span,
    ):
        # host material and defect stoichiometry
        self.host_name = host_name
        self.defect_stoichiometry = defect_stoichiometry
        # defect data
        self.defect_key = defect_key
        self.defect_charge = defect_charge
        self.defect_spin = defect_spin
        self.formation_energy_const = formation_energy_const
        # distance data
        self.min_distance = min_distance
        self.interval = interval
        self.span = span
