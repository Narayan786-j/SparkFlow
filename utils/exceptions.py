class Error(Exception):

    def __init__(self,status_code,details,actualErrorMessage=None,errorCode=None):
        self.status_code = status_code
        self.details = details
        self.actualErrorMessage = actualErrorMessage
        self.errorCode = errorCode

        if self.actualErrorMessage == None:
            self.actualErrorMessage = self.details
        if self.errorCode == None:
            self.errorCode = "HBFFPYTHONINT00003"