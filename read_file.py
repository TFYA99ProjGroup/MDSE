class Read_MD_Error(Exception):
    def __init__(self, msg):
        super().__init__(msg)


def get_one_MD(file):
    """Reads from '#' to '#', and places everything inbetween in a dictionary/map.
       Data inbetween should be as 'Key:value'.

       Error if first line is not '#'. Then reads lines until reaches '#'
       
    Args:
        file (str): Name of the input-file

    Returns:
        Dictionary: Data as key:value. Empty if file is EOF
        
    
    
    """
    line = file.readline()
    if (line != '#\n' and line != '#'):
        #Bad format or empty file
        if (line == ""): #Empty 
            return {}
        raise Read_MD_Error("Input-file ill-formated")

    line = file.readline()
    line = line.replace("\n","")
    temp_dic = {}

    while(line != '#'):
        if ":" in line:
            key, value = line.split(":",1) #OBS error if doesnt contain :
        else:
            raise Read_MD_Error("Data not in key:value format")
        temp_dic[key] = value
        line = file.readline()
        line = line.replace("\n","")
    return temp_dic

def get_all_MD(filename):
    """Loop a file, calls get_one_MD until file is empty.
       Creates dictionary for each '#data#' and place in list

    Args:
        filename (str): Name to input-file

    Returns:
        list: The whole input-file formated as dictionaries in a list
    
    
    """
    file = open(filename,"r")

    All_MD = []
    
    one_MD = get_one_MD(file)

    while( one_MD): #False if empty list
        All_MD.append(one_MD.copy())
        one_MD = get_one_MD(file)

    file.close()
    return All_MD
