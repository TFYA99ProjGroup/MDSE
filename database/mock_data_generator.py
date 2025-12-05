# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

import logging
import random
import json
import uuid
from datetime import datetime
from pathlib import Path
from mdse.rm.dbmanager import MongoDBEntry

logger = logging.getLogger(__name__)


def generate_mock_entry(
        base_name: str, run_uuid: str, is_outlier: bool = False) -> dict:
    """
    Generates a single mock MongoDBEntry with semi-realistic data.

    Args:
        base_name (str): The base name for the entry (e.g., 'Cu_300K').
        run_uuid (str): A unique identifier for this specific run.
        is_outlier (bool): If True, generates values far from the mean.

    Returns:
        dict: A dictionary representation of the mock entry.
    """
    element = base_name.split('_')[0]
    nsites = 15

    # Generate MDSE properties
    # Base values for "normal" entries
    lindemann_mean, lindemann_std = 0.08, 0.01
    self_diffusion_mean, self_diffusion_std = 1.5e-9, 0.2e-9
    total_energy_per_atom_mean, total_energy_per_atom_std = -3.5, 0.01
    isobaric_specific_heat_mean, isobaric_specific_heat_std = 2.5e-4, 0.1e-4
    debye_mean, debye_std = 400, 20


    if is_outlier:
        # Generate values that are around 5 standard deviations away
        lindemann = lindemann_mean + random.uniform(4, 6) * lindemann_std
        self_diffusion = self_diffusion_mean - random.uniform(4, 6) \
            * self_diffusion_std
        isobaric_specific_heat = isobaric_specific_heat_mean + random.uniform(4, 6) \
            * isobaric_specific_heat_std
        debye = debye_mean - random.uniform(4, 6) * debye_std
        total_energy = (total_energy_per_atom_mean + random.uniform(4, 6) \
            * total_energy_per_atom_std) * nsites

    else:
        # Generate values close to the mean
        lindemann = random.gauss(lindemann_mean, lindemann_std)
        self_diffusion = random.gauss(self_diffusion_mean, self_diffusion_std)
        isobaric_specific_heat = random.gauss(isobaric_specific_heat_mean,
                                              isobaric_specific_heat_std)
        debye = random.gauss(debye_mean, debye_std)
        total_energy = random.gauss(total_energy_per_atom_mean,
                                    total_energy_per_atom_std) * nsites

    mdse_fields = {
        "lindemann": lindemann,
        "self_diffusion": self_diffusion,
        "isobaric_specific_heat": isobaric_specific_heat,
        "debye": debye,
        "total_energy": total_energy,
        "defect": {},
    }

    # Create the MongoDBEntry
    entry = MongoDBEntry(
        id=f"{base_name}_{run_uuid}",
        structure_features=["periodic"],
        mdse_fields=mdse_fields,
        last_modified=datetime.now(),
        elements=[element],
        nelements=1,
        elements_ratios=[1.0],
        chemical_formula_descriptive=element,
        chemical_formula_reduced=element,
        chemical_formula_anonymous="A",
        dimension_types=[1, 1, 1],
        nperiodic_dimensions=3,
        lattice_vectors=[
            [random.uniform(1.0, 9.0) for _ in range(3)],
            [random.uniform(1.0, 9.0) for _ in range(3)],
            [random.uniform(1.0, 9.0) for _ in range(3)],
        ],
        cartesian_site_positions=[
            [random.uniform(0.0, 50.0) for _ in range(3)]
            for _ in range(nsites)
        ],
        nsites=nsites,
        species_at_sites=[element] * nsites,
        species=[
            {
                "name": element,
                "chemical_symbols": [element],
                "concentration": [1.0],
            }
        ],
    )

    return entry.to_dict()


def create_mock_data_file(
    output_path: str, num_groups: int, docs_per_group: int, outliers_per_group: int = 1
    ):
    """
    Creates a JSON file with mock data for database testing.

    Args:
        output_path (str): The path to the output JSON file.
        num_groups (int): The number of distinct simulation groups (e.g., 'Cu_300K').
        docs_per_group (int): The number of documents to generate for each group.
        outliers_per_group (int): The number of outliers to generate within each group.
    """
    all_entries = []
    elements = ["Cu", "Fe", "Ni", "Al", "Ti"]
    temps = ["300K", "500K", "700K", "900K"]

    logger.info(f"Generating mock data for {num_groups} groups...")
    for i in range(num_groups):
        base_name = f"{random.choice(elements)}_{random.choice(temps)}"
        logger.info(f"Group '{base_name}': {docs_per_group} "
                    f"docs, {outliers_per_group} outliers")
        for j in range(docs_per_group):
            is_outlier = j < outliers_per_group
            run_uuid = str(uuid.uuid4())[:8]
            doc = generate_mock_entry(base_name, run_uuid, is_outlier=is_outlier)
            all_entries.append(doc)

    # Write to file
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2, default=lambda o: o.isoformat()
                      if hasattr(o, 'isoformat') else o)
    logger.info(f"Successfully created mock data file at: {output_path}")


if __name__ == "__main__":
    # Configuration
    NUM_GROUPS = 3
    DOCS_PER_GROUP = 10
    OUTLIERS_PER_GROUP = 1
    OUTPUT_FILE = "results/mock_simulation_data.json"

    create_mock_data_file(OUTPUT_FILE, NUM_GROUPS, DOCS_PER_GROUP, OUTLIERS_PER_GROUP)
