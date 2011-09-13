class ReSubLogger:
    file = None
    replacement = None
    message = None
    suppressText = False

    def __init__(self, file, replacement, message, suppressText=True):
        self.file = file
        self.replacement = replacement
        self.message = message
        self.suppressText = suppressText

    def subAndLog(self, match):
        self.file.reportError(self.message, match, self.suppressText)
        return self.replacement

    def subAndLogFunc(self, match):
        return self.subAndLog(match)(match)