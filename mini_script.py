#!/usr/bin/env python3

from ase import units
from ase.build import bulk, molecule, nanotube
from ase.visualize import view
from ase.md.verlet import VelocityVerlet
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3 import EMT, Trajectory

def createCrystal(chem_notation='H', structure='sc', positions=None, a=1.0, b=None, c=None, cubic=True):
    """Create a crystal or molecule."""
    if positions is None:
        return bulk(chem_notation, structure, a, b, c)

def simulateNVE(atoms, timestep, length):
    """Run NVE molecular dynamics."""
    dyn = VelocityVerlet(atoms, timestep=timestep)
    traj = Trajectory(f"{"".join(set(atoms.get_chemical_symbols()))}.traj", "w", atoms)
    dyn.attach(traj.write, interval=10)
    dyn.run(length)

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
    crystal = generateTestCrystal()
    view(crystal)
