# extact-matches-to-csv
# extact-sharedmatches-to-csv

Make a comma separated values (CSV) file from the text representation of Ancestry DNA matches
from a web browser.

The first script works on files saved from the account owner's page of matches.
The second works on files from the account owner's pages of shared matches.

- Requires Python 3.6+
- Assumes input names are UTF-8, page text is English.

## Usage ##

From your Ancestry page displaying matches (or shared matches): from the browser use the menu File -> Save As
to save the output as a text file named with extension ".txt".
    Do that with as many next pages as you desire, giving each saved file a unique name ending in ".txt".
    The program reads all ".txt" files in the current directory.

Keep the two types of output separate (owner matches vs shared matches) because they have different formats and  the scripts themseles do not attempt to select which format is being used.

## Installation ##

Copy this Python scripts into the folder containing those text files and run it by clicking on
it (in a windowing environment) or using the command line to change the options. The output
file (if default) will be created in the same folder.

Depending on the Python installation method, it may be necessary to use the command line 
to run the program like this:
``` 
python extract-matches-to-csv.py
dir matches.csv
```

Example of using the command line to change options:
```
extract-matches-to-csv.py --id-with-name --min-cm 18
```

## Options ## 

The two scripts use the same options.

--version

Display the version number then exit.

--out-file FILENAME

Output file, default "matches.csv". This option is used rather than output to stardard-out so
that a file is created without resorting to command line usage. For the shared matches script the default is "shared-matches.csv".

--min-cm CMVALUE

Reject any matches with a cM value smaller than this value. Default is 22.

--skip-header

Do not output a header line. Default: header is included

--skip-id

Exclude the ids for each person as extracted from the URL for match pairs.
The ids help to uniquely identify each person. Default: ids are included.

--id-with-name

Attach a person's id to the person name. Default is to put ids in a separate column.

--skip-relationship

Exclude display of the estimated relationships.

## Examples ##

Account owner's page:
![account owner](examples/account-screenshot.jpg)
