#!/usr/bin/env python3

from ase import units
from ase.md.verlet import VelocityVerlet
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3 import EMT, Trajectory

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
    simulateNVE(mg_super_cube, timestep=2 * units.fs, length=400)
