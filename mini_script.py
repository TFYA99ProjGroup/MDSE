#!/usr/bin/env python3

from ase.build import molecule
from ase.visualize import view
from ase.build import bulk
from ase.build import nanotube

# Test view
ch4 = molecule("CH4")
view(ch4)

# Cubic non-prim unit cell
mg_cube= bulk("Mg", "fcc", a=3.6, cubic=True)
mg_super_cube = mg_cube*(4,4,4)
view(mg_super_cube)

# Nanotube
cnt1 = nanotube(6, 0, length=4)
view(cnt1)

# FCC
"""from ase.lattice.cubic import FaceCenteredCubic
atoms = FaceCenteredCubic(
directions=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
symbol="Cu",
size=(4, 4, 4),
pbc=True)
view(atoms)"""


