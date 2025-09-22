import yaml
from yaml.loader import SafeLoader

def read_file(filename):
    """Read yaml file.

    Args:
        filename (str): Name of the config yaml file

    Returns:
        A list. Each element is a dictionary, containing information on a MD simulation.
    """
    with open(filename,"r") as f:
        data = list(yaml.load_all(f,Loader=SafeLoader))
        return data