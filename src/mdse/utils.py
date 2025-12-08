# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

import logging
import re

from mdse.rm.dbmanager import DBManager
from httklib.httk_reader import (
    get_chemical_potential,
    get_defect_formation_energy,
    setup_db,
)

logger = logging.getLogger(__name__)


def defect_formation_energy(db):
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
    pattern = r"([A-Za-z]+):?(-?\d+)"
    element_counts = {
        elem: int(count) for elem, count in re.findall(pattern, stoichiometry)
    }

    logger.debug(f"Element counts: {element_counts}")

    return element_counts


def transfer_chemical_potential(sqlite_path, mongodb_adress):
    store = setup_db(sqlite_path)

    mongodb = DBManager(mongodb_adress)
    mongodb.clear_collection("Chemical_potential")
    mongodb.write_dict_to_db(**get_chemical_potential(store))

def transfer_defect_formation_energy(sqlite_path, mongodb_adress):
    store = setup_db(sqlite_path)

    mongodb = DBManager(mongodb_adress)
    mongodb.clear_collection("DFT_data")
    mongodb.write_dict_to_db(**get_defect_formation_energy(store))
