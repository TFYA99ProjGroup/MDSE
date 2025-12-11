# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.

"""
YAML configuration file parser for MDSE.

This module is responsible for reading and interpreting YAML files that define
molecular dynamics simulations. It provides functionalities to:

1.  Read a base YAML configuration file.
2.  "Un-nest" or expand simulation parameters. If a parameter like temperature
    is defined as a list or a range, this module generates a separate, complete
    simulation configuration for each value.
3.  Handle command-line overwrites for specific configuration values.
4.  Expand file paths, creating multiple simulations if a path points to a directory.

The simulation configuration files have a specific format that need to be followed, the structure looks like

.. code-block:: YAML

    [Name]:
      CRYSTAL:
        TYPE: [DATABASE, FILE or BULK]
        Name: [name of material or sim]
        Supercell: (optional)
          - [x]
          - [y]
          - [z]
        Filepath: [relative path from this file to crystal file or database] (only required for FILE and DATABASE)

        [The following are only required for DATABSE]
        Structure_folder: [path to generated structure files]
        Query:
          [key]: [value]

        [The following are only required for BULK]
        Structure: [fcc, bcc, etc.]
        Lattice_a: [Å]
        Lattice_b: [Å] (optional)
        Lattice_c: [Å] (optional)
        Cubic: [True/False cubic unitcell]

      ENSAMBLE:
        Ensamble: [NVT, NVE, NPT]
        Temp: [temperature in K]
        [required for NVT]
        ThermoTime: [steps between thermostat use]
        [required for NPT]
        Pressure: [eV/Å^3]
        BaroTime: [steps between barostat use]
      SIMULATION:
        Timestep: [timestep in fs]
        Length: [number of timesteps]
        TrajInterval: [frequence of write]
        Calculator: [MACE, LennardJones, EMT]
        CalculatorParams:
            [param]: [value] (see documentation of specific calculator)
        Create_traj: [Whether to create a trajectory file for sim]
      RESULT:
        Properties:
          - [material property or all]
          - [prop]

The Temp, Pressure settings can also have a _list and _range extension which look like

.. code-block:: python

    Temp_list:
      - [K]
      - ...
      .

or

.. code-block:: python

    Temp_range:
      start: [K]
      stop: [K]
      step: [stepsize]

which create multiple simulations for each element in the list or range.

"""

import yaml
import logging
from copy import deepcopy
from pathlib import Path

logger = logging.getLogger(__name__)
# from yaml.loader import SafeLoader

# TODO
# -Error handling if forexample "p_range["Start"]" is missing
# -Make sure the dictionaries are properly copied. Use .deepcopy()
#       instead of .copy()? Since dictionary can contain lists


def read_yaml_simulations(filename):
    """
    Reads a YAML file containing MD simulation configurations and
    returns it as a dictionary.

    Parameters
    ----------
    filename : str or Path
        Path to the configuration YAML file.

    Returns
    -------
    dict
        A dictionary containing the simulation configurations parsed from the
        YAML file.
    """
    logger.debug(f"Reading from {filename}")
    with open(filename, "r") as f:
        simulations_config = yaml.safe_load(f)
        return simulations_config


