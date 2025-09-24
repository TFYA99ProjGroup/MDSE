#!/usr/bin/env python3

from mdse.md.simulation import simulate_nve, create_crystal

from ase import units
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3 import EMT
from ase.visualize import view
from ase.build import bulk

# Cubic non-prim unit cell
mg_cube= bulk("Mg", "fcc", a=3.6, cubic=True)
mg_super_cube = mg_cube*(4,4,4)

MaxwellBoltzmannDistribution(mg_super_cube, temperature_K=800)

mg_super_cube.calc = EMT()
simulate_nve(mg_super_cube, timestep=2 * units.fs, length=400)

test_crystal = create_crystal(chem_notation = 'Cu', structure = 'fcc', a = 3.6, cubic=True)
view(test_crystal)
