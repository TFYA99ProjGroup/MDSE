#!/usr/bin/env python3

from ase import units
from ase.build import bulk, molecule, nanotube
from ase.visualize import view
from ase.md.verlet import VelocityVerlet
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3 import EMT, Trajectory
# TODO Axel/Oskar: Check if asap is better optimized for all following functions instead of ase.
# Add more params to createCrystal, fix cubic
# Maybe move down som imports to __main__

def createCrystal(chem_notation='H', structure='sc', positions=None, a=3.6, b=None, c=None, cubic=True):
    """Create the atom or molecule or crystal object from the specified params.

    Key args:
    chemNotation -- the chemical notation of the object (default: 'H')
    structure -- The Lattice types or Crystal structure of the object (default: 'sc')
    positions -- Individual atomic positions (optional argument)
    a -- lattice constant
    b -- secondary lattice constant (optional argument)
    c -- third lattice constant (optional argument)
    cubic --
    """
    if positions is None:
        crystal = bulk(chem_notation, structure, a, b, c)
    else:
        crystal =  bulk(chem_notation, positions, a, b, c)
    return crystal


def simulateNVE(atoms, timestep, length):
    """Run NVE molecular dynamics."""
    dyn = VelocityVerlet(atoms, timestep=timestep)
    traj = Trajectory(f"{"".join(set(atoms.get_chemical_symbols()))}.traj", "w", atoms)
    dyn.attach(traj.write, interval=10)
    dyn.run(length)

## Patrik grejor
# Did this to be able to run code in jupyter notebook
def generateTestCrystal():
    """Generate a demo crystal for testing/visualization."""
    mg_cube = bulk("Mg", "fcc", a=3.6, cubic=True)
    mg_super_cube = mg_cube*(4,4,4)
    MaxwellBoltzmannDistribution(mg_super_cube, temperature_K=800)
    mg_super_cube.calc = EMT()
    test_crystal = createCrystal(chem_notation='Cu', structure='fcc', a=3.6)
    return test_crystal

if __name__ == "__main__":
    # Test crystal
    crystal = createCrystal(chem_notation="N", structure="fcc", a=3.6, cubic=True)
    view(crystal)
