import os
from os import path
from mdse.md.simulateMD import SimulateMD


def test_mdobject():

    sim = {
        'Type': 'Cu',
        'Structure': 'fcc',
        'Lattice_a': 3.6,
        'Cubic': True,
        'Temp': 800,
        'Timestep': 2,
        'Length': 800,
        'TrajInterval': 10
    }

    sim3 = SimulateMD(sim)

    assert (sim3.chem_notation == 'Cu')
    assert (sim3.structure == 'fcc')
    assert (sim3.a == 3.6)
    assert (sim3.temperature == 800)

    sim3.simulate_nve()

    traj_file = "Cu_800.traj"

    assert path.exists(traj_file)
    os.remove(traj_file)

