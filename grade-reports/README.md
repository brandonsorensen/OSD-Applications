# Merge Grade Reports

This README contains step-by-step instruction for running the _merge_files.py_ Python script contained in this directory.

### Installing Python

The following section covers the installation of the Python language interpreter, which is necessary for running Python scripts. Python is one of the most widely used programming languages in the world and even comes pre-installed on some operating systems, such as macOS and most Linux distrobutions. So long as you follow the instructions closely, there is no risk of installing anything malicious on your machine.

If you already have Python, you can skip to the [Installing Dependencies](#installing-dependencies) section.

#### Windows

Python does not come preinstalled on Windows. Use the following instructions to install it:

1. You can download Python at its [website](https://www.python.org/downloads/). There will be multiple versions available. It does not matter which one you choose so long as it is version 3.0 or greater. Do not download 2.7.

2. In the installer, ensure that you check "Add Python to PATH".

   ![Python installer](/Users/Brandon/Library/Mobile Documents/com~apple~CloudDocs/osd-job/scripts/images/python-installer.png)

3. You may wish to uncheck "Install launcher for all users" if yours is a shared computer.

4. Restart your computer.

5. When your computer is rebooted, open the command prompt by clicking the Start button and typing "cmd". It should appear in the search results.

6. In the command prompt, type:

   `python -V`

   Press _Enter_.

   Note: you can paste text into the command prompt by right clicking anywhere in the black space. It is a good idea to copy and paste all the commands in this document so as to avoid typos.

   The version number of your Python installation should print. For example, for the most recent version of Python as of the time of this writing, you would see: `Python 3.9.0`.

   If anything else happens, something went wrong. Concact Brandon or Terri.

#### macOS

Python comes pre-installed on macOS. It is accessed through the Terminal.app application, which is located in the "Utilities" sub-folder in the "Applications" folder. You can find it quickly by pressing Command ⌘ and the space bar at the same time to bring up Spotlight. Here type "terminal", and you will see it among the results.

![spotlight search](/Users/Brandon/Library/Mobile Documents/com~apple~CloudDocs/osd-job/scripts/images/spotlight.png)

Type `python -V` to print the version number.

### Installing Dependencies

On top of Python, we need two extra tools to help us work with the data:

- pandas is a library for working with the kind of tabular data found in CSV and Excel files
- The xlrd package is necessary for reading in Excel files.

We can install these packages with the following command:

`python -m pip install --user pandas xlrd`

If you are not sure if you have already installed these dependencies, there is no harm in running the above command again. It will install any you do have and ignore the rest.

## Running the Script

### Required Files

The script expects files from four sources: 

| Source    | File Type  |          Default Path |
| :-------- | :--------: | --------------------: |
| Apex      |    CSV     |      reports/apex.csv |
| Schoology |    CSV     | reports/schoology.csv |
| IDLA      |    CSV     |      reports/idla.csv |
| BYU       | Excel/XLSX |      reports/byu.xlsx |

The above table is organized into three columns: the real-world source that the file is referencing, i.e. the origin of the data, the file type, and the default path. This path is relative to the directory of this README file and the Python script.

It is important to remember that the script _will not work_ if the files are not in the format specified above.

### Run

The simplest way to run the script is to create a folder called "reports" in the same folder as the script, then  put the requisite files in that folder.

### Advanced Usage

The more involved method entails specifying exactly where these four files are located.

```
usage: merge_files.py [-h] [-b BYU] [-a APEX] [-i IDLA] [-s SCHOOLOGY]
                      [-p PS_STUDENTS] [-o OUTPUT_PATH] [-f] [-q]

Merge grade reports into one file.

optional arguments:
  -h, --help            show this help message and exit
  -b BYU, --byu BYU     path to the BYU file (default: reports/byu.xlsx)
  -a APEX, --apex APEX  path to the Apex file (default: reports/apex.csv)
  -i IDLA, --idla IDLA  path to the IDLA file (default: reports/idla.csv)
  -s SCHOOLOGY, --schoology SCHOOLOGY
                        path to the Schoology file (default:
                        reports/schoology.csv)
  -p PS_STUDENTS, --ps-students PS_STUDENTS
                        path to the PowerSchool students file (default:
                        reports/student-schools.csv)
  -o OUTPUT_PATH, --output-path OUTPUT_PATH
                        path to the PowerSchool students file (default:
                        current working directory)
  -f, --keep-future     exclude classes that start in the future
  -q, --silence-output  silence/quiet any console output

```



