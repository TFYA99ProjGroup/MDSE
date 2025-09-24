import yaml
from yaml.loader import SafeLoader

#TODO
#-Error handling if forexample "p_range["Start"]" is missing
#-Make sure the dictionaries are properly copied. Use .deepcopy() instead of .copy()? Since dictionary can contain lists


def read_yaml_simulations(filename):
    """
    Reads a YAML file containing MD simulation configurations and returns it as a dictionary.

    Args:
        filename (str): Name of the config YAML file.

    Returns:
        dict: Dictionary where each key is a simulation name and each value is its parameter dictionary.
    """
    with open(filename, "r") as f:
        simulations_config = yaml.safe_load(f)
        return simulations_config
    
def unnest_simulation_parameters(all_simulations):
    """
    Expands nested parameters (lists or ranges) in the simulations_config dictionary for each simulation.
    For each simulation, if a parameter is specified as a list or a range, it creates multiple simulation configs,
    one for each value in the list or range. This is repeated for all parameters in parameters_to_expand.

    Args:
        all_simulations (dict): Dictionary of all simulations from the YAML file.

    Returns:
        list: List of dictionaries, each representing a fully un-nested simulation configuration.
    """
    parameters_to_expand = ["Temp", "Type", "Time"]  # Parameters that may be nested as lists or ranges
    final_simulation_configs = []  # Will hold all expanded simulation configs
    for simulation_name, simulation_full_config in all_simulations.items():
        # Start with the original simulation as a tuple (name, config)
        current_simulations = [(simulation_name, simulation_full_config)]
        # For each parameter, expand all current simulations if the parameter is a list or range
        for parameter in parameters_to_expand:
            expanded_simulations = []
            for simulation in current_simulations:
                expanded_simulations.extend(expand_parameter(simulation, parameter))
            # Update current simulations to the newly expanded list for the next parameter
            current_simulations = expanded_simulations
        # Convert each tuple (name, config) back to a dictionary for output
        final_simulation_configs.extend({name: conf} for name, conf in current_simulations)
    return final_simulation_configs

def expand_parameter(simulation_to_expand, parameter):
    """
    Expands a single parameter for a given simulation if it is specified as a list or a range.
    If the parameter is a list, creates a new simulation for each value in the list.
    If the parameter is a range, creates a new simulation for each value in the range.
    If the parameter is a single value or not present, returns the simulation unchanged.

    Args:
        simulation_to_expand (tuple): (simulation_name, simulation_config)
        parameter (str): The parameter to expand (e.g., 'Temp', 'Type', 'Time')

    Returns:
        list: List of (simulation_name, simulation_config) tuples, one for each expanded value.
    """
    result = []
    sim_name, sim_params = simulation_to_expand

    param_list = parameter + "_list"   # e.g., 'Temp_list'
    param_range = parameter + "_range" # e.g., 'Temp_range'

    # If parameter exists as a single value, leave as is
    if sim_params.get(parameter):
        return [(sim_name, sim_params)]

    # If parameter is a list, expand for each value
    values_as_list = sim_params.get(param_list)
    if values_as_list:
        for i, value in enumerate(values_as_list):
            new_params = sim_params.copy()  # Shallow copy, might need more for nested structures
            new_params.pop(param_list)
            new_params[parameter] = value
            result.append((f"{sim_name}_{i}", new_params))
        return result

    # If parameter is a range, expand for each value in the range
    values_as_range = sim_params.get(param_range)
    if values_as_range:
        for i, index in enumerate(range(values_as_range["Start"], values_as_range["Stop"], values_as_range["Step"])):
            new_params = sim_params.copy()
            new_params.pop(param_range)
            new_params[parameter] = index
            result.append((f"{sim_name}_{i}", new_params))
        return result

    # If parameter is not present, leave as is
    return [(sim_name, sim_params)]

def main_read(filename):
    """
    Reads from a YAML file, then un-nests the MD simulations by expanding any parameters
    specified as lists or ranges. Returns a list where each element is a fully expanded
    MD simulation configuration as a dictionary.

    Args:
        filename (str): Name of the .yaml config file

    Returns:
        list: List of expanded MD simulation configurations (dicts)
    """
    all_simulations = read_yaml_simulations(filename)
    return unnest_simulation_parameters(all_simulations)


##-----Test------

test = main_read("test_file.yaml")
# Print each expanded simulation configuration
for sim in test:
    print(sim)