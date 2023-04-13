# Sunnyside TIE (Simulated Hospital TIE)
Simulated hospital TIE for testing real-time messaging services.

## Run
In the directory containing `app.py` create a file `data/working.csv` with the test patient data you wish to use to test the destination system. This must contain the columns NHS_NUMBER,DOB,FAMILY_NAME,GIVEN_NAME.

Simply run `python app.py` to run in default mode and `python app.py -h` to see a list of command line arguments.