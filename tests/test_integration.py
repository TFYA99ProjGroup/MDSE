from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from pathlib import Path
import json


def test_regular_run():
    file_path = Path(__file__).resolve()
    path = file_path.parent / "test_result_sim.yaml"
    print(path)
    sim_list = main_read(path)
    rm = RunManager(sim_list)
    rm.run_simulations()
    jsonfiledir = file_path.parent.parent / "results"
    for jsonfile in jsonfiledir.iterdir():
        if jsonfile.suffix == ".json":
            assert jsonfile.exists(), f"File does not exist: {jsonfile}"
            with open(jsonfile, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(data)

                assert data["Structure_id"] is not None
                assert isinstance(data["Structure_id"], str)

                assert "atoms" in data
                assert isinstance(data["atoms"], dict)

                assert "composition" in data
                assert isinstance(data["composition"], dict)

                assert "Properties" in data
                assert isinstance(data["Properties"], dict)

                # atoms dict
                atoms = data["atoms"]
                assert "elements" in atoms
                assert isinstance(atoms["elements"], list)
                assert all(isinstance(e, str) for e in atoms["elements"])

                assert "positions" in atoms
                assert isinstance(atoms["positions"], list)
                for pos in atoms["positions"]:
                    assert isinstance(pos, list)
                    assert all(isinstance(x, (float, int)) for x in pos)

                assert "lattice_vectors" in atoms
                assert isinstance(atoms["lattice_vectors"], list)
                for vec in atoms["lattice_vectors"]:
                    assert isinstance(vec, list)
                    assert all(isinstance(x, (float, int)) for x in vec)

                # composition dict
                comp = data["composition"]
                assert "elements" in comp
                assert isinstance(comp["elements"], list)
                assert all(isinstance(e, str) for e in comp["elements"])

                assert "chemical_formula_reduced" in comp
                assert isinstance(comp["chemical_formula_reduced"], str)

                # Properties dict
                props = data["Properties"]
                expected_props = [
                    "Lindemann",
                    "Self-diffusion",
                    "Isobaric specific heat",
                    "Debye",
                ]
                for key in expected_props:
                    assert key in props
                    assert isinstance(props[key], (float, int))
