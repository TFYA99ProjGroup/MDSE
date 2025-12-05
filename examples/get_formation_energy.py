# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

# Reads data from existing db, and calculates
# defect formation energy for entries. Also calculates formation energy for host.

from mdse.logging.logging_config import setup_logging
from mdse.rm.dbmanager import DBManager
from mdse.rm.dbmanager import MongoDBEntry
from mdse.utils import calc_formation_energy, defect_formation_energy, get_nelements
from datetime import datetime
import random

mongodb = "mongodb://admin:secret@localhost:27017/"

# the db with all the good stuff in it
db = DBManager(mongodb)

setup_logging()


def make_fake_entries(n=10, seed=420):
    random.seed(seed)
    elements_pool = [
        ("C", "Se"),
        ("Si", "O"),
        ("Ga", "N"),
        ("Ge", "Te"),
        ("Al", "P"),
        ("Mg", "S"),
    ]

    defect_types = [
        ("vacancy", "{el}:-1"),
        ("interstitial", "{el}:1"),
        ("substitution", "{el1}:1_{el2}:-1"),
        ("substitution", "{el1}:1_{el2}:-1"),
    ]

    entries = {}

    for i in range(n):
        key = f"{random.getrandbits(128):032x}"
        el1, el2 = random.choice(elements_pool)

        # random 4–6 atom cell
        natoms = random.randint(4, 6)

        species = [random.choice([el1, el2]) for _ in range(natoms)]

        # positions (simple cubic-like fake pattern)
        positions = []
        for _ in range(natoms):
            positions.append(
                [
                    round(random.uniform(0, 5), 3),
                    round(random.uniform(0, 5), 3),
                    round(random.uniform(0, 5), 3),
                ]
            )

        cell = [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]]

        # --- defect ---
        dtype, stoich_pattern = random.choice(defect_types)
        stoich = stoich_pattern.format(el=el1, el1=el1, el2=el2)

        # --- energy in eV (realistic small-cell range) ---
        total_energy = round(random.uniform(-40.0, -10.0), 4)

        entry = MongoDBEntry(
            id=f"{el1}{el2}_1K_{''.join(species)}_{i}",
            last_modified=datetime.now(),
            elements=list(set(species)),
            nelements=len(set(species)),
            mdse_fields={
                "lindemann": round(random.uniform(0.01, 0.05), 4),
                "self_diffusion": random.uniform(1e-13, 1e-11),
                "isobaric_specific_heat": round(random.uniform(10, 30), 2),
                "debye": round(random.uniform(150, 600), 2),
                "total_energy": total_energy,
                "defect_key": key,
                "defect_stoichiometry": stoich,
                "defect_configuration": f"{dtype}_config_{i}",
                "host_material": "diamond",
                "simulation_parameters": {
                    "Ensamble": "NVT",
                    "Temp": 1,
                    "ThermoTime": 5,
                    "Timestep": "1 fs",
                    "Length": 5,
                    "TrajInterval": 1,
                    "Calculator": "MACE",
                    "CalculatorParams": {
                        "model_paths": \
                            "../2023-12-10-mace-128-L0_energy_epoch-249.model",
                        "device": "cpu",
                    },
                    "Create_traj": True,
                },
            },
            chemical_formula_reduced=f"{el1}{el2}",
            cartesian_site_positions=positions,
            lattice_vectors=cell,
            nsites=natoms,
            species_at_sites=species,
        )

        entries[entry.id] = entry.to_dict()

    return entries


fake_entries = make_fake_entries(1000)
fake_host = {
    "HOST": MongoDBEntry(
        "HOST",
        elements=["C"],
        nelements=1,
        nsites=4,
        species_at_sites=[
            "C",
            "C",
            "C",
            "C",
        ],
        chemical_formula_descriptive="C4",
        mdse_fields={"total_energy": -50},
    ).to_dict()
}

db.clear_collection("structures")
db.write_dict_to_db(fake_entries, collection_str="structures")
db.write_dict_to_db(fake_host, collection_str="structures")

# -----------------------------------------------------------------------------
# Calculates formation energy for fake structures and formation energy for host
# -----------------------------------------------------------------------------

defect_formation_energy(db)

host_entry = next(
    iter(
        db.read_from_db(
            {"defect_key": None},
            outputs=["id", "total_energy", "chemical_formula_descriptive"],
            collection_str="structures",
        ).values()
    )
)

energy = host_entry["total_energy"]
element_count = get_nelements(host_entry["chemical_formula_descriptive"])

formation_energy, tot_chem_pot = calc_formation_energy(energy, element_count, db)

host_formation_entry = {
    "host": {
        "id": host_entry["id"],
        "defect_key": None,
        "formation_energy": formation_energy,
        "total_chemical_potential": tot_chem_pot,
    }
}
db.write_dict_to_db(host_formation_entry, collection_str="MACE_results")
