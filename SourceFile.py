import os
import re

class SourceFile:
    validFileExtensions = (".m", ".h")
    ignoreMatch = re.compile(r'[^\n]*\!lint-ignore', re.MULTILINE)

    errors = None
    metaData = None
    name = None
    ext = None
    contents = None
    root = None
    modified = False
    pretend = False

    def __init__(self, fileName, rootDir, pretend):
        self.ext = SourceFile.filterLineEndings(fileName)
        if self.ext:
            self.name = fileName[:-len(self.ext)]
            if not rootDir:
                rootDir = os.getcwd()
            self.root = rootDir
            self.errors = list()
            self.metaData = {}
            self.modified = False
            self.pretend = pretend

    @staticmethod
    def filterLineEndings(fileName):
        for ext in SourceFile.validFileExtensions:
            if fileName.endswith(ext):
                return ext
        return False

    #Returns False if the error was suppressed
    #level starts at 0 for uninteresting stuff. It escalates from there
    def reportError(self, error, match, level=0, suppressText=True):
        ignore = SourceFile.ignoreMatch.match(self.get(), match.start())
        if ignore is None:
            lineno = self.get().count("\n", 0, match.start())+2
            if not suppressText:
                badString = match.group(0)
            else:
                badString = None
            self.errors.append((error, lineno, badString, level))
            return True
        return False

    def reoffsetError(self, match, amount):
        if amount != 0:
            error = self.errors[-1]
            lineno = self.get().count("\n", 0, match.start()+amount)+2
            self.errors[-1] = (error[0], lineno, error[2], error[3])

    def hasErrors(self):
        return len(self.errors)

    def getErrors(self):
        for errorTuple in self.errors:
            if errorTuple[2]:
                yield "%s:%s: %s: %s (%s)" % (self, errorTuple[1], errorTuple[0], self.errorTypeForLevel(errorTuple[3]), errorTuple[2])
            else:
                yield "%s:%s: %s: %s" % (self, errorTuple[1], self.errorTypeForLevel(errorTuple[3]), errorTuple[0])

    def errorTypeForLevel(self, level):
        if level <= 0:
            return 'warning'
        else:
            return 'error'

    def getRawErrors(self):
        for errorTuple in errors:
            yield errorTuple

    def fileWithExtension(self, extension):
        if os.path.exists("%s%s" % (self.name, extension)):
            return SourceFile("%s%s" % (self.name, extension), self.root, self.pretend)
        return None

    def get(self):
        if not self.contents:
            current = os.getcwd()
            os.chdir(self.root)
            with open(self.__str__()) as file:
                self.contents = file.read()
            os.chdir(current)
        return self.contents

    def set(self, contents):
        if not self.pretend:
            self.contents = contents
            self.modified = True

    def save(self):
        if self.contents and self.modified:
            current = os.getcwd()
            os.chdir(self.root)
            with open("%s%s" % (self.name, self.ext), "w") as file:
                file.write(self.contents)
            os.chdir(current)

    def replace(self, find, replace):
        self.contents = self.contents.replace(find, replace)

    def type(self):
        if self.ext == ".m":
            return "objc"
        if self.ext == ".h":
            return "header"

    def __str__(self):
        return "%s%s" % (self.name, self.ext)