import pathlib
from __main__ import aboutThisProgramShort

class messenger(object):

    def __init__(self, name: str):
        self.role = name

    def programInitMesg(self, verbose: bool = False):
        if verbose:
            print(aboutThisProgram)
        else:
            print(aboutThisProgramShort)

    def say(self, message: str):
        print(self.role + ": " + message)

    def saySuccess(self, successMessage: str):
        print("SUCCESS: " + successMessage)

    def sayError(self, errorMessage: str):
        print("ERROR: " + errorMessage)

    def operationReport(self, successNum: int, errorNum: int, errors: dict, processedDir: pathlib.Path, outputDir: pathlib.Path):
        errorsString = ""
        for listkey, error in errors.items():
            errorsString += "   ERROR: " + error.get("file") + " --> \"" + error.get("errorStatus") + "\"\n"
        if errorsString == "":
            errorsString = "    <none>"
        print(f"""
---------------- Report ---------------- 
       
Operation type:     {self.role}
# of successes:     {str(successNum)}
# of errors:        {str(errorNum)}

Errors that occurred:

{errorsString}


Input files that were successfully processed have been moved to {str(processedDir)} and the output files have been placed in {str(outputDir)}. To process the remaining files that were unsuccessful, fix the errors, and run the same command again.
        """)

