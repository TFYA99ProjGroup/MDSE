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
    
    if (source == "jsonl"):
        path = config_data.get("path")
        file_path = Path(path)
        logger.debug(f".json found at {file_path}")

        data = []
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    data.append(json.loads(line))


        #Need the defectinfo field, containing {"defect_size" : , "defect_type" : }
        for dat in data:
            
            defect = dat["defect"]
            if not defect:
                dat["DefectInfo"] = {}
                dat["DefectInfo"]["defect_size"] = -1
                dat["DefectInfo"]["defect_type"] = "Error"
                continue
            numb, defname = format_jsonl(defect)
            dat["DefectInfo"] = {}
            dat["DefectInfo"]["defect_size"] = numb
            dat["DefectInfo"]["defect_type"] = defname
  

        return data


    elif (source == "mongo"):

        uri = config_data.get("uri")
        db_name = config_data.get("database")
        table_name = config_data.get("table")

        if not uri or not db_name or not table_name:
            raise RuntimeError("Config for mongo lacks uri or database or table field")

        client = MongoClient(uri)
        db = client[db_name]
        table = db[table_name]

        #Needs to return [ {sim_id : 1, energy : 2},  {sim_id : 2, energy : 4}] so
        #list of dictionaries.
        #Each dictionary is information about one result/simulation.
        dum = False
        if dum:
            return table

        raise RuntimeError("Not implemented for mongoDB yet")

def format_jsonl(defect_dat):
    """

    C:1_Rb:-1	Rb_C	0
    C:1_Rb:-1	Int_Rb:Vac_C	(1/2, 1/8, 1/8):0

    stichometry same for two different difects.
    But if configuration = 0, then its substitution!

    """
    
    stoichiometry = defect_dat["stoichiometry"]
    config = defect_dat["configuration"]

    if "C:1_" in stoichiometry and config == '0':
        #Substitution of the other element
        other_ = stoichiometry.split("_")[1]
        other = other_.split(":")[0]
        return 1, other + "_C"
    
    if "_C:1" in stoichiometry and config == '0':
        #Substitution of the other element
        other_ = stoichiometry.split("_")[0]
        other = other_.split(":")[0]
        return 1, other + "_C"

    if "C:1_" in stoichiometry and config != '0':
        #Either Vac_C + Inter, or int_C + int_other
        #print(stoichiometry)
        other_ = stoichiometry.split("_")[1]
        other = other_.split(":")[0]
        other_n = other_.split(":")[1]

        #print(other_n)
        if other_n == '-1':
            #Vac_c + inter
            return 2, "Int_" + other + ":Vac_C"
        if other_n == '-2':
            #inter + subst.
            return 2, "Int_" + other + ":" + other + "_C"
        

    if "_C:1" in stoichiometry and config != '0':
        #Either Vac_C + Inter, or int_C + int_other
        #print(stoichiometry)
        other_ = stoichiometry.split("_")[0]
        other = other_.split(":")[0]
        other_n = other_.split(":")[1]

        #print(other_n)
        if other_n == '-1':
            #Vac_c + inter
            return 2, "Int_" + other + ":Vac_C"
        if other_n == '-2':
            #inter + subst.
            return 2, "Int_" + other + ":" + other + "_C"
        

    if "C:2_" in stoichiometry:
        #Sub and vacancy/sub
        other_ = stoichiometry.split("_")[1]
        other = other_.split(":")[0]
        other_n = other_.split(":")[1]

        if other_n == '-1':
            #Sub other, vac C
            return 2, other + "_C" + ":Vac_C"
        if other_n == '-2':
            #Sub other, sub other
            return 2, other + "_C" + ":" + other + "_C"
        
    if "_C:2" in stoichiometry:
        #Sub and vacancy
        other_ = stoichiometry.split("_")[0]
        other = other_.split(":")[0]
        other_n = other_.split(":")[1]

        if other_n == '-1':
            #Sub other, vac C
            return 2, other + "_C" + ":Vac_C"
        if other_n == '-2':
            #Sub other, sub other
            return 2, other + "_C" + ":" + other + "_C"
        
    #Should now be a lonely element
    if not stoichiometry:
        #If None, then
        return -1, "Error"


    other = stoichiometry.split(":")[0]
    nr = stoichiometry.split(":")[1]

    if nr == '-1':
        #Then single interstition
        return 1, "Int_" + other
    if nr == '-2':
        #int-int
        return 2, "Int_" + other + ":Int_" + other

    return -1, "Error"