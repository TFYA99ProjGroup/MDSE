"""
This example utilises the resultMD class to calculate some properties
and then store them in a MongoDB database.
"""
from mdse.md.resultMD import ResultMD
from pymongo import MongoClient

result = ResultMD.from_file("Cu_300.traj") # NVT
msd = result.calc_msd()
lindemann = result.calc_lindemann()
self_diffusion = result.calc_self_diff()
iso_heat_cap_per_atom = result.calc_isochoric_heat_capacity_per_atom()

# Connect to MongoDB. MongoDB must be running.
client = MongoClient("mongodb://admin:secret@localhost:27017/")

# Select your database
db = client["materials_db"]

# Select a "table" in the database
examples = db["examples"]

doc = {
  "structure_id": "Cu_300K",
  "atoms": {
    "elements": ["Cu", "Cu", "Cu"],
    "positions": [[0,0,0],[1.8,0,0],[0,1.8,0]],  # representative frame
    "lattice_vectors": [[3.6149,0,0],[0,3.6149,0],[0,0,3.6149]]
  },
  "composition": {
    "elements": ["Cu"],
    "chemical_formula_reduced": "Cu"
  },
  "properties": {
    "msd": msd,
    "lindemann": lindemann,
    "self_diffusion": self_diffusion,
    "isochoric_heat_capacity_per_atom": iso_heat_cap_per_atom
  }
}

examples.insert_one(doc)

for s in examples.find():
    print(s)
