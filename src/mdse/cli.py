# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""
Command-Line Interface (CLI) for the MDSE package.

This module defines the main entry point and command structure for interacting
with the MDSE (Molecular Dynamics Simulation Engine) package from the command
line. It uses Python's `argparse` library to create a powerful and user-friendly
interface with multiple subcommands.

The CLI supports a wide range of functionalities, including:

- **Simulation Management**:

  - `simulate`: Run molecular dynamics simulations from a YAML configuration file,\
    with support for MPI for parallel execution.

- **Data Analysis**:

  - `msd`: Calculate and visualize the Mean Square Displacement.
  - `lindemann`: Calculate the Lindemann index.
  - `self_diff`: Calculate the self-diffusion coefficient.
  - `ish`: Calculate the isobaric specific heat.

- **Database Interaction**:

  - `write_db`: Write simulation results from JSON files to a MongoDB database.
  - `visualize`: Generate plots from data stored in the database.
  - `outliers`: Detect and report outlier data points in the database.

- **Visualization and File Management**:

  - `view`: Open and inspect crystal structure files (`.traj`) using ASE's GUI.
  - `clean`: Remove simulation trajectory files (`.traj`) from a directory.

- **Documentation**:

  - `build_docs`: Build the project's Sphinx documentation locally.
  - `view_docs`: Open the locally built documentation in a web browser.

The `main()` function serves as the primary entry point, which parses command-line
arguments, sets up logging, and dispatches the request to the appropriate
handler function.
"""

import argparse
import subprocess
import glob
import os
import logging
import webbrowser

from mdse.parser import main_read
from mdse.rm.runmanager import RunManager
from mdse.rm.dbmanager import DBManager
from mdse.logging import setup_logging
from mdse.md.resultMD import ResultMD
from mdse.visualizeDB.run_visDB import run_visualize_db
from mdse.utils import defect_formation_energy


logger = logging.getLogger(__name__)


def view_crystal(args):
    """
    Open one or more crystal structure files in the ASE GUI.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - filepath (list[str] | None): Paths to files to view. If None, opens \
        all `.traj` files in the current directory.

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

        - filepath (str | None): Directory path where `.traj` files \
          will be removed. If None, defaults to the current directory.
        - recursive (bool): If True, also search subdirectories.

    Notes
    -----
    Side Effects: \
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
            files = glob.glob(os.path.join(filepath, "**", "*.traj"), recursive=True)
        else:
            # Only in the specified directory
            files = glob.glob(os.path.join(filepath, "*.traj"))

    for file in files:
        try:
            os.remove(file)
            logger.debug(f"Removed: {file}")
        except OSError as e:
            logger.error(f"Could not remove {file}: {e}")
    logger.info(f"Removed {len(files)} files")


def simulate_mpi(args):
    """
    MPI-safe simulation: minimal logging, suitable for running under mpirun.
    Run molecular dynamics simulations defined in a YAML configuration.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - filepath (str): Path to a YAML file describing simulation parameters.
        - config (list[str] | None): Optional 'key=value' pairs to
          overwrite configuration from the YAML file.

    Notes
    -----
    Parses the input YAML using ``main_read()``, creates a ``RunManager``,
    and executes all simulations. This function is intended to be called from
    `simulate()` when the `--mpi` flag is used.
    """

    try:
        import mpi4py.MPI as MPI

        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
    except Exception as e:
        logger.error(f"MPI backend not available: {e}. Exiting.")
        return
    try:
        config_dict = parse_config(args.config)

    except AttributeError:
        config_dict = None

    if config_dict is not None:
        if rank == 0:
            logger.debug(f"Overwriting config with {config_dict}")
    sim_list = main_read(args.filepath, config_dict)

    if rank == 0:
        logger.info(
            f"MPI run: {len(sim_list)} simulations using {comm.Get_size()} ranks."
        )

    rm = RunManager(sim_list)

    rm.run_simulations()

    if rank == 0:
        logger.info("MPI simulations done")


