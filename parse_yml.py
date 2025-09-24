import yaml
from yaml.loader import SafeLoader

#TODO
#-Error handling if forexample "p_range["Start"]" is missing
#-Make sure the dictionaries are properly copied. Use .deepcopy() instead of .copy()? Since dictionary can contain lists


def read_yaml_simulations(filename):
    """Read yaml file.

    Args:
        filename (str): Name of the config yaml file

    Returns:
        A list. Each element is a dictionary, containing information on a MD simulation.
    """
    with open(filename, "r") as f:
        simulations_config = yaml.safe_load(f)
        return simulations_config
    
def unnest_simulation_parameters(all_simulations):
    """
    Expands nested parameters (lists or ranges) in the simulations_config dictionary for each simulation.
    Returns a list of fully un-nested simulation dictionaries.
    """
    parameters_to_expand = ["Temp", "Type", "Time"]
    final_simulations = []
    for sim_name, sim_params in all_simulations.items():
        current_simulations = [(sim_name, sim_params)]
        for parameter in parameters_to_expand:
            expanded_simulations = []
            for sim_pair in current_simulations:
                expanded_simulations.extend(expand_parameter(sim_pair, parameter))
            current_simulations = expanded_simulations
        final_simulations.extend({name: conf} for name, conf in current_simulations)
    return final_simulations

def expand_parameter(sim_pair, parameter):
    result = []
    sim_name, sim_params = sim_pair

    param_list = parameter + "_list"
    param_range = parameter + "_range"

    # If parameter exists, leave as is
    if sim_params.get(parameter):
        return [(sim_name, sim_params)]

    # If parameter is a list
    values_as_list = sim_params.get(param_list)
    if values_as_list:
        for i, value in enumerate(values_as_list):
            new_params = sim_params.copy()
            new_params.pop(param_list)
            new_params[parameter] = value
            result.append((f"{sim_name}_{i}", new_params))
        return result

    # If parameter is a range
    values_as_range = sim_params.get(param_range)
    if values_as_range:
        for i, index in enumerate(range(values_as_range["Start"], values_as_range["Stop"], values_as_range["Step"])):
            new_params = sim_params.copy()
            new_params.pop(param_range)
            new_params[parameter] = index
            result.append((f"{sim_name}_{i}", new_params))
        return result

    # If no parameter is mentioned, leave as is
    return [(sim_name, sim_params)]

def main_read(filename):
    """
    Reads from .yaml file, then un-nests the MD simulations.
    Returns a list where each element is a MD simulation, as a dictionary.
    """
    all_simulations = read_yaml_simulations(filename)
    return unnest_simulation_parameters(all_simulations)


##-----Test------

test = main_read("test_file.yaml")
for sim in test:
    print(sim)