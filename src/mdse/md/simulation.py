#!/usr/bin/env python3

from ase.md.verlet import VelocityVerlet
from asap3 import Trajectory
from ase.build import bulk
# TODO Axel/Oskar: Check if asap is better optimized for all following functions instead of ase.
# Add more params to createCrystal

def create_crystal(chem_notation='H', structure='sc', positions=None, a=1.0, b=None, c=None, cubic=True):
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
    

def simulate_nve(atoms, timestep, length, trajInterval=10):
    dyn = VelocityVerlet(atoms, timestep=timestep)
    traj = Trajectory(f"{"".join(set(atoms.get_chemical_symbols()))}.traj", "w", atoms)
    dyn.attach(traj.write, interval=trajInterval)

    dyn.run(length)
