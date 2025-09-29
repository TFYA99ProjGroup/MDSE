from pathlib import Path
from mdse.parser.parse_yml import main_read
from mdse.md.simulateMD import SimulateMD


def test_mdobject():
    path = Path("tests/test_file.yaml")
    sim_list = main_read(path)
    sim = next(iter(sim_list[0].values()))

    assert (sim.str() == {'Type': 'Cu', 'Structure': 'fcc', 'Lattice': 3.6,
            'Cubic': True, 'Temp': 800, 'Timestep': 2, 'Length': 400, 'TrajInterval': 10})
    sim3 = SimulateMD(chem_notation=sim['Type'], structure=sim.get(
        'Structure'), a=sim.get('Lattice'), cubic=sim.get('Cubic'),
        temperature=sim.get('Temp'),
        timestep=sim.get('Timestep'), length=sim.get('Length'),
        traj_interval=sim.get('TrajInterval'))
    sim3.simulate_nve()
