import argparse
import subprocess
import glob
import os

from mdse.parser.parse_yml import main_read
from mdse.md.simulateMD import SimulateMD
from mdse.rm.runmanager import RunManager


def view_crystal(args):
    if args.filepath:
        print(args.filepath)
        subprocess.run(["ase", "gui"] + args.filepath)
    else:
        subprocess.run("ase gui *.traj", shell=True)


def remove_all_traj(args):
    if args.filepath:
        filepath = args.filepath
    else:
        filepath = "."
    files = glob.glob(os.path.join(filepath, "*.traj"))
    for file in files:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except OSError as e:
            print(f"Could not remove {file}: {e}")


def simulate(args):
    sim_list = main_read(args.filepath)
    rm = RunManager(sim_list)
    rm.run_simulations()


def main():
    parser = argparse.ArgumentParser(description="MDSE - ")

    subparsers = parser.add_subparsers(title="subcommands", dest="command")

    parser_simulate = subparsers.add_parser("simulate", help="simulate once")
    parser_simulate.add_argument(
        "--filepath", required=True, help="The filepath to be simulated")
    parser_simulate.set_defaults(func=simulate)

    parser_view_crystal = subparsers.add_parser("view", help="view a crystal")
    parser_view_crystal.add_argument(
        "--filepath", nargs="+", help="The filepath to be viewed")
    parser_view_crystal.set_defaults(func=view_crystal)

    parser_remove_traj = subparsers.add_parser(
        "clean", help="Remove all traj files in a directory")
    parser_remove_traj.add_argument(
        "--filepath", help="The filepath to directory where traj files should be removed.")
    parser_remove_traj.set_defaults(func=remove_all_traj)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
