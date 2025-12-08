#
#    Copyright (C) 2025 See Authors
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

from pathlib import Path
import re
from httk.atomistic.atomisticio import struct_to_cif
from httklib.classes import (
    DefectCell,
    DefectInfo,
    ChemicalPotential,
    HostSuperCellResult,
    HostSuperCell,
    HullDistance,
    ScreenCell,
    ScreenResult,
)
import httk.db
import time

import logging

logger = logging.getLogger(__name__)


def setup_db(db_path: str):
    """
    Initialize an HTTK SQLite-backed database and return a search interface.

    Parameters
    ----------
    db_path : str or Path-like
        Path to the SQLite database file.

    Returns
    -------
    search : httk.db.filteredcollection.FCSqlite
        A searcher object that can be used to query the database.
    """
    backend = httk.db.backend.Sqlite(str(db_path))
    store = httk.db.store.SqlStore(backend)

    return store


def get_defects(store, **query):
    """
    Query a defect structure from the HTTK database.

    Parameters
    ----------
    search : httk.db.store.SqlStore
        The searcher used to run database queries.
    query : dict
        Query to filter the output from the database.

    Returns
    -------
    matches : list
        The retrieved matches for the specified query.
        If no matching entry is found returns None.
    """
    start = time.time()
    search = store.searcher()

    search_host_cell = search.variable(HostSuperCell)

    if query.get("host") is not None:
        search.add(search_host_cell.material == query["host"])

        search.output(search_host_cell.material, "host_material")
        search.output(search_host_cell.host_supercell, "structure")
    else:
        search_defect_cell = search.variable(DefectCell)
        search_defect_info = search.variable(DefectInfo)

        search.add(search_defect_info.key == search_defect_cell.key)

        if query.get("key") is not None:
            search.add(search_defect_cell.key == str(query["key"]))

        if query.get("priority") is not None:
            search.add(search_defect_cell.priority == query["priority"])

        search.output(search_defect_cell.key, "key")
        search.output(search_defect_info.defect_stoichiometry, "stoichiometry")
        search.output(search_defect_info.configuration, "configuration")
        search.output(search_host_cell.material, "host_material")
        search.output(search_defect_cell.defect_structure, "structure")

    query_time = time.time() - start

    logger.debug(f"Query took {query_time:.2f} seconds")

    matches = [materialtuple[0] for materialtuple in list(search)]
    if not matches:
        logger.warning(f"No defect structure found for query: {query}")
        return None

    return matches


def save_to_cif(defect, defects_folder):
    """
    Save an HTTK structure object to a cif file.

    The function writes the structure to a cif file.
    HTTK-specific site metadata (Wyckoff symbols and multiplicities)
    are cleared before export to avoid compatibility issues.

    Parameters
    ----------
    defect : list
        Result from database query as a list of values/objects

    Returns
    -------
    defect_path : Path or None
        The corresponding path to the cif file, or None if save failed.
    """
    key = defect[0]
    structure = defect[-1]

    structure.rc_sites.wyckoff_symbols = None
    structure.rc_sites.multiplicities = None

    try:
        defect_path = Path(f"{str(defects_folder)}/_{key}.cif")
        struct_to_cif(structure, str(defect_path))

        return defect_path

    except Exception as e:
        logger.error(f"Failed to save structure to cif: {e}")
        return None


def save_defects(defects, defect_folder):
    """
    Save a collection of defect structures as CIF files.

    Each defect in `defects` is written to the directory specified by
    `defect_folder` using `save_to_cif()`. The function attempts to create the
    target folder if it does not exist, logging a warning if folder creation
    fails. It also logs the time taken to perform the conversion.

    Parameters
    ----------
    defects : iterable
        A sequence of defect objects to save. Each element must be compatible
        with `save_to_cif()`.
    defect_folder : str or Path-like
        Path to the directory where CIF files will be stored.

    Returns
    -------
    list of Path
        A list of file paths corresponding to the saved CIF files.

    Notes
    -----
    - Folder creation errors (e.g., directory already exists) are logged but
      do not interrupt execution.
    - The function logs the total conversion time at debug level.
    """
    start = time.time()
    defect_folder = Path(defect_folder)
    try:
        defect_folder.mkdir()
    except Exception as e:
        logger.warning(e)

    defect_paths = []
    for defect in defects:
        defect_paths.append(save_to_cif(defect, defect_folder))

    conversion_time = time.time() - start
    logger.debug(
        (
            f"Converting {len(defects)} structures to cif "
            f"took {conversion_time:.2f} seconds"
        )
    )
    return defect_paths


