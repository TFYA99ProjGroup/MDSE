#!/usr/bin/env python3

from mdse.md.simulation import simulate_nve, create_crystal
from ase import units
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3 import EMT
from ase.visualize import view
from ase.build import bulk

# Cubic non-prim unit cell
test_crystal = create_crystal(chem_notation = 'Cu', structure = 'fcc', a = 3.6, cubic=True)
super_cube = test_crystal*(4,4,4)

MaxwellBoltzmannDistribution(super_cube, temperature_K=800)

super_cube.calc = EMT()
simulate_nve(super_cube, timestep=2 * units.fs, length=400)
