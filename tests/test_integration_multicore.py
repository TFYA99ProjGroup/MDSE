from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from mdse.rm.dbmanager import DBManager
from test_integration import validate_db_document

from pathlib import Path
import json
import pymongo
import os
import pytest


@pytest.mark.mpi
def test_multicore(address):
    file_path = Path(__file__).resolve()
    path = file_path.parent / "test_result_sim.yaml"
    sim_list = main_read(path)

    try:
        import mpi4py.MPI as MPI

        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
    except Exception:
        return

    # Kör simulationer parallellt
    rm = RunManager(sim_list)
    rm.run_simulations()

    comm.Barrier()

    # Endast rank 0 validerar
    if rank == 0:
        validate_rm_without_runmanager(file_path, address)


def validate_rm_without_runmanager(file_path, address):
    jsonfiledir = file_path.parent.parent / "results"
    json_files = list(jsonfiledir.glob("*.json"))
    assert len(json_files) == 1, f"Expected 1 json files, found {len(json_files)}"

    for jsonfile in json_files:
        with open(jsonfile, "r", encoding="utf-8") as f:
            data = json.load(f)
            for data_point in data:
                validate_db_document(data_point)

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
