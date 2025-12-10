# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


import json
from pathlib import Path
import logging
from pymongo import MongoClient
from mdse.rm.dbmanager import DBManager

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
        logger.debug(f"Creating plots from DB")

        uri = config_data.get("uri")

        #Create the client
        client = DBManager(uri)
        #Get mace entries
        mace_entries = client.read_from_db(
            conditions={},
            outputs=[
                "defect_key",
                "formation_energy"
            ],
            collection_str="MACE_results"
        )
        #Get DFT entries
        dft_entries = client.read_from_db(
            conditions={},
            outputs=[
                "defect_key",
                "defect_formation_energy",
                "spin",
                "defect_type",
            ],
            collection_str="DFT_data"
        )

        #Get structure entries (where properties and results are stored)
        structure_entries = client.read_from_db(
            conditions={},
            outputs=[
                "lindemann",
                "self_diffusion",
                "debye",
                "total_energy",
                "defect_key"
            ],
            collection_str="structures"
        )
        logger.debug("Sucsesfully connected to collections in DB")

        #Convert to list, for easy handling
        all_mace_entries = list(mace_entries.values())
        all_dft_entries = list(dft_entries.values())
        all_structure_entries = list(structure_entries.values())


        final_data = []
        for mace_entry in all_mace_entries:
            def_id = mace_entry["defect_key"]
            #Will get multiple entries, because diferent spins.
            #Compare Mace to multiple DFT-spins

            #Find dft_entries that match
            matching_dft = []
            for dft_ent in all_dft_entries:
                if dft_ent["defect_key"] == def_id:
                    matching_dft.append(dft_ent)

            #Add structure data to mace data (Should be 1:1 match)
            for struct_match in all_structure_entries:
                if struct_match.get("defect_key") == def_id:
                   mace_entry["lindemann"] = struct_match["lindemann"]
                   mace_entry["energy"] = struct_match["total_energy"]
                   mace_entry["self_diffusion"] = struct_match["self_diffusion"]
                   mace_entry["debye"] = struct_match["debye"]

            logger.debug("Added structure data to mace entries")
            #Collect dft data (Different spins, not 1:1 match)
            for dft_entry in matching_dft:
                mace_copy = mace_entry.copy()
                # Extract fields we need
                mace_copy["DFT_defect_formation_energy"] = dft_entry.get("defect_formation_energy")
                mace_copy["delta_E"] = mace_copy["DFT_defect_formation_energy"] - mace_copy["formation_energy"]
                mace_copy["DefectInfo"] = {"defect_type" : dft_entry.get("defect_type")}
                mace_copy["spin"] = dft_entry.get("spin")
                final_data.append(mace_copy)
            logger.debug("Added DFT data to entries")
                
        for entry in final_data:
            #Fix some data
            def_type = entry["DefectInfo"]["defect_type"]

            entry["DefectInfo"]["defect_size"] = get_def_size(def_type)
            entry["DefectInfo"]["vacancy"] = get_vacancy(def_type)

        logger.debug(f"Sucsesfully created {len(final_data)} data points.")
        return final_data




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