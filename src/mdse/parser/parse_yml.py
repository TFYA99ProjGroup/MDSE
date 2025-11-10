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

    Args:
        filename (str): Name of the config YAML file.

    Returns:
        dict: Dictionary where each key is a simulation name and
        each value is its parameter dictionary.
    """
    logger.debug(f"Reading from {filename}")
    with open(filename, "r") as f:
        simulations_config = yaml.safe_load(f)
        return simulations_config


def unnest_simulation_parameters(all_simulations):
    """
    Expands nested parameters (lists or ranges) in the
    simulations_config dictionary for each simulation.

    For each simulation, if a parameter is specified as a list or
    a range, it creates multiple simulation configs,
    one for each value in the list or range.
    This is repeated for all parameters in parameters_to_expand.

    Args:
        all_simulations (dict): Dictionary of all simulations from the YAML file.

    Returns:
        list: List of dictionaries, each representing
        a fully un-nested simulation configuration.
    """
    logger.debug("Beginning unnesting parameters")
    parameters_to_expand = [
        "Temp",
        "Pressure"
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
                    expand_parameter(simulation, parameter))
            # Update current simulations to the newly expanded list
            # for the next parameter
            current_simulations = expanded_simulations
        # Convert each tuple (name, config) back to a dictionary for output
        final_simulation_configs.extend(
            {name: conf} for name, conf in current_simulations
        )
    logger.debug("Unnesting done")
    return final_simulation_configs


def expand_parameter(simulation_to_expand, parameter):
    """
    Expands a single parameter for a given simulation if
    it is specified as a list or a range.

    If the parameter is a list, creates a new simulation for
    each value in the list.

    If the parameter is a range, creates a new simulation for
    each value in the range.

    If the parameter is a single value or not present,
    returns the simulation unchanged.

    Args:
        simulation_to_expand (tuple): (simulation_name, simulation_config)
        parameter (str): The parameter to expand (e.g., 'Temp', 'Type', 'Time')

    Returns:
        list: List of (simulation_name, simulation_config) tuples,
        one for each expanded value.
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
    values_as_range = sim_params.get(param_range)
    if values_as_range:
        logger.debug(f"Parameter {parameter} was a range, iterating...")
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


def main_read(filename):
    """
    Reads from a YAML file, then un-nests the MD simulations by
    expanding any parameters specified as lists or ranges.

    Returns a list where each element is a fully expanded
    MD simulation configuration as a dictionary.

    Args:
        filename (str): Name of the .yaml config file

    Returns:
        list: List of expanded MD simulation configurations (dicts)
    """
    all_simulations = read_yaml_simulations(filename)
    logger.debug(f"Read from {filename} done!")
    logger.debug("Format OK")
    return get_files(unnest_simulation_parameters(all_simulations))

def get_files(simulations):
    """
    Expand simulations: if CRYSTAL.TYPE == 'FILE' and Filepath is a directory,
    create separate simulations for all files in that folder.

    Currently this does not work recursively, so all the relvant files must be
    in the uppermost level of the specified directory
    """
    expanded_parameters = []
    for sim in simulations:
        (name,val), = sim.items()
        crystal_params = val.get("CRYSTAL")

        if crystal_params.get("TYPE") != "FILE":
            logger.debug("Specified crystal input is not")
            expanded_parameters.append(sim)
            continue

        dir_path  = Path(crystal_params.get("Filepath"))
        if not dir_path.is_dir():
            logger.debug("CRYSTAL input is direct path to config file")
            expanded_parameters.append(sim)
            continue

        logger.debug("CRYSTAL input is path to folder")
        logger.debug(f"Searching folder at: {str(dir_path)}")
        for file_path in map(str,dir_path.iterdir()):
            if not Path(file_path).is_file():
                continue
            logger.debug(f"Config file found: {file_path}")
            new_sim = deepcopy(sim)
            new_sim[name]["CRYSTAL"]["Filepath"] = file_path
            expanded_parameters.append(new_sim)

    return expanded_parameters