def unnest_simulation_parameters(all_simulations, overwrite_config={}):
    """
    Expands nested parameters (lists or ranges) in the
    simulation configurations and applies command-line overwrites.

    This function iterates through each simulation defined in the input
    dictionary. For parameters specified as a list (e.g., `Temp_list`) or a
    range (e.g., `Pressure_range`), it generates distinct simulation
    configurations for each value.

    After expansion, it applies any `overwrite_config` values, modifying the
    generated configurations.

    Parameters
    ----------
    all_simulations : dict
        A dictionary of simulation configurations, as read from the YAML file.
    overwrite_config : dict, optional
        A dictionary of parameters to overwrite in the configurations.
        Defaults to an empty dictionary.

    Returns
    -------
    list[dict]
        A list of fully expanded and overwritten simulation configurations.
    """
    logger.debug("Beginning unnesting parameters")
    parameters_to_expand = [
        "Temp",
        "Pressure",
    ]  # Parameters that may be nested as lists or ranges
    final_simulation_configs = []  # Will hold all expanded simulation configs
    for simulation_name, simulation_full_config in all_simulations.items():
        logger.debug(f"Unnesting {simulation_name}")
        # Start with the original simulation as a tuple (name, config)
        current_simulations = [(simulation_name, simulation_full_config)]
        # For each parameter, expand all current
        # simulations if the parameter is a list or range
        for parameter in parameters_to_expand:
            logger.debug(f"Getting parameter {parameter}")
            expanded_simulations = []
            for simulation in current_simulations:
                expanded_simulations.extend(
                    expand_parameter(simulation, parameter, overwrite_config)
                )
            # Update current simulations to the newly expanded list
            # for the next parameter
            current_simulations = expanded_simulations
        # Convert each tuple (name, config) back to a dictionary for output
        final_simulation_configs.extend(
            {name: conf} for name, conf in current_simulations
        )
    logger.debug("Unnesting done")
    logger.debug(final_simulation_configs)

    if overwrite_config:
        all_categories = {
            "CRYSTAL": ["TYPE", "Name", "Filepath", "Structure_folder", "Query"],
            "ENSAMBLE": ["Ensamble", "Temp", "ThermoTime"],
            "SIMULATION": [
                "Timestep",
                "Length",
                "TrajInterval",
                "Calculator",
                "CalculatorParams",
                "Create_traj",
            ],
            "RESULT": ["Properties"],
        }
        for simulation in final_simulation_configs:
            for category in all_categories.keys():
                for key in all_categories[category]:
                    if key in overwrite_config.keys():
                        logger.debug(simulation)
                        first_value = next(iter(simulation.values()))
                        if (
                            type(overwrite_config[key]) is dict
                            and type(first_value[category][key]) is dict
                        ):
                            try:
                                if (
                                    first_value["SIMULATION"]["Calculator"]
                                    == "LennardJones"
                                ):
                                    new_config = nest_lennard_jones(
                                        first_value[category][key],
                                        overwrite_config[key],
                                    )
                                    if new_config:
                                        first_value[category][key] = new_config
                                    continue
                            except Exception:
                                pass
                            for nested_key in first_value[category][key].keys():
                                logger.debug(f"nestedkey {nested_key}")
                                logger.debug(f"{overwrite_config[key]}")
                                if nested_key in overwrite_config[key].keys():
                                    first_value[category][key][nested_key] = (
                                        overwrite_config[key][nested_key]
                                    )

                        else:
                            first_value[category][key] = overwrite_config[key]
        logger.debug(f"overwrite config: {overwrite_config}")
        logger.debug(
            f"config has been overwritten. Now the config is {final_simulation_configs}"
        )

    return final_simulation_configs


def nest_lennard_jones(og_config, overwrite_config):
    """Special handler to overwrite nested Lennard-Jones parameters.

    The LennardJones calculator can have parameters like `epsilon` and `sigma`
    defined as nested lists (matrices). This function correctly applies
    overwrites to specific elements within these nested structures.

    Examples
    --------
    To overwrite the first row of the ``epsilon`` matrix for a Lennard-Jones
    potential, you can target a specific index in the ``CalculatorParams``.

    **Command:**

    .. code-block:: bash

        mdse simulate ... -c CalculatorParams.epsilon.0=0.3

    **Effect on Configuration:**

    This command transforms the ``CalculatorParams`` from:

    .. code-block:: json

        {
            "elements": [0],
            "epsilon": [[0.226738]],
            "sigma": [[0.70641]],
            "rCut": [[1.3]]
        }

    to:

    .. code-block:: json

        {
            "elements": [0],
            "epsilon": [[0.3]],
            "sigma": [[0.70641]],
            "rCut": [[1.3]]
        }

    Parameters
    ----------
    og_config : dict
        The original Lennard-Jones parameter dictionary from the simulation
        configuration.
    overwrite_config : dict
        The overwrite values for the Lennard-Jones parameters, typically
        parsed from the command line.

    Returns
    -------
    dict
        The updated Lennard-Jones parameter dictionary.

    Notes
    -----
    This function modifies a copy of the original config and returns it.
    """
    logger.debug("in nest_lennard_jones!")
    new_config = {}
    try:
        for key in og_config.keys():
            new_config[key] = og_config[key]
            if key in overwrite_config.keys():
                logger.debug(overwrite_config[key])
                for index in overwrite_config[key].keys():
                    if (
                        type(overwrite_config[key][index]) is not list
                        and key != "elements"
                    ):
                        overwrite_config[key][index] = [overwrite_config[key][index]]
                    new_config[key][int(index)] = overwrite_config[key][index]

    except Exception as e:
        logger.error(
            "You wrote the overwrite wrong! Please try again, "
            + f"or consider to use something other than Lennard Jones {e}"
        )


