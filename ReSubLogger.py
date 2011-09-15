class ReSubLogger:
    file = None
    replacement = None
    message = None
    suppressText = False
    level = 0
    offset = 0

    def __init__(self, file, replacement, message, level=0, suppressText=True):
        self.file = file
        self.replacement = replacement
        self.message = message
        self.suppressText = suppressText
        self.level = level
        self.offset = 0

    def setOffset(self, offset):
        self.offset = offset

    def subAndLog(self, match):
        if self.file.reportError(self.message, match, self.level, self.suppressText):
            self.file.reoffsetError(match, self.offset)
            if hasattr(self.replacement, '__call__'):
                ret = self.replacement(match)
            else:
                ret = self.replacement
            return match.expand(ret)
        else:
            return match.group(0)

    def subAndLogFunc(self, match):
        return self.subAndLog(match)