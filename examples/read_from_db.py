from mdse.rm.dbmanager import DBManager

writer = DBManager("mongodb://admin:secret@localhost:27017/")

result = writer.read_from_db(
    conditions={"composition.elements": "Cu"},
    outputs=[
        "Structure_id",
        "atoms.elements",
        "Properties",
        "composition.chemical_formula_reduced",
    ],
)
print(result)
