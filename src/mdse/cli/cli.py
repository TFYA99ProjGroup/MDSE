import argparse
import subprocess

from mdse.parser.parse_yml import main_read
from mdse.md.simulateMD import SimulateMD


def simulateone(args):
    sim_list = main_read(args.filepath)
    sim = next(iter(sim_list[0].values()))
    sim3 = SimulateMD(chem_notation=sim['Type'], structure=sim.get(
        'Structure'), a=sim.get('Lattice'), cubic=sim.get('Cubic'),
        temperature=sim.get('Temp'),
        timestep=sim.get('Timestep'), length=sim.get('Length'),
        traj_interval=sim.get('TrajInterval'))
    sim3.simulate_nve()


def view_crystal(args):
    subprocess.run(["ase", "gui", args.filepath])


def main():
    parser = argparse.ArgumentParser(description="MDSE - ")

    subparsers = parser.add_subparsers(title="subcommands", dest="command")

    parser_simulate = subparsers.add_parser("simulate", help="simulate once")
    parser_simulate.add_argument(
        "--filepath", required=True, help="The filepath to be simulated")
    parser_simulate.set_defaults(func=simulateone)

    parser_view_crystal = subparsers.add_parser("view", help="view a crystal")
    parser_view_crystal.add_argument(
        "--filepath", required=True, help="The filepath to be viewed")
    parser_view_crystal.set_defaults(func=view_crystal)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
