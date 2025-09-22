import yaml
from yaml.loader import SafeLoader

#TODO
#-Error handling if forexample "p_range["Start"]" is missing
#-Make sure the dictionaries are properly copied. Use .deepcopy() instead of .copy()? Since dictionary can contain lists


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
    
def unnest_temp(MD_obj, p = "Temp"):
    """Takes a dictionary for a MD simulation. Check if any parameter is nested, an un-nests it.
    Can be nested as a list or range
    
    Args:
        MD_obj (dictionary): The dictionary representing an simulation
        p (str): The parameter to un-nest

    Returns:
        List of MD objects un-nessted.
    """
    un_nest = []

    #Extract the dictionary containing all information
    name_of_MD_temp = list(MD_obj.keys())
    name_of_MD = name_of_MD_temp[0]
    dic_org_temp = list(MD_obj.values())
    dic_org = dic_org_temp[0]

    #Variables used
    p_list = p + "_list"
    p_range = p + "_range"

    #If p exists, leave
    if (dic_org.get(p)):
        return [{name_of_MD:dic_org}]

    #If p is a list
    Temp_list = dic_org.get(p_list)
    if (Temp_list):
        i = 0
        for temps in Temp_list: #Loop over list
            new_dic = dic_org.copy()
            new_dic.pop(p_list)
            new_dic[p] = temps
            un_nest.append({name_of_MD + "_" +str(i) :new_dic})
            i = i +1

        return un_nest
    
    #If p is a range
    Temp_range = dic_org.get(p_range)
    if (Temp_range):
        i = 0
        for index in range(Temp_range["Start"],Temp_range["Stop"],Temp_range["Step"]):
            new_dic = dic_org.copy()
            new_dic.pop(p_range)
            new_dic[p] = index
            un_nest.append({name_of_MD + "_" + str(i):new_dic})
            i = i + 1
        return un_nest

    #If no p is mentioned, leave it as is
    return [{name_of_MD:dic_org}]

def main_read(filename):
    """The main read functions.
    Reads from .yaml file, then un-nestes the MD simulations.

    Args:
        filename (str): Name of the .yaml config file
    
    Returns:
        List where each element is a MD simulation, as a dictionary.
    """
    nested_MD = read_file(filename)

    #Un-nest temperature
    un_nested_MD_1 = []
    for MDs in nested_MD:
        un_nested_MD_1 = un_nested_MD_1 + unnest_temp(MDs,"Temp")

    #Un-nest type
    un_nested_MD_2 = []
    for MDs in un_nested_MD_1:
        un_nested_MD_2 = un_nested_MD_2 + unnest_temp(MDs,"Type")


    return un_nested_MD_2


##-----Test------

test = main_read("test_file.yaml")
for finals in test:
    print(finals)