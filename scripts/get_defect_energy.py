# Parasitic script that takes data from existing db, and calculates
# defect formation energy for entries.

from mdse.rm.dbmanager import DBManager

mongodb = "mongodb://admin:secret@localhost:27017/"

# the db with all the good stuff in it
db = DBManager(mongodb)

# we should query for all structures in the db,
output = db.read_from_db({"element" : "He"},outputs=["chemical_potential"],collection_str="Chemical_potential")
print(output)

output2 = db.get_all_values(field="element",collection_str="Chemical_potential")
print(output2)

def get_chem_pot(store, stoichiometry):
    search = store.searcher()
    pattern = r"([A-Za-z]+):(-?\d+)"
    matches = {elem: -int(count) for elem, count in re.findall(pattern, stoichiometry)}

    search_chem_pot = search.variable(ChemicalPotential)
    search.add(search_chem_pot.material.is_in(*matches.keys()))

    search.output(search_chem_pot.material, "material")
    search.output(search_chem_pot.chemical_potential, "chem_pot")

    query_result = [item[0] for item in list(search)]
    query_result = {
        elem: chemical_potential for elem, chemical_potential in query_result
    }

    chemical_potential = 0
    for elem, count in matches.items():
        chemical_potential += query_result[elem] * count

    return chemical_potential

def get_defect_formation_energy(store, address, **query):
    search = store.searcher()
    search_defect_info = search.variable(DefectInfo)
    search_screen_result = search.variable(ScreenResult)
    search_host = search.variable(HostSuperCellResult)
    search_screen_cell = search.variable(ScreenCell)
    search_hull_distance = search.variable(HullDistance)

    search.add(search_defect_info.key == search_screen_cell.defect_key)
    search.add(search_defect_info.key == search_hull_distance.defect_key)
    search.add(search_screen_result.defect_key == search_defect_info.key)

    search.add(search_screen_cell.charge == search_hull_distance.defect_charge)
    search.add(search_screen_cell.spin == search_hull_distance.defect_spin)

    search.add(search_screen_result.charge == 0)
    search.add(search_hull_distance.min_distance < 1e-5)

    if query.get("key") is not None:
        search.add(search_defect_info.key == query["key"])

    search.output(search_defect_info.key, "key")
    search.output(search_defect_info.defect_stoichiometry, "stoichiometry")
    search.output(search_screen_result.total_energy_coarse, "tot_energy_defect")
    search.output(search_host.total_energy, "tot_energy")
    search.output(search_screen_result.spin, "spin")
    search.output(search_defect_info.defect_type, "defect_type")

    matches = [defecttuple[0] for defecttuple in list(search)]

    dft_data = {}
    for match in matches:
        stoichiometry = match[1]

        chem_pot = get_chem_pot(store, stoichiometry)

        defect_formation_energy = match[2] - match[3] - chem_pot

        dft_data[str(match[0]) + "_" + str(match[4])] = {
            "defect_key": str(match[0]),
            "stoichiometry": match[1],
            "defect_type": match[5],
            "tot_energy_defect": match[2],
            "tot_energy_host": match[3],
            "defect_formation_energy": defect_formation_energy,
            "spin": match[4],
        }

    db_manager = DBManager(address)

    db_manager.write_dict_to_db(dft_data, collection_str="DFT_data")

