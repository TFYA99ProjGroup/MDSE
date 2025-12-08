# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


import pytest
import uuid
from mdse.rm.dbmanager import DBManager
from database.mock_data_generator import generate_mock_entry


@pytest.fixture(scope="function")
def setup_db(address):
    """
    Provides a DBManager instance connected to a test database
    and ensures the test collection is cleared before and after the test.
    """
    db_name = "test_materials_db"
    collection_name = "test_structures"

    manager = DBManager(address)
    db = manager.client[db_name]
    collection = db[collection_name]

    # Ensure collection is empty before test
    collection.delete_many({})

    yield manager, db_name, collection_name

    # Teardown: clear the collection after the test
    collection.delete_many({})


def test_detect_outliers(setup_db):
    """
    Tests the outlier detection functionality by inserting mock data
    with a known outlier and verifying it is detected.
    """
    manager, db_name, collection_name = setup_db

    # Generate mock data with one clear outlier
    base_name = "Cu_300K"
    num_docs = 10
    outlier_index = 5
    docs_to_insert = []
    outlier_id = ""

    for i in range(num_docs):
        is_outlier = (i == outlier_index)
        run_uuid = str(uuid.uuid4())[:8]
        entry = generate_mock_entry(base_name, run_uuid, is_outlier=is_outlier)
        if is_outlier:
            outlier_id = entry['id']
        docs_to_insert.append(entry)

    collection = manager.client[db_name][collection_name]
    collection.insert_many(docs_to_insert)

    outliers = manager.detect_outliers(db_client=db_name, db_collection=collection_name)

    assert len(outliers) > 0, "Expected to find at least one outlier"

    outlier_exist = any(o['id'] == outlier_id and
                        o['property'] == 'lindemann' for o in outliers)
    assert outlier_exist, f"Outlier with ID {outlier_id} not detected for lindemann"
