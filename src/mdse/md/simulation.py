#!/usr/bin/env python3

from ase import Atoms
from ase.md.verlet import VelocityVerlet
from asap3 import Trajectory
from ase.build import bulk
# TODO Axel/Oskar: Check if asap is better optimized for
# all following functions instead of ase.
# Add more params to createCrystal


def create_crystal(
    chem_notation="H",
    structure="sc",
    positions=None,
    a: float = 1.0,
    b: float = None,
    c: float = None,
    cubic=True,
) -> Atoms:
    """Create the atom or molecule or crystal object from the specified params.

    Key args:
    chemNotation -- the chemical notation of the object (default: 'H')
    structure -- The Lattice types or Crystal structure of the object (default: 'sc')
    positions -- Individual atomic positions (optional argument)
    a (float) -- lattice constant
    b (float) -- secondary lattice constant (optional argument)
    c (float) -- third lattice constant (optional argument)
    cubic --
    """
    # Define if we're using structure or positions
    if positions is None:
        crystal = bulk(chem_notation, structure, a=a, b=b, c=c, cubic=cubic)
        return crystal
    # else


def print_energy(atoms):
    epot = atoms.get_potential_energy()
    ekin = atoms.get_kinetic_energy()
    temp = atoms.get_temperature()
    print(
        f"Energy per atom: Epot ={epot:6.3f}eV  Ekin = {ekin:.3f}eV "
        f"(T={temp:.3f}K) Etot = {epot + ekin:.3f}eV"
    )


def simulate_nve(atoms, timestep, length, trajInterval=10):
    dyn = VelocityVerlet(atoms, timestep=timestep)
    symbols = "".join(set(atoms.get_chemical_symbols()))
    traj = Trajectory(f"{symbols}.traj", "w", atoms)

    dyn.attach(traj.write, interval=trajInterval)
    dyn.attach(print_energy, interval=trajInterval, atoms=atoms)

    dyn.run(length)
