from datetime import datetime
from pymongo import MongoClient

# Connect to MongoDB (must match your optimade_config.json)
client = MongoClient("mongodb://admin:secret@localhost:27017/?authSource=admin")
db = client["materials_db"]
structures = db["structures"]

# Small OPTIMADE-compliant structure
doc = {
  "id": "descriptive_name", #must
  # "immutable_id": None, #optional (handled by alias of MongoDB's _id)
  "type": "structures", #must
  "structure_features": [], #must, but can be empty list

  # Here we can add custom fields as needed
  "custom_example_int": 1, #optional
  "custom_example_str": "example", #optional
  "custom_example_list": [1, 2, 3], #optional
  "custom_example_dict": {"key": "value"}, #optional

  # Should fields, very good ideas to have
  "last_modified": datetime.now(), #should
  "elements": None, #should
  "nelements": None, #should
  "elements_ratios": None, #should
  "chemical_formula_descriptive": None, #should
  "chemical_formula_reduced": None, #should
  "chemical_formula_anonymous": None, #should
  "dimension_types": None, #should
  "nperiodic_dimensions": None, #should
  "lattice_vectors": None, #should
  "cartesian_site_positions": None, #should
  "nsites": None, #should
  "species_at_sites": None, #should
  "species": None, #should

  # Optional fields, but good if queryable
  "chemical_formula_hill": None, #optional
  "space_group_symmetry_operations_xyz": None, #optional
  "space_group_symbol_hall": None, #optional
  "space_group_symbol_hermann_mauguin": None, #optional
  "space_group_symbol_hermann_mauguin_extended": None, #optional
  "space_group_it_number": None, #optional
  "assemblies": None, #optional
}

# Insert the document
structures.insert_one(doc)
print("Structure added!")