def simulate(args):
    """
    Run molecular dynamics simulations defined in a YAML configuration.

    If the `--mpi` flag is used, this function will dispatch to `simulate_mpi`
    for parallel execution.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - filepath (str): Path to a YAML file describing simulation parameters.
        - mpi (bool): If True, dispatch to the MPI-safe simulation function.
        - config (list[str] | None): Optional 'key=value' pairs to
          overwrite configuration from the YAML file.

    Notes
    -----
    Parses the input YAML using ``main_read()``, creates a ``RunManager``,
    and executes all simulations.
    """
    
    if args.mpi:
        simulate_mpi(args)
        return

    try:
        config_dict = parse_config(args.config)

    except AttributeError:
        config_dict = None

    if config_dict is not None:
        logger.debug(f"Overwriting config with {config_dict}")

    sim_list = main_read(args.filepath, config_dict)
    logger.info(f"Starting {len(sim_list)} simulations")

    rm = RunManager(sim_list)
    rm.run_simulations()
    logger.info("Simulation done!")


def convert_scalar(v):
    """
    Attempt to convert a string to an integer or float.

    Parameters
    ----------
    v : str
        The input string to convert.

    Returns
    -------
    int | float | str
        The converted value as an integer or float if successful,
        otherwise the original string.
    """
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def parse_value(v):
    """
    Parse a string value into a scalar or a list of scalars.

    If the string contains commas, it is split into a list of values.
    Each value is then converted to an int or float if possible.

    Parameters
    ----------
    v : str
        The string value to parse.

    Returns
    -------
    int | float | str | list[int | float | str]
        The parsed value, which can be a single scalar or a list of scalars.
    """
    v = v.strip()
    if "," in v:
        return [convert_scalar(x) for x in v.split(",")]
    return convert_scalar(v)


def insert_nested(d, key_path, value):
    """
    Insert a value into a nested dictionary using a dot-separated key path.

    Creates nested dictionaries as needed.

    Parameters
    ----------
    d : dict
        The dictionary to modify.
    key_path : str
        A dot-separated string representing the nested keys (e.g., "a.b.c").
    value : any
        The value to insert at the specified path.

    Notes
    -----
    This function modifies the input dictionary `d` in place.
    """
    keys = key_path.split(".")
    cur = d
    for k in keys[:-1]:
        if k not in cur:
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


def parse_config(items):
    """
    Parse a list of 'key=value' strings into a nested dictionary.

    Keys can be dot-separated to create nested structures. For example,
    ``["sim.steps=1000", "potential.name=EAM"]`` becomes
    ``{'sim': {'steps': 1000}, 'potential': {'name': 'EAM'}}``.

    Parameters
    ----------
    items : list[str] | None
        A list of strings, each in "key=value" format.

    Returns
    -------
    dict | None
        A nested dictionary representing the configuration, or None if the
        input is None.
    """
    if items is None:
        return None
    result = {}
    for item in items:
        key, val = item.split("=", 1)
        value = parse_value(val)
        insert_nested(result, key, value)
    return result


def calc_msd(args):
    """
    Calculate and visualize the mean square displacement (MSD).

    This function processes one or more trajectory files, calculates the MSD
    for each, and generates a plot.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - filepath (list[str]): Paths to `.traj` files containing simulation
          results.
    """

    paths = args.filepath
    for path in paths:
        logger.debug(f"Running msd calculation from {path}")
        result = ResultMD.from_file(path)
        result.visualize_msd()


def calc_lindemann(args):
    """
    Calculate and print the Lindemann index.

    This function processes one or more trajectory files and prints the
    calculated Lindemann index for each.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - filepath (list[str]): Paths to `.traj` files containing simulation
          results.
    """

    paths = args.filepath
    for path in paths:
        logger.debug(f"Running lindemann calculation from {path}")
        result = ResultMD.from_file(path)
        logger.info(f"Lindemann calc from {path}: {result.calc_lindemann()}")


def calc_self_diff(args):
    """
    Calculate and print the self-diffusion coefficient.

    This function processes one or more trajectory files and prints the
    calculated self-diffusion coefficient for each.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - filepath (list[str]): Paths to `.traj` files containing simulation
          results.
    """

    paths = args.filepath
    for path in paths:
        logger.debug(f"Running self_diff calculation from {path}")
        result = ResultMD.from_file(path)
        logger.info(
            f"Self diffusion coefficient calculation from {path}:"
            + f"{result.calc_self_diff()}"
        )


