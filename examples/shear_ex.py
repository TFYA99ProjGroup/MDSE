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