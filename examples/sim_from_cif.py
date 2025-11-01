"""
This example loads a crystal from a cif file.
"""
from mdse.md.simulationmanager import SimulationManager
from mdse.parser.parse_yml import main_read

simulations = main_read("crystal_from_cif.yaml")

config = list(simulations[0].values())[0]

sim1 = SimulationManager(config)

sim1.view_super_crystal()
