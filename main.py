import os

from project import parse_configuration
from project import OperatingSystem

Folder_Path = "/output"
Input_Testcase_Path = '/input_testcases'

def run_each_input_testcase(file_to_run):

    current_directory = os.getcwd() + Input_Testcase_Path
    config_data = parse_configuration(f"{current_directory}/{file_to_run}")

    # # -------------- Actual Run ---------------

    OperatingSystem(
        config_data=config_data,
        file_to_run=file_to_run,
        folder_path=Folder_Path
    )

def main():

    # ********************************************
    # * Choose the testcase we would like to run *
    # ********************************************

    # Run each file in this list # "testcase-addd.txt"
    files_to_run = [
        "testcase-addd.txt"
    ]

    for file in files_to_run:
        run_each_input_testcase(file)

    print("## SUCCESS: All testcases ran successfully\n## NOTE: Check output folder for the result")
    

if __name__ == '__main__':
    main()
