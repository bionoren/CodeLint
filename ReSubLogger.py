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
        if self.file.reportError(self.message, match, self.suppressText):
            if hasattr(self.replacement, '__call__'):
                ret = self.replacement(match)
            else:
                ret = self.replacement
            return match.expand(ret)
        else:
            return match.group(0)

    def subAndLogFunc(self, match):
        return self.subAndLog(match)