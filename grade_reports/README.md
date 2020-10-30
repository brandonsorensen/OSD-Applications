# Merge Grade Reports

This README contains step-by-step instruction for running the _merge_files.py_ Python script contained in this directory.

## Running the Script

### Required Files

The script expects files from four sources: 

| Source    | File Type  |            Default Path |
| :-------- | :--------: | ----------------------: |
| Apex      |    CSV     |      `reports/apex.csv` |
| Schoology |    CSV     | `reports/schoology.csv` |
| IDLA      |    CSV     |      `reports/idla.csv` |
| BYU       | Excel/XLSX |      `reports/byu.xlsx` |

The above table is organized into three columns: the real-world source that the file is referencing, i.e. the origin of the data, the file type, and the default path. This path is relative to the directory of this README file and the Python script.

It is important to remember that the script _will not work_ if the files are not in the format specified above.

### Run

The simplest way to run the script is to create a folder called "reports" in the same folder as the script, then put the requisite files in that folder. They must be named _exactly_ as they are named above, bearing in mind that `reports/` refers to the folder in which they are contained. The script looks for these files down to the letter.

### Advanced Usage

The more involved method entails specifying exactly where these four files are located. You should use this method only if you are comfortable in a command line environment. Running the script with the `-h` flag will produce usage instructions for the API:

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
                        path to which the CSV file will be written (default:
                        current working directory)
  -f, --keep-future     exclude classes that start in the future
  -q, --silence-output  silence/quiet any console output

```


