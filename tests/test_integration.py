# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from mdse.rm.dbmanager import DBManager

from pathlib import Path
import json
import pymongo
import os


def test_regular_onecore(address):
    file_path = Path(__file__).resolve()
    path = file_path.parent / "test_result_sim.yaml"
    sim_list = main_read(path)
    validate_rm(file_path, sim_list, address)


def validate_rm(file_path, sim_list, address):
    rm = RunManager(sim_list)
    rm.run_simulations()
    jsonfiledir = file_path.parent.parent / "results"
    json_files = list(jsonfiledir.glob("*.json"))
    assert len(json_files) == 1, f"Expected 1 json files, found {len(json_files)}"

    for jsonfile in jsonfiledir.iterdir():
        if jsonfile.suffix == ".json":
            assert jsonfile.exists(), f"File does not exist: {jsonfile}"
            with open(jsonfile, "r", encoding="utf-8") as f:
                for data in json.load(f):
                    validate_db_document(data)

    db_str = "test_db"
    collection_str = "test_collection"

    client = pymongo.MongoClient(address)
    db = client[db_str]
    collection = db[collection_str]

    collection.delete_many({})
    count_before = collection.count_documents({})

    writer = DBManager(address)
    writer.write_jsonfiles_to_db(jsonfiledir, db_str, collection_str)

    count_after = collection.count_documents({})

    expected_new_docs = 8

    assert count_after - count_before == expected_new_docs, (
        f"Expected {expected_new_docs} new documents, got {count_after - count_before}"
    )

    for doc in collection.find({}):
        doc.pop("_id", None)
        validate_db_document(doc)

    for path in json_files:
        try:
            os.remove(path)
        except PermissionError:
            pass
        except IsADirectoryError:
            pass

    collection.delete_many({})


def validate_db_document(doc):
    # Mandatory string fields
    assert "id" in doc and isinstance(doc["id"], str)
    assert "type" in doc and isinstance(doc["type"], str)
    assert doc["type"] == "structures"

    # Simple list fields
    assert "elements" in doc
    assert isinstance(doc["elements"], list)
    assert all(isinstance(e, str) for e in doc["elements"])

    # Integers
    assert "nelements" in doc
    assert isinstance(doc["nelements"], int)

    # Optional fields that are allowed to be None
    nullable_fields = [
        "elements_ratios",
        "chemical_formula_descriptive",
        "chemical_formula_anonymous",
        "dimension_types",
        "nperiodic_dimensions",
        "lattice_vectors",
        "cartesian_site_positions",
        "nsites",
        "species_at_sites",
        "species",
        "chemical_formula_hill",
        "space_group_symmetry_operations_xyz",
        "space_group_symbol_hall",
        "space_group_symbol_hermann_mauguin",
        "space_group_symbol_hermann_mauguin_extended",
        "space_group_it_number",
        "assemblies",
    ]

    for f in nullable_fields:
        assert f in doc, f"Missing optional field {f}"
        assert doc[f] is None or isinstance(doc[f], (str, list, dict, int, float))

    # Required numeric properties
    numeric_properties = [
        "lindemann",
        "self_diffusion",
        "isobaric_specific_heat",
        "debye",
    ]

    for prop in numeric_properties:
        assert prop in doc, f"Missing property {prop}"
        assert isinstance(doc[prop], (float, int))

    # last_modified timestamp
    assert "last_modified" in doc

    # structure_features must be a list
    assert "structure_features" in doc
    assert isinstance(doc["structure_features"], list)
