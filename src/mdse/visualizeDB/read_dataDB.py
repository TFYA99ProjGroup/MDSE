# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


import json
from pathlib import Path
import logging
from pymongo import MongoClient

logger = logging.getLogger(__name__)

"""
Should return a dictionary.
Later, adapt so can read from mongoDB.
But still should return a dictionary

"""


def read_data(config_data):
    """Reads the data we whant to plot. Stored in .json or mongoDB.

    arg:
        config_data(str): Information about data, such as location, what type etc.

    returns:
        data(dic): Dictionary containing the data about simulations
    """
    logger.debug("Start getting data to visualize on")
    source = config_data.get("data_source")

    if (source == "json"):
        logger.debug("Found data as .json")
        path = config_data.get("path")
        if not path:
            raise RuntimeError(".json path missing")

        file_path = Path(path)
        logger.debug(f".json found at {file_path}")

        if not file_path.is_file():
            raise RuntimeError("Path not to .json file")

        try:
            with open(file_path,"r") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            raise RuntimeError("Invalid form in .json file")

        logger.debug(f"Succesfully read .json at {file_path}")
        return data


    elif (source == "mongo"):

        uri = config_data.get("uri")
        db_name = config_data.get("database")
        table_name = config_data.get("table")

        #if not uri or not db_name or not table_name:
        #    raise RuntimeError("Config for mongo lacks uri or database or table field")

        client = MongoClient(uri)
        db = client["materials_db"]

        DFT_data = db["DFT_data"]
        MACE_data = db["MACE_results"]

        final_data = [] #[{id: 1, ...}, {id: 2,....}]

        # Get all documents
        all_mace_entries = []
        for doc in MACE_data.find():
            doc["_id"] = str(doc["_id"])  # optional, to make JSON-friendly
            all_mace_entries.append(doc)

        for mace_entry in all_mace_entries:
            def_id = mace_entry["defect_key"]

            dft_entry = DFT_data.find_one({"defect_key" : def_id})
            #Will get multiple entries, because diferent spins.
        
            if dft_entry:
                # Extract fields we need
                mace_entry["DFT_defect_formation_energy"] = dft_entry.get("defect_formation_energy")
                mace_entry["DefectInfo"] = {"defect_type" : dft_entry.get("defect_type")}
                mace_entry["DefectInfo"]["spin"] = dft_entry.get("spin")
            else:
                print("SOMETINH BAD HAPPENED!")
                
        temp = True
        for entry in all_mace_entries:
            #Calculate energy diff, and fix format
            entry["delta_E"] = abs(entry["DFT_defect_formation_energy"] - entry["formation_energy"])

            def_type = entry["DefectInfo"]["defect_type"]

            entry["DefectInfo"]["defect_size"] = get_def_size(def_type)
            entry["DefectInfo"]["vacancy"] = get_vacancy(def_type)
            if temp:
                entry["avg_a"] = 1
                temp = False
            else:
                entry["avg_a"] = 2
                temp = True

        print(f"Found {len(all_mace_entries)} entries")
        return all_mace_entries
     


        #db = client[db_name]
        #table = db[table_name]

        #Needs to return [ {sim_id : 1, energy : 2},  {sim_id : 2, energy : 4}] so
        #list of dictionaries.
        #Each dictionary is information about one result/simulation.
        dum = False
        if dum:
            return table

        raise RuntimeError("Not implemented for mongoDB yet")



def get_vacancy(def_type):
    """Checks if there is a vacancy. Returns nr of vac"""

    if "Vac_" in def_type:
        return 1
    return 0

def get_def_size(def_type):
    """Gets number of defects"""

    if ":" in def_type:
        return 2
    return 1