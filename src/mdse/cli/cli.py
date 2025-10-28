"""
Functions for parsing MDSE configuration files.
"""

import argparse
import subprocess
import glob
import os
import logging

from mdse.parser.parse_yml import main_read
from mdse.rm.runmanager import RunManager
from mdse.logging.logging_config import setup_logging
from mdse.md.resultMD import ResultMD


logger = logging.getLogger(__name__)


def view_crystal(args):
    """
    Open one or more crystal structure files in the ASE GUI.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:
        - filepath (list[str] or None): Paths to files to view.
          If None, opens all `.traj` files in the current directory.

    Notes
    -----
    Uses the `ase gui` command under the hood.
    """

    if args.filepath:
        logger.info("Viewing crystal from %s", args.filepath)
        subprocess.run(["ase", "gui"] + args.filepath)
    else:
        logger.info("Viewing crystal all crystals in current directory")
        subprocess.run("ase gui *.traj", shell=True)


def remove_all_traj(args):
    """
    Remove all `.traj` files from a specified directory.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:
        - filepath (str or None): Directory path where `.traj` files
          will be removed. If None, defaults to the current directory.
        - recursive (bool): If True, also search subdirectories.

    Side Effects
    ------------
    Deletes files from disk and prints status messages for each file.
    """

    if args.filepath:
        filepath = args.filepath
    else:
        filepath = "."

    if not os.path.exists(filepath):
        logger.warning(f"Path does not exist: {filepath}")
        files = []
    else:
        if args.recursive:
            # Recursively search subdirectories
            files = glob.glob(os.path.join(
                filepath, "**", "*.traj"), recursive=True)
        else:
            # Only in the specified directory
            files = glob.glob(os.path.join(filepath, "*.traj"))

    for file in files:
        try:
            os.remove(file)
            logger.debug(f"Removed: {file}")
        except OSError as e:
            logger.warning(f"Could not remove {file}: {e}")
    logger.info(f"Removed {len(files)} files")


def simulate(args):
    """
    Run molecular dynamics simulations defined in a YAML configuration.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:
        - filepath (str): Path to a YAML file describing simulation parameters.

    Notes
    -----
    Parses the input YAML using `main_read`, creates a `RunManager`,
    and executes all simulations sequentially.
    """

    sim_list = main_read(args.filepath)
    logger.info(f"Starting {len(sim_list)} simulations")

    rm = RunManager(sim_list)
    if args.ensamble.lower() == "nvt":
        rm.run_nvt_simulations()
    elif args.ensamble.lower() == "nve":
        rm.run_nve_simulations()
    elif args.ensamble.lower() == "npt":
        rm.run_npt_simulations()
    else:
        logger.info("Use one of following ensambles: NVT, NVE or NPT")
        return
    logger.info("Simulation done!")


def calc_msd(args):
    paths = args.filepath
    for path in paths:
        logger.debug(f"Running msd calculation from {path}")
        result = ResultMD.from_file(path)
        result.visualize_msd()


def calc_lindemann(args):
    paths = args.filepath
    for path in paths:
        logger.debug(f"Running lindemann calculation from {path}")
        result = ResultMD.from_file(path)
        logger.info(f"Lindemann calc from {path}: {result.calc_lindemann()}")


def calc_self_diff(args):
    paths = args.filepath
    for path in paths:
        logger.debug(f"Running self_diff calculation from {path}")
        result = ResultMD.from_file(path)
        logger.info(
            f"Self diffusion coefficient calculation from {path}:" +
            f"{result.calc_self_diff()}"
        )


def calc_isobaric_specific_heat(args):
    paths = args.filepath
    for path in paths:
        logger.debug(f"Running isobaric_specific_heat calculation from {path}")
        result = ResultMD.from_file(path)
        logger.info(
            f"Isobaric specific heat per atom calculation from {path}:" +
            f"{result.calc_isochoric_heat_capacity_per_atom()}"
        )


def main():
    """
    Entry point for the MDSE CLI.

    Provides the following subcommands:

    - `simulate`: Run simulations defined in a YAML file.
        Usage: `mdse simulate -f config.yml`
    - `view`: Open structure files with the ASE GUI.
        Usage: `mdse view -f file1.traj file2.traj`
    - `clean`: Remove all `.traj` files in a directory.
        Usage: `mdse clean -f ./results`

    Notes
    -----
    The selected subcommand is dispatched to the corresponding function
    via `argparse`'s `set_defaults(func=...)`.
    """

    # ----------Setup----------
    parser = argparse.ArgumentParser(description="MDSE")

    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")

    subparsers = parser.add_subparsers(title="subcommands", dest="command")
    # ----------Subparsers----------

    parser_simulate = subparsers.add_parser("simulate", help="simulate once")
    parser_simulate.add_argument(
        "-f",
        "--filepath",
        required=True,
        metavar="FILEPATH",
        help="The filepath to be simulated",
    )
    parser_simulate.add_argument(
        "-e",
        "--ensamble",
        required=True,
        metavar="FILEPATH",
        help="Which ensamble to be used: NVT, NVE or NPT",
    )
    parser_simulate.set_defaults(func=simulate)

    parser_view_crystal = subparsers.add_parser("view", help="view a crystal")
    parser_view_crystal.add_argument(
        "-f",
        "--filepath",
        nargs="+",
        metavar="FILEPATH",
        help="The filepath to be viewed",
    )
    parser_view_crystal.set_defaults(func=view_crystal)

    parser_remove_traj = subparsers.add_parser(
        "clean", help="Remove all traj files in a directory"
    )
    parser_remove_traj.add_argument(
        "-f",
        "--filepath",
        metavar="FILEPATH",
        help="The filepath to directory where traj files should be removed.",
    )
    parser_remove_traj.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Remove .traj files recursively in all subdirectories.",
    )

    parser_remove_traj.set_defaults(func=remove_all_traj)

    parser_calc_msd = subparsers.add_parser(
        "msd", help="Calculate msd from traj-file")
    parser_calc_msd.add_argument(
        "-f",
        "--filepath",
        nargs="+",
        metavar="FILEPATH",
        help="The filepath to be calculated",
    )
    parser_calc_msd.set_defaults(func=calc_msd)

    parser_calc_lindemann = subparsers.add_parser(
        "lindemann", help="Calculate lindemann from traj-file"
    )
    parser_calc_lindemann.add_argument(
        "-f",
        "--filepath",
        nargs="+",
        metavar="FILEPATH",
        help="The filepath to be calculated",
    )
    parser_calc_lindemann.set_defaults(func=calc_lindemann)

    parser_calc_self_diff = subparsers.add_parser(
        "self_diff", help="Calculate self diffusion coefficient from traj-file"
    )
    parser_calc_self_diff.add_argument(
        "-f",
        "--filepath",
        nargs="+",
        metavar="FILEPATH",
        help="The filepath to be calculated",
    )
    parser_calc_self_diff.set_defaults(func=calc_self_diff)

    parser_calc_isobaric_specific_heat = subparsers.add_parser(
        "ish", help="Calculate isobaric specific heat per atom from traj-file"
    )
    parser_calc_isobaric_specific_heat.add_argument(
        "-f",
        "--filepath",
        nargs="+",
        metavar="FILEPATH",
        help="The filepath to be calculated",
    )
    parser_calc_isobaric_specific_heat.set_defaults(
        func=calc_isobaric_specific_heat)

    # ----------Other----------
    args = parser.parse_args()

    setup_logging(debug=args.debug)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
