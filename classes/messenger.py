import pathlib
from __main__ import aboutThisProgramShort

class messenger(object):
    """
    A class for conveying information to the user.

    This class was an easy way for me to print information in a consistent
    fashion and avoid randomly throwing print() statements around willy-nilly.
    """

    def __init__(self, name: str):
        self.role = name


    def programInitMesg(self,
                        doc: str,
                        author: str,
                        version: str,
                        verbose: bool = False):
        if verbose:
            print(f"""
# -----------------------------
{doc}

Author: {author}
Version: {version}
# -----------------------------
"""         )
        else:
            print(f"""
# -----------------------------
Submerge.py

Author: {author}
Version: {version}
# -----------------------------
"""         )


    def say(self, message: str, indent: int = 0):
        print(str("    "*indent) + message)


    def inform(self, message: str, indent: int = 0):
        print(str("    "*indent) + self.role + ": " + message)


    def saySuccess(self, successMessage: str):
        print("SUCCESS: " + successMessage)


    def sayError(self, errorMessage: str):
        print("ERROR: " + errorMessage)


    def sayDictKey(self, dct: dict, key, keyLabel: str = None):
        if keyLabel != None:
            label = keyLabel + " "
        else:
            label = ""
        print(f"{label}{str(key)}: {str(dct[key])}")


    def sayDict(self, dct: dict, keyLabel: str = None):
        if keyLabel != None:
            label = keyLabel + " "
        else:
            label = ""
        for key, val in dct.items():
            print(f"{label}{str(key)}: {str(valcount in)}")


    def operationReport(self,
                        successNum: int,
                        errorNum: int, 
                        errors: dict,
                        processedDir: pathlib.Path, 
                        outputDir: pathlib.Path):
        
        errorsString = ""
        for listkey, error in errors.items():
            errorsString += (f"   ERROR: {str(error.get('file'))} --> "
                             f"\"{str(error.get('error'))}\"\n")
        if errorsString == "":
            errorsString = "    <none>"
        print((f"""
---------------- Report ---------------- 
       
Operation type:     {self.role}
# of successes:     {str(successNum)}
# of errors:        {str(errorNum)}

Errors that occurred:

{errorsString}


Input files that were successfully processed have been moved to"""
f"{str(processedDir)} and the output files have been placed in "
f"{str(outputDir)}. To process the remaining files that were unsuccessful, "
f"fix the errors, and run the same command again."
        ))

