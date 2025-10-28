"""
Runs a single simulation of fcc copper at 800 K.
Also views the crystal structure of the simulation object.
"""

from mdse.md.simulationmanager import SimulationManager

config = {
    "Type": "Cu",
    "Structure": "fcc",
    "Lattice_a": 3.6,
    "Cubic": True,
    "Temp": 800,
    "Timestep": 2,
    "Length": 400,
    "TrajInterval": 10,
}

simulation = SimulationManager(config=config)
simulation.simulate_nve()
simulation.view_super_crystal()
