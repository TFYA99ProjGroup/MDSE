from ase import units
from ase.lattice.cubic import FaceCenteredCubic
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution

from ase.md.langevin import Langevin
from ase.md.nose_hoover_chain import IsotropicMTKNPT
from ase.md.verlet import VelocityVerlet

from asap3 import Trajectory

# Use Asap for a huge performance increase if it is installed
use_asap = True

if use_asap:
    from asap3 import EMT

    size = 10
else:
    from ase.calculators.emt import EMT

    size = 3

# Set up a crystal
atoms = FaceCenteredCubic(
    directions=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    symbol='Cu',
    size=(size, size, size),
    pbc=True,
)
atoms = atoms

# Describe the interatomic interactions with the Effective Medium Theory
atoms.calc = EMT()

# Set the momenta corresponding to T=300K
MaxwellBoltzmannDistribution(atoms, temperature_K=300)

# Pressure
p_au = 3.85e-2 # atomic units, (1 atm = 3.44e-9)
T_K = 300

atoms.info['p_au'] = p_au
atoms.info['T_K'] = T_K

dyn = IsotropicMTKNPT(atoms, 5 * units.fs, temperature_K=T_K, pressure_au=p_au, tdamp=500*units.fs, pdamp=1000*units.fs)  # 5 fs time step.
traj = Trajectory("test.traj", "w", atoms)


dyn.attach(traj.write, interval=10)


def printenergy(a=atoms):  # store a reference to atoms in the definition.
    """Function to print the potential, kinetic and total energy."""
    epot = a.get_potential_energy() / len(a)
    ekin = a.get_kinetic_energy() / len(a)
    print(
        f'Energy per atom: Epot ={epot:6.3f}eV  Ekin = {ekin:.3f}eV '
        f'(T={ekin / (1.5 * units.kB):3.0f}K) Etot = {epot + ekin:.3f}eV'
    )


# Now run the dynamics
dyn.attach(printenergy, interval=10)
printenergy()
dyn.run(5000)