def get_defect_formation_energy(store, **query):
    """
    Compute defect formation energies from a data store and write the results to
    MongoDB.

    Parameters
    ----------
    store : httk.db.store.SqlStore
        A httk datastore object.
    **query : dict, optional
        Optional filters for the query. Currently supports:
        - key (str): Restrict results to a specific defect key.

    Notes
    -----
    This function:
      1. Queries all neutral (charge = 0) defect calculations.
      2. Retrieves defect stoichiometry, total energies, spin, and defect type.
      3. Computes chemical potentials using `get_chem_pot()`.
      4. Calculates defect formation energies:

        .. math::

           E_\\mathrm{form} = E_\\mathrm{defect} - E_\\mathrm{host} - \\sum_i n_i \\mu_i

      5. Stores the resulting data in a MongoDB collection named "DFT data".

    Returns
    -------
    None
        Results are written directly to the database.
    """
    search = store.searcher()
    search_defect_info = search.variable(DefectInfo)
    search_screen_result = search.variable(ScreenResult)
    search_host = search.variable(HostSuperCellResult)
    search_screen_cell = search.variable(ScreenCell)
    search_hull_distance = search.variable(HullDistance)

    search.add(search_defect_info.key == search_screen_cell.defect_key)
    search.add(search_defect_info.key == search_hull_distance.defect_key)
    search.add(search_screen_result.defect_key == search_defect_info.key)

    search.add(search_screen_cell.charge == search_hull_distance.defect_charge)
    search.add(search_screen_cell.spin == search_hull_distance.defect_spin)

    search.add(search_screen_result.charge == 0)
    search.add(search_hull_distance.min_distance < 1e-5)

    if query.get("key") is not None:
        search.add(search_defect_info.key == query["key"])

    search.output(search_defect_info.key, "key")
    search.output(search_defect_info.defect_stoichiometry, "stoichiometry")
    search.output(search_screen_result.total_energy_coarse, "tot_energy_defect")
    search.output(search_host.total_energy, "tot_energy")
    search.output(search_screen_result.spin, "spin")
    search.output(search_defect_info.defect_type, "defect_type")

    matches = [defecttuple[0] for defecttuple in list(search)]

    dft_data = {}
    for match in matches:
        stoichiometry = match[1]

        chem_pot = calc_chem_pot(store, stoichiometry)

        defect_formation_energy = match[2] - match[3] - chem_pot

        dft_data[str(match[0]) + "_" + str(match[4])] = {
            "defect_key": str(match[0]),
            "stoichiometry": match[1],
            "defect_type": match[5],
            "tot_energy_defect": match[2],
            "tot_energy_host": match[3],
            "defect_formation_energy": defect_formation_energy,
            "spin": match[4],
        }

    return {"collection_str": "DFT_data", "data": dft_data}


def calc_chem_pot(store, stoichiometry):
    """
    Compute the total chemical potential contribution for a given defect stoichiometry.

    Parameters
    ----------
    store : httk.db.store.SqlStore
        A httk datastore object.
    stoichiometry : str
        Stoichiometry string of the form "Elem1:-n1_Elem2:-n2 ...", where
        negative integers indicate added atoms and positive integers removed atoms.

    Returns
    -------
    float
        The summed chemical potential: :math:`\\sum_i(n_i\\mu_i)`, using the database-
        stored chemical potentials for each involved element.

    Notes
    -----
    The function:
      - Parses element counts from the stoichiometry string.
      - Queries the datastore for the corresponding elemental chemical potentials.
      - Computes the weighted sum of potentials according to the parsed stoichiometry.
    """
    search = store.searcher()
    pattern = r"([A-Za-z]+):(-?\d+)"
    matches = {elem: -int(count) for elem, count in re.findall(pattern, stoichiometry)}

    search_chem_pot = search.variable(ChemicalPotential)
    search.add(search_chem_pot.material.is_in(*matches.keys()))

    search.output(search_chem_pot.material, "material")
    search.output(search_chem_pot.chemical_potential, "chem_pot")

    query_result = [item[0] for item in list(search)]
    query_result = {
        elem: chemical_potential for elem, chemical_potential in query_result
    }

    chemical_potential = 0
    for elem, count in matches.items():
        chemical_potential += query_result[elem] * count

    return chemical_potential


def get_chemical_potential(store):
    search = store.searcher()
    search_chem_pot = search.variable(ChemicalPotential)

    search.output(search_chem_pot.material, "material")
    search.output(search_chem_pot.chemical_potential, "chem_pot")

    query_result = [chempot[0] for chempot in list(search)]
    chem_pots = {}
    for elem, chemical_potential in query_result:
        chem_pots[elem] = {"element": elem, "chemical_potential": chemical_potential}

    return {"collection_str": "Chemical_potential", "data": chem_pots}
