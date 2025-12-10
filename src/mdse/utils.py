# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""Utility functions for post-processing and data management.

This module provides helper functions for tasks such as calculating defect
formation energies from simulation results and transferring data between
different database sources (e.g., from an HTTK SQLite DB to MongoDB).
"""

import logging
import re

from mdse.rm.dbmanager import DBManager
from httk4mdse.httk_reader import (
    get_chemical_potential,
    get_defect_formation_energy,
    setup_db,
)

logger = logging.getLogger(__name__)


def defect_formation_energy(db):
    """Calculates defect formation energies and stores them in the database.

    This function reads defect simulation results and the corresponding host
    material energy from a MongoDB database. It then calculates the formation
    energy for each defect and writes the results (including the formation
    energy and total chemical potential) back into a new collection named
    'MACE_results'.

    Note:
        This function will clear the 'MACE_results' collection before writing
        new data.

    Args:
        db (DBManager): An active DBManager instance connected to the database.
    """
    defects = db.read_from_db(
        {"host_material": "diamond"},
        outputs=[
            "id",
            "defect_key",
            "defect_stoichiometry",
            "host_material",
            "total_energy",
        ],
    )

    host = db.read_from_db({"defect_key": None}, outputs=["id", "total_energy"])
    E_Host = next(iter(host.values()))["total_energy"]

    md_entries = {}
    for entry in defects.values():
        E_D = entry["total_energy"]
        defect_stoichiometry = entry["defect_stoichiometry"]
        logger.debug(f"Defect stoichiometry: {defect_stoichiometry}")

        element_counts = get_nelements(defect_stoichiometry)
        element_counts = {elem: -count for elem, count in element_counts.items()}

        E_DF, total_chem_pot = calc_formation_energy(E_Host, element_counts, db, E_D)

        md_entries[entry["id"]] = {
            "id": entry["id"],
            "defect_key": entry["defect_key"],
            "formation_energy": E_DF,
            "total_chemical_potential": total_chem_pot,
        }

    db.clear_collection("MACE_results")
    db.write_dict_to_db(md_entries, collection_str="MACE_results")


def calc_formation_energy(host_energy, element_counts, db, defect_energy=0):
    """Calculates the formation energy for a given defect.

    The formation energy is calculated using the formula:
    E_DF = E_D - E_Host + sum(n_i * mu_i)

    where E_D is the energy of the defect system, E_Host is the energy of the
    pristine host system, n_i is the number of atoms of element i added or
    removed, and mu_i is the chemical potential of element i.

    Args:
        host_energy (float): The total energy of the host material.
        element_counts (dict[str, int]): A dictionary mapping element symbols to the
            number of atoms of that type added (positive) or removed (negative).
        db (DBManager): The database manager used to query for chemical potentials.
        defect_energy (float, optional): The total energy of the system containing
            the defect. Defaults to 0.

    Returns:
        tuple[float, float]: A tuple containing the calculated formation energy
            and the total chemical potential contribution.
    """
    total_chem_pot = 0
    for elem, nelement in element_counts.items():
        chemical_potential = next(
            iter(
                db.read_from_db(
                    {"element": elem},
                    outputs=["chemical_potential"],
                    collection_str="Chemical_potential",
                ).values()
            )
        )["chemical_potential"]

        total_chem_pot += nelement * chemical_potential

    formation_energy = defect_energy - host_energy + total_chem_pot
    return formation_energy, total_chem_pot


def get_nelements(stoichiometry):
    """Parses a stoichiometry string into a dictionary of element counts.

    The function uses a regular expression to find all element-count pairs in
    the input string.

    Args:
        stoichiometry (str): A string representing the change in stoichiometry,
            e.g., "C:-1,Si:1".

    Returns:
        dict[str, int]: A dictionary mapping element symbols to their counts.
    """
    pattern = r"([A-Za-z]+):?(-?\d+)"
    element_counts = {
        elem: int(count) for elem, count in re.findall(pattern, stoichiometry)
    }

    logger.debug(f"Element counts: {element_counts}")

    return element_counts


def transfer_chemical_potential(sqlite_path, mongodb_adress):
    """Transfers chemical potential data from an SQLite DB to MongoDB.

    This function connects to an HTTK-formatted SQLite database, retrieves
    chemical potential data, and writes it to a specified MongoDB instance.
    The target collection 'Chemical_potential' in MongoDB is cleared before
    the new data is inserted.

    Args:
        sqlite_path (str): The file path to the source SQLite database.
        mongodb_adress (str): The connection address for the target MongoDB server.
    """
    store = setup_db(sqlite_path)

    mongodb = DBManager(mongodb_adress)
    mongodb.clear_collection("Chemical_potential")
    mongodb.write_dict_to_db(**get_chemical_potential(store))

def transfer_defect_formation_energy(sqlite_path, mongodb_adress):
    """Transfers DFT defect formation energy data from an SQLite DB to MongoDB.

    This function connects to an HTTK-formatted SQLite database, retrieves
    defect formation energy data, and writes it to a specified MongoDB instance.
    The target collection 'DFT_data' in MongoDB is cleared before the new data
    is inserted.

    Args:
        sqlite_path (str): The file path to the source SQLite database.
        mongodb_adress (str): The connection address for the target MongoDB server.
    """
    store = setup_db(sqlite_path)

    mongodb = DBManager(mongodb_adress)
    mongodb.clear_collection("DFT_data")
    mongodb.write_dict_to_db(**get_defect_formation_energy(store))
