from pymongo import MongoClient

# Will be moved to examples later

# Connect to MongoDB
client = MongoClient("mongodb://admin:secret@localhost:27017/")

# Select your database
db = client["materials_db"]

# Select collection (like a table)
structures = db["structures"]

doc1 = {
    "structure_id": "SiO2_300K_0001",
    "atoms": {
        "elements": ["Si", "O", "O"],
        "positions": [[0,0,0], [0.5,0.5,0], [0.5,0,0.5]],
        "lattice_vectors": [[5.43,0,0], [0,5.43,0], [0,0,5.43]]
    },
    "properties": {
        "energy_total_eV": -12.34,
        "temperature_K": 300,
        "pressure_GPa": 0.001
    },
    "composition": {
        "elements": ["Si", "O"],
        "chemical_formula_reduced": "SiO2"
    }
}

structures.insert_one(doc1)

docs = [
    {"structure_id": "Si_0001", "atoms": {"elements": ["Si"], "positions": [[0,0,0]]}},
    {"structure_id": "O2_0001", "atoms": {"elements": ["O","O"],
                                          "positions": [[0,0,0],[0.5,0.5,0]]}}
]

structures.insert_many(docs)

# Find all structures
for s in structures.find():
    print(s)

print("----")

# Find structures containing "O"
for s in structures.find({"composition.elements": "O"}):
    print(s)
