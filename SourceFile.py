import os
import re

class SourceFile:
    validFileExtensions = (".m", ".h")
    ignoreSearch = re.compile(r'\$ignore\s*?$', re.MULTILINE)

    errors = None
    metaData = None
    name = None
    ext = None
    contents = None
    root = None

    def __init__(self, fileName, rootDir=None):
        self.ext = SourceFile.filterLineEndings(fileName)
        if self.ext:
            path = fileName.split("/")
            self.name = path[len(path)-1][:-len(self.ext)]
            if not rootDir:
                rootDir = os.getcwd()
            self.root = rootDir
            self.errors = list()
            self.metaData = {}

    @staticmethod
    def filterLineEndings(fileName):
        for ext in SourceFile.validFileExtensions:
            if fileName.endswith(ext):
                return ext
        return False

    #Returns False if the error was suppressed
    def reportError(self, error, match, suppressText=True):
        ignore = self.ignoreSearch.search(self.get(), match.start())
        if ignore is None:
            lineno = self.get().count("\n", 0, match.start())+1
            if not suppressText:
                badString = match.group(0)
            else:
                badString = None
            self.errors.append((error, lineno, badString))
            return True
        return False

    def hasErrors(self):
        return len(self.errors)

    def getErrors(self):
        for errorTuple in self.errors:
            if errorTuple[2]:
                yield "%s:%s: %s (%s)" % (self, errorTuple[1], errorTuple[0], errorTuple[2])
            else:
                yield "%s:%s: %s" % (self, errorTuple[1], errorTuple[0])

    def getRawErrors(self):
        for errorTuple in errors:
            yield errorTuple

    def fileWithExtension(self, extension):
        if os.path.exists("%s%s" % (self.name, extension)):
            return SourceFile("%s%s" % (self.name, extension))
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
        self.contents = contents

    def save(self):
        if self.contents:
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