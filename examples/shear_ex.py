# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from pathlib import Path

here = Path(__file__).parent
config_path = here / "shear.yaml"
config = main_read(config_path)

rm = RunManager(config)

#rm.md_simulations[0]._attach_shear()

nvt = rm.md_simulations[0].simulate()

G = nvt.calc_shear_modulus()
B = nvt.calc_bulk_modulus()
E = nvt.calc_youngs_modulus()
print(f"G: {G}")
print(f"B: {B}")
print(f"E: {E}")
