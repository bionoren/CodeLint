class ReSubLogger:
    file = None
    replacement = None
    message = None
    suppressText = False
    level = 0

    def __init__(self, file, replacement, message, level=0, suppressText=True):
        self.file = file
        self.replacement = replacement
        self.message = message
        self.suppressText = suppressText
        self.level = level

    def subAndLog(self, match):
        if self.file.reportError(self.message, match, self.level, self.suppressText):
            if hasattr(self.replacement, '__call__'):
                ret = self.replacement(match)
            else:
                ret = self.replacement
            return match.expand(ret)
        else:
            return match.group(0)

    def subAndLogFunc(self, match):
        return self.subAndLog(match)