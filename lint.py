#!/usr/bin/python

import re
import sys
import getopt
import commands
import os
from SourceFile import SourceFile
from objCAuditer import objCAuditor
from ReSubLogger import ReSubLogger

class Lint:
    toOneTrueBraceStyle = None
    toOneTrueBraceStyle_elsePatch = None
    fromOneTrueBraceStyle = None
    fromOneTrueBraceStyle_elsePatch = None
    fixBraceIndentation = None
    validFileExtensions = (".m", ".h")
    pretend = False
    sameLine = False
    files = list()
    originalDir = None

    def __init__(self, flags):
        if "-h" in flags or "--help" in flags:
            self.usage()
            exit(0)

        self.toOneTrueBraceStyle = re.compile(r'\s*?\n\s*\{', re.DOTALL)
        self.toOneTrueBraceStyle_elsePatch = re.compile(r'\}\s*else\s*?\s*\{', re.DOTALL)
        self.fromOneTrueBraceStyle = re.compile(r'\s*\{( |\t)*')
        self.fromOneTrueBraceStyle_elsePatch = re.compile(r'(\s*)\}\s*else')
        self.fixBraceIndentation = re.compile(r'^(( |\t)*)(.*)\n\{', re.MULTILINE)

        self.sameLine = "-n" not in flags
        self.pretend = "-p" in flags

        if "-d" in flags:
            rootDir = flags[flags.index("-d")+1]
        else:
            rootDir = commands.getoutput("git rev-parse --show-toplevel")
        print "Processing files in %s" % os.getcwd()

        if "--all" in flags:
            for fileName in os.listdir(rootDir):
                if fileName[0] != ".":
                    file = SourceFile(fileName, rootDir, self.pretend)
                    if file.ext:
                        self.files.append(file)
        else:
            status = commands.getoutput("git status")
            match = re.search(r'branch\s+(.+?)\s*$', status, re.IGNORECASE | re.MULTILINE)
            changedFiles = commands.getoutput("git diff --name-only remotes/origin/%s ." % match.group(1))
            for fileName in changedFiles.strip().split("\n"):
                file = SourceFile(fileName, rootDir, self.pretend)
                if file.ext:
                    print file
                    self.files.append(file)

    @staticmethod
    def run():
        try:
            opts, args = getopt.getopt(sys.argv, "hsndpu:", ["all", "help"])
            linter = Lint(args[1:])
            ret = linter.process()
            if ret is False:
                print "Lint analysis failed!"
        except getopt.GetoptError:
            Lint.usage()

    #Returns true if everything analyzed cleanly
    @staticmethod
    def analyze():
        linter = Lint(["lint", "-s", "-u", "-p"])
        ret = linter.process()
        if ret is False:
            print "Lint analysis failed!"
        return ret

    @staticmethod
    def usage():
        print "Usage: work.py lint (-s | -n) [-au] [-d DIR]"
        print "-h     Display this usage message"
        print "--help Display this usage message"
        print "-p     Analyze for compliance, don't actually write anything"
        print "-s     Converts to braces on the same line\n\t(default)"
        print "-n     Converts to braces on a new line"
        print "-d     Directory to operate on\n\t(defaults to current directory)"
        print "--all  Process all files in the directory\n\t(overrides -u)"
        print "-u     Process only files that have changed since the last git push\n\t(default)"

    #Returns true if everything analyzed cleanly or if everything was updated to analyze cleanly
    def process(self):
        noErrors = True
        for file in self.files:
            print "processing %s\n========================" % file
            self.convertLineEndings(file)
            self.fixWhiteSpace(file)
            if file.type() == "header":
                if objCAuditor.implementationExists(file):
                    auditer = objCAuditor(file)
                    files = auditer.audit()
                    for f in files:
                        f.save()
                        if self.pretend:
                            for error in f.getErrors():
                                print error
                        noErrors = noErrors and not f.hasErrors()
            file.save()
            if self.pretend:
                for error in file.getErrors():
                    print error
            noErrors = noErrors and not file.hasErrors()
        if self.pretend:
            return noErrors
        return True

#fixing braces and whitespace
    def convertToOneTrueBraceStyle(self, input, file):
        func = ReSubLogger(file, r' {', "Invalid brace style")
        match = re.search(re.escape(input), file.get())
        func.setOffset(match.start())
        ret = self.toOneTrueBraceStyle.sub(func.subAndLog, input)
        #patch else blocks together
        func = ReSubLogger(file, r'} else {', "Invalid brace style")
        func.setOffset(match.start())
        return self.toOneTrueBraceStyle_elsePatch.sub(func.subAndLog, ret);

    def convertFromOneTrueBraceStyle(self, input, file):
        func = ReSubLogger(file, r'\n{', "Invalid brace style")
        match = re.search(re.escape(input), file.get())
        func.setOffset(match.start())
        ret = self.fromOneTrueBraceStyle.sub(func.subAndLog, input);
        #patch else blocks together
        func = ReSubLogger(file, r'\1}\1else', "Invalid brace style")
        func.setOffset(match.start())
        return self.fromOneTrueBraceStyle_elsePatch.sub(func.subAndLog, ret);

    def convertLineEndings(self, file):
        if self.sameLine:
            function = self.convertToOneTrueBraceStyle
        else:
            function = self.convertFromOneTrueBraceStyle

        findQuotedStringOrLineComment = re.compile(r'(?:"(?:[^"\\]*?(?:\\.[^"\\]*?)*?)"|//.*?$)', re.DOTALL | re.MULTILINE)
        notStrings = findQuotedStringOrLineComment.split(file.get())
        strings = findQuotedStringOrLineComment.finditer(file.get())

        for i in range(0, len(notStrings)):
            notStrings[i] = function(notStrings[i], file)

        ret = notStrings[0]
        for i in range(1, len(notStrings)):
            if len(notStrings[i]) > 0:
                if notStrings[i].startswith(" {"): #avoid problems with single line comments like this
                    ret += "{" + strings.next().group(0) + notStrings[i][2:]
                else:
                    ret += strings.next().group(0) + notStrings[i]
        if not self.sameLine:
            func = ReSubLogger(file, r'\1\3\n\1{', "Invalid brace style")
            ret = self.fixBraceIndentation.sub(func.subAndLog, ret)
        file.set(ret)

    def fixWhiteSpace(self, file):
        ret = file.get()

        #It's important that we check this first
        trailingWhiteSpace = re.compile(r'(?<=\S)(?: |\t)+\n')
        func = ReSubLogger(file, r'\n', "Trailing whitespace")
        ret = trailingWhiteSpace.sub(func.subAndLog, ret)

        multipleNewLines = re.compile(r'\n{3,}')
        func = ReSubLogger(file, r'\n\n', "Excessive newlines")
        ret = multipleNewLines.sub(func.subAndLog, ret)

        trailingWhiteSpace = re.compile(r'\n+$')
        func = ReSubLogger(file, r'', "Trailing newlines")
        ret = trailingWhiteSpace.sub(func.subAndLog, ret)

        if file.type() in ("objc", "header"):
            implementationEndWhiteSpace = re.compile(r'@end\n?(\S)')
            func = ReSubLogger(file, r'@end\n\n\1', "Insufficient whitespace after @end tag")
            ret = implementationEndWhiteSpace.sub(func.subAndLog, ret)

        file.set(ret)

if __name__ == "__main__":
    Lint.run()