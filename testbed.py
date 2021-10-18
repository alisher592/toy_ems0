import os
class files:
    with open(os.getcwd()+"\\parameters.txt") as f:
        param_file = f.readlines()
        param_file = [x.strip() for x in param_file] 

print(files.param_file[0])

#open(os.getcwd()+"\\parameters.txt", 'r')


    