class Error(Exception):
     def __init__(self, message="psimi module error"):
         super(Error,self).__init__(message)

class EvidTypeError(Error):
    def __init__(self, message="Unsupported EvidType"):
        super(EvidTypeError,self).__init__(message)

class MissingParentError(Error):
    def __init__(self, message="Missing Parent Element"):
        super(MissingParentError,self).__init__(message)

    
        