def expand_parameter(simulation_to_expand, parameter, overwrite_config={}):
    """
    Expands a simulation based on a single parameter specified as a list or range.

    If the specified `parameter` is found in the simulation configuration as a
    list (e.g., `Temp_list`) or a range (e.g., `Temp_range`), this function
    generates a new simulation configuration for each value. If the parameter
    is a single value or not present, it returns the original simulation.

    Parameters
    ----------
    simulation_to_expand : tuple[str, dict]
        A tuple containing the simulation name and its configuration dictionary.
    parameter : str
        The base name of the parameter to expand (e.g., 'Temp', 'Pressure').
    overwrite_config : dict, optional
        A dictionary of command-line overwrites that may apply to the list or
        range itself. Defaults to an empty dictionary.

    Returns
    -------
    list[tuple[str, dict]]
        A list of expanded simulations, each as a (name, config) tuple.
    """
    result = []
    sim_name, sim_params = simulation_to_expand

    param_list = parameter + "_list"  # e.g., 'Temp_list'
    param_range = parameter + "_range"  # e.g., 'Temp_range'
    ensamble_params = sim_params.get("ENSAMBLE")
    # If parameter exists as a single value, leave as is
    if ensamble_params.get(parameter):
        logger.debug(f"Parameter {parameter} was a single value")
        return [(sim_name, sim_params)]

    # If parameter is a list, expand for each value
    values_as_list = ensamble_params.get(param_list)
    if values_as_list:
        logger.debug(f"Parameter {parameter} was a list, extracting...")
        logger.debug(param_list)
        logger.debug(overwrite_config.keys())
        if param_list in overwrite_config.keys():
            logger.debug(
                f"overwriting {values_as_list} with {overwrite_config[param_list]}"
            )
            values_as_list = overwrite_config[param_list]
        for value in values_as_list:
            # Shallow copy, might need more for nested structures
            new_params = deepcopy(sim_params)
            logger.debug(sim_params)
            new_params.get("ENSAMBLE").pop(param_list)
            logger.debug(sim_params)
            new_params.get("ENSAMBLE")[parameter] = value
            result.append((f"{sim_name}_{parameter}_{value}", new_params))
        return result

    # If parameter is a range, expand for each value in the range
    logger.debug(sim_params)
    values_as_range = ensamble_params.get(param_range)
    if values_as_range:
        logger.debug(f"Parameter {parameter} was a range, iterating...")
        if param_range in overwrite_config.keys():
            logger.debug(f"Before overwrite{values_as_range}")
            for key in values_as_range.keys():
                if key in overwrite_config[param_range].keys():
                    values_as_range[key] = overwrite_config[param_range][key]
            logger.debug(f"After overwrite{values_as_range}")

        for value in range(
            values_as_range["Start"],
            values_as_range["Stop"],
            values_as_range["Step"],
        ):
            new_params = deepcopy(sim_params)
            new_params.get("ENSAMBLE").pop(param_range)
            new_params.get("ENSAMBLE")[parameter] = value
            result.append((f"{sim_name}_{parameter}_{value}", new_params))
        return result

    # If parameter is not present, leave as is
    return [(sim_name, sim_params)]


def main_read(filename, overwrite_config={}):
    """
    Reads from a YAML file, then un-nests the MD simulations by
    expanding any parameters specified as lists or ranges.

    This is the main entry point for parsing. It orchestrates reading the YAML
    file, expanding parameter lists/ranges, applying overwrites, and finally
    expanding directory paths into individual file paths.

    Parameters
    ----------
    filename : str or Path
        Path to the main YAML configuration file.
    overwrite_config : dict, optional
        A dictionary of parameters to overwrite. Defaults to an empty dict.

    Returns
    -------
    list[dict]
        A final list of fully specified, individual simulation configurations.
    """
    all_simulations = read_yaml_simulations(filename)
    logger.debug(f"Read from {filename} done!")
    logger.debug("Format OK")
    return get_files(
        unnest_simulation_parameters(all_simulations, overwrite_config), filename
    )


def get_files(simulations, config_file_path):
    """
    Expand simulations where the crystal source is a directory.

    If a simulation's `CRYSTAL.Filepath` points to a directory, this function
    creates a new, separate simulation configuration for each file found
    within that directory. If the path is a single file or not a file-based
    crystal source, the simulation is passed through unchanged.

    Parameters
    ----------
    simulations : list[dict]
        A list of simulation configurations (potentially with directory paths).
    config_file_path : str or Path
        The path to the original YAML config file, used to resolve relative
        directory paths.

    Returns
    -------
    list[dict]
        An expanded list of simulation configurations where all directory
        paths have been resolved to individual files.
    """
    expanded_parameters = []
    config_dir = Path(config_file_path).parent
    for sim in simulations:
        ((name, val),) = sim.items()
        crystal_params = val.get("CRYSTAL")

        if crystal_params.get("Filepath") is None:
            logger.debug("Specified crystal input is not")
            expanded_parameters.append(sim)
            continue

        dir_path = (config_dir / crystal_params.get("Filepath")).resolve()
        if crystal_params.get("TYPE") == "DATABASE":
            logger.debug("CRYSTAL input is path to database")
            crystal_params["Filepath"] = str(dir_path)
            expanded_parameters.append(sim)
            continue

        if not dir_path.is_dir():
            logger.debug("CRYSTAL input is direct path to config file")
            expanded_parameters.append(sim)
            continue

        logger.debug("CRYSTAL input is path to folder")
        logger.debug(f"Searching folder at: {str(dir_path)}")
        for file_path in map(str, dir_path.iterdir()):
            if not Path(file_path).is_file():
                continue
            logger.debug(f"Config file found: {file_path}")
            new_sim = deepcopy(sim)
            new_sim[name]["CRYSTAL"]["Filepath"] = file_path
            expanded_parameters.append(new_sim)

    return expanded_parameters
