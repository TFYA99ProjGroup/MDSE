"""
Short example with running the mace calculator
"""
from mdse.parser.parse_yml import main_read
from mdse.rm.runmanager import RunManager

config = main_read("metal.yaml")

rm = RunManager(config)
for sim in rm.md_simulations:
    sim.simulate()
