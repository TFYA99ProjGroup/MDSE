"""
Short example script that demonstrates that you can specify a path to a folder in the
config and that the parser will create jobs for each config file in the folder. In
particular this demonstrates that relative paths are correctly handled for .cif
based on the location of the main config file and not where the script is run from.
"""
from mdse.parser.parse_yml import main_read
from pathlib import Path

file_path = Path(__file__).resolve().parent
simulations = main_read((file_path / "../from_folder.yaml").resolve())
# We print the resulting simulations
for sim in simulations:
    print(sim)

print(f"Total number of simulations: {len(simulations)}")
