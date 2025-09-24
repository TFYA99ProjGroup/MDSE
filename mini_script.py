#!/usr/bin/env python3

from ase import units
from ase.md.verlet import VelocityVerlet
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3 import EMT, Trajectory
# TODO Axel/Oskar: Check if asap is better optimized for all following functions instead of ase.
# Add more params to createCrystal

def createCrystal(chem_notation='H', structure='sc', positions=None, a=1.0, b=None, c=None, cubic=True):
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
    # Define if we're using structure or positions
    if positions == None:
        crystal = bulk(chem_notation, structure, a, b, c)
        return crystal
    #else
    

def simulateNVE(atoms, timestep, length):
    dyn = VelocityVerlet(atoms, timestep=timestep)
    traj = Trajectory(f"{"".join(set(atoms.get_chemical_symbols()))}.traj", "w", atoms)
    dyn.attach(traj.write, interval=10)

    dyn.run(length)

if __name__ == "main":
    from ase.build import molecule
    from ase.visualize import view
    from ase.build import bulk
    from ase.build import nanotube

    # Cubic non-prim unit cell
    mg_cube= bulk("Mg", "fcc", a=3.6, cubic=True)
    mg_super_cube = mg_cube*(4,4,4)

    MaxwellBoltzmannDistribution(mg_super_cube, temperature_K=800)

    mg_super_cube.calc = EMT()
    #simulateNVE(mg_super_cube, timestep=2 * units.fs, length=400)
    test_crystal = createCrystal(chem_notation = 'Cu', structure = 'fcc', a = 3.6, cubic=True)
    view(test_crystal)
