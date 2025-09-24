from ase import Atoms
from ase.md.verlet import VelocityVerlet
from asap3 import Trajectory
from ase.build import bulk 
from ase.visualize import view

from mdse.parser.parse_yml import main_read

class SimulateMD:
    def __init__(self, chem_notation = 'H', structure = 'sc', positions = None, a = 3.6, b = None, c = None, cubic = True):
        self.chem_notation = chem_notation
        self.structure = structure
        self.positions = positions
        self.a = a
        self.b = b
        self.c = c
        self.cubic = cubic


    def view_super_crystal(self):
        if self.positions == None:
            crystal = bulk(self.chem_notation, self.structure, self.a, self.cubic)
            super_crystal = crystal*(4,4,4)
            view(super_crystal)


    def print_some_stuff(self):
        print(f"Element: {self.chem_notation}")
        print(f"Lattice(a): {self.a}")


# Test defined
sim1 = SimulateMD(chem_notation='C', structure='fcc', a=1.0, b=1.0, c=1.0, cubic=True)
#sim1.print_some_stuff()
#sim1.view_super_crystal()

# Test empty
#sim2 = SimulateMD()
#sim2.view_super_crystal()


# Det funkar, måste bara göra snyggt, samt lägga till ex. NVE funktion

## lol nice sökväg
sim_list = main_read("../../../examples/test_file.yaml")

# sim_list[0] is the first simulation
# sim equals the dictionary of the first simulation
sim = next(iter(sim_list[0].values()))

# sim.get() picks the values from the simulation
sim3 = SimulateMD(chem_notation=sim.get('Type'), structure=sim.get('Structure'), a=sim.get('Lattice'), cubic=sim.get('Cubic'))
sim3.view_super_crystal()

