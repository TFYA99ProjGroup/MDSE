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

    expected_new_docs = 4

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


def validate_db_document(data):
    # Top-level keys
    assert data["simulation_id"] is not None
    assert isinstance(data["simulation_id"], str)

    assert "atoms" in data
    assert isinstance(data["atoms"], dict)

    assert "composition" in data
    assert isinstance(data["composition"], dict)

    assert "properties" in data
    assert isinstance(data["properties"], dict)

    # atoms dict
    atoms = data["atoms"]

    assert "elements" in atoms
    assert isinstance(atoms["elements"], list)
    assert all(isinstance(e, str) for e in atoms["elements"])

    assert "positions" in atoms
    assert isinstance(atoms["positions"], list)
    for pos in atoms["positions"]:
        assert isinstance(pos, list)
        assert all(isinstance(x, (float, int)) for x in pos)

    assert "lattice_vectors" in atoms
    assert isinstance(atoms["lattice_vectors"], list)
    for vec in atoms["lattice_vectors"]:
        assert isinstance(vec, list)
        assert all(isinstance(x, (float, int)) for x in vec)

    # composition dict
    comp = data["composition"]

    assert "elements" in comp
    assert isinstance(comp["elements"], list)
    assert all(isinstance(e, str) for e in comp["elements"])

    assert "chemical_formula_reduced" in comp
    assert isinstance(comp["chemical_formula_reduced"], str)

    # Properties dict
    props = data["properties"]

    expected_props = [
        "lindemann",
        "self-diffusion",
        "isobaric specific heat",
        "debye",
    ]

    for key in expected_props:
        assert key in props, f"Missing property {key}"
        assert isinstance(props[key], (float, int))