def calc_isobaric_specific_heat(args):
    """
    Call the isobaric specific heat calculation function.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - filepath (list[str]): Paths to `.traj` files containing simulation
          results.
    """

    paths = args.filepath
    for path in paths:
        logger.debug(f"Running isobaric_specific_heat calculation from {path}")
        result = ResultMD.from_file(path)
        logger.info(
            f"Isobaric specific heat per atom calculation from {path}:"
            + f"{result.calc_isochoric_heat_capacity_per_atom()}"
        )


def build_website_locally(args):
    """
    Build the Sphinx documentation locally.

    This function runs the Sphinx build command to generate HTML documentation
    from the source files located in ``docs/source``. The built site will be
    placed in ``docs/_build/html``.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. This parameter is unused.
    """
    logger.info("Building the documentation locally")
    subprocess.run(
        "sphinx-build -b html docs/source docs/_build/html", shell=True, check=True
    )
    logger.info("Build has been done to docs/_build")


def view_website_browser(args):
    """
    Open the locally built documentation in default web-browser.

    This function launches default web-browser to display the generated HTML
    documentation at ``docs/_build/html/index.html``.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. This parameter is unused.
    """
    logger.info("Viewing the docs with default web-browser")
    webbrowser.open("docs/_build/html/index.html")


def write_to_database(args):
    """
    Write simulation results from JSON files to a MongoDB database.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - address (str): The connection URI for the MongoDB database.
        - filepath (list[str]): A list of paths to JSON files or directories
          containing JSON files to be written to the database.
    """
    writer = DBManager(args.address)
    for path in args.filepath:
        logger.info(f"Writing data from {path} to {args.address}")
        writer.write_jsonfiles_to_db(path)

def calculate_defect_formation_energy(args):
    """
    From an existing database calculate the defect formation energies

    Parameters
    ----------
    args : argparse.address
        Command-line arguments. Should contain:

        - filepath (str): Path to database
    """

    db = DBManager(args.address)
    defect_formation_energy(db)

def visualize_DB(args):
    """
    Generate plots from data in the database using a configuration file.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - filepath (str): Path to a YAML configuration file that specifies
          which data to fetch and how to plot it.
    """
    path = args.filepath

    run_visualize_db(path)


def outlier_detection(args):
    """
    Connect to the database and run outlier detection.

    Fetches data from a specified MongoDB collection, groups it by chemical
    formula, and identifies outliers for given physical properties based on a
    standard deviation threshold.

    Parameters
    ----------
    args : argparse.Namespace
        Command-line arguments. Should contain:

        - address (str): The connection URI for the MongoDB database.
        - properties (list[str] | None): A list of properties to check for
          outliers (e.g., 'energy_per_atom').
        - db_client (str): The name of the MongoDB database.
        - db_collection (str): The name of the collection within the database.
        - std_dev (float): The standard deviation threshold for classifying
          a data point as an outlier.
    """
    logger.debug(f"Connecting to the database at {args.address}")
    try:
        db_manager = DBManager(args.address)
    except Exception as e:
        logger.error(
            f"Failed to connect to MongoDB. "
            f"Ensure it is running. Error: {e}"
        )
        return

    logger.debug(
        f"Running outlier detection with properties: {args.properties}, "
        f"db: {args.db_client}, collection: {args.db_collection}, "
        f"std_dev: {args.std_dev}"
    )
    outliers = db_manager.detect_outliers(
        properties_to_check=args.properties,
        db_client=args.db_client,
        db_collection=args.db_collection,
        std_dev_threshold=args.std_dev,
    )

    if outliers:
        logger.info(f"Found {len(outliers)} outliers.")
        for outlier in outliers:
            logger.info(
                f"Outlier: "
                f"ID: {outlier['id']}, "
                f"Property: {outlier['property']}, "
                f"Value: {outlier['value']}, "
                f"Group mean: {outlier['mean']}, "
                f"Group std_dev: {outlier['std_dev']}"
            )
    else:
        logger.info("No outliers were found with the current settings.")


