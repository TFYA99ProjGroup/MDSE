from read_file import get_all_MD

test_data = get_all_MD("text_test.txt")

for data in test_data:
    print('#'*5,data.get("Atom"),'#'*5)
    print("Temperature:",data.get("Temp"))
    print("Timestep:",data.get("Time"))