def create_parser():
    """
    Create and configure the argument parser for the MDSE CLI.

    This function defines all the commands, subcommands, and their respective
    arguments, help messages, and default functions to be executed.

    Returns
    -------
    argparse.ArgumentParser
        The fully configured parser object.
    """
    # ----------Setup----------
    parser = argparse.ArgumentParser(description="MDSE")

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(title="commands", metavar="{subcommand}")
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
        "-c",
        "--config",
        required=False,
        metavar="KEY=VAL",
        nargs="+",
        help=(
            "Overwrite config variables, needs correctly spelled strings."
            + "Eg. 'Name=Ar' to replace the element with Argon."
        ),
    )
    parser_simulate.add_argument(
        "--mpi",
        required=False,
        action="store_true",
        help=(
            "Run in MPI-safe mode: only the master process logs output. "
            "Requires launching with an MPI command, e.g., "
            "mpirun -n 4 mdse simulate [args]."
        ),
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

    parser_calc_msd = subparsers.add_parser("msd", help="Calculate msd from traj-file")
    parser_calc_msd.add_argument(
        "-f",
        "--filepath",
        required=True,
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
        required=True,
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
        required=True,
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
        required=True,
    )
    parser_calc_isobaric_specific_heat.set_defaults(func=calc_isobaric_specific_heat)

    build_website = subparsers.add_parser("build_docs", description="hidden")

    build_website.set_defaults(func=build_website_locally)

    view_website = subparsers.add_parser("view_docs", description="hidden")

    view_website.set_defaults(func=view_website_browser)

    write_to_db = subparsers.add_parser(
        "write_db", help="Write all json-files in a directory to database"
    )
    write_to_db.add_argument(
        "-f",
        "--filepath",
        nargs="+",
        metavar="FILEPATH",
        help="The filepath to be writing from",
        required=True,
    )

    write_to_db.add_argument(
        "-a",
        "--address",
        metavar="ADDRESS",
        help="The address to be writing to",
        required=True,
    )

    write_to_db.set_defaults(func=write_to_database)

    visualize_db = subparsers.add_parser(
        "visualize", help="Visualizes data from database. Uses config file to."
    )

    visualize_db.add_argument(
        "-f",
        "--filepath",
        required=True,
        metavar="FILEPATH",
        help="Filepath to config file, that has info about what data and what plots.",
    )

    visualize_db.set_defaults(func=visualize_DB)

    formation_energy_db = subparsers.add_parser(
        "calc_defect_formation_energy", help="Calculates the defect formation energy " +
                                             "from a database."
    )

    formation_energy_db.add_argument(
        "-a",
        "--address",
        metavar="ADDRESS",
        help="The address of the db, we modify",
        required=True,
    )

    formation_energy_db.set_defaults(func=calculate_defect_formation_energy)

    detect_outliers = subparsers.add_parser(
        "outliers", help="Detects outliers in the database."
    )
    detect_outliers.add_argument(
        "-a",
        "--address",
        metavar="ADDRESS",
        help="The address of the MongoDB database.",
        required=True,
    )
    detect_outliers.add_argument(
        "-p",
        "--properties",
        nargs="+",
        metavar="PROPERTY",
        help="One or more properties to check for outliers. "
        "If not provided, defaults will be used.",
        required=False,
    )
    detect_outliers.add_argument(
        "--db-client",
        metavar="DB_CLIENT",
        help="The name of the MongoDB database to use. Defaults to 'materials_db'.",
        required=False,
        default="materials_db",
    )
    detect_outliers.add_argument(
        "--db-collection",
        metavar="DB_COLLECTION",
        help="The name of the collection to use. Defaults to 'structures'.",
        required=False,
        default="structures",
    )
    detect_outliers.add_argument(
        "--std-dev",
        metavar="STD_DEV_THRESHOLD",
        type=float,
        help="The number of standard deviations for outlier detection. "
        "Defaults to 2.0.",
        required=False,
        default=2.0,
    )
    detect_outliers.set_defaults(func=outlier_detection)

    return parser


def main():
    """Main entry point for the MDSE command-line interface.

    This function orchestrates the CLI by:

    1. Creating the argument parser.
    2. Parsing the command-line arguments provided by the user.
    3. Setting up the logging configuration (e.g., setting the level to DEBUG\
       if `--debug` is specified).
    4. Dispatching the command to the appropriate handler function based on the\
       subcommand provided.
    5. If no subcommand is given, it prints the help message.

    Examples
    --------
    Running a simulation:

    >>> mdse simulate -f config.yml

    Viewing a trajectory file:

    >>> mdse view -f result.traj

    Cleaning up trajectory files:

    >>> mdse clean -f ./results --recursive

    """
    parser = create_parser()

    args = parser.parse_args()

    setup_logging(debug=args.debug)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
