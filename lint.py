#!/usr/bin/python

import re
import sys
import argparse
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
        self.toOneTrueBraceStyle = re.compile(r'\s*?\n\s*\{', re.DOTALL)
        self.toOneTrueBraceStyle_elsePatch = re.compile(r'\}\s*else\s*?\n\s*\{', re.DOTALL)
        self.fromOneTrueBraceStyle = re.compile(r'\s*\{( |\t)*')
        self.fromOneTrueBraceStyle_elsePatch = re.compile(r'(\s*)\}\s*else')
        self.fixBraceIndentation = re.compile(r'^(( |\t)*)(.*)\n\{', re.MULTILINE)

        self.sameLine = "n" not in flags
        self.pretend = "p" in flags

        if "d" in flags:
            rootDir = flags[flags.index("-d")+1]
        else:
            match = re.search(r':\s+(.+?):\s+', commands.getoutput("$(git rev-parse --show-toplevel)"))
            rootDir = match.group(1)
        print "Processing files in %s" % os.getcwd()

        if "all" in flags:
            for fileName in commands.getoutput("find %s" % rootDir).strip().split("\n"):
                cont = True
                if "ignore" in flags:
                    for ignore in flags.ignore:
                        if fileName.replace(rootDir+"/", "", 1).startswith(ignore[0]):
                            cont = False
                            break
                if not cont:
                    continue
                file = SourceFile(fileName, rootDir, self.pretend)
                if file.ext:
                    self.files.append(file)
        else:
            status = commands.getoutput("git status")
            match = re.search(r'branch\s+(.+?)\s*$', status, re.IGNORECASE | re.MULTILINE)
            changedFiles = commands.getoutput("git diff --name-only remotes/origin/%s ." % match.group(1))
            for fileName in changedFiles.strip().split("\n"):
                print "name = %s" % fileName
                file = SourceFile(fileName, rootDir, self.pretend)
                if file.ext:
                    print file
                    self.files.append(file)

    @staticmethod
    def run():
        parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
        parser.add_argument("-s", action='store_true', help="Converts to braces on the same line\n\t(default)")
        parser.add_argument("-n", action='store_true', help="Converts to braces on a new line")
        parser.add_argument("-d", action='store_true', help="Directory to operate on\n\t(defaults to current directory)")
        parser.add_argument("-p", action='store_true', help="Analyze for compliance, don't actually write anything")
        parser.add_argument("-u", action='store_true', help="Process only files that have changed since the last git push\n\t(default)")
        parser.add_argument("--all", action='store_true', help="Process all files in the directory\n\t(overrides -u)")
        parser.add_argument("--ignore", action="append", nargs=1, help="Ignore the indicated directory")
        linter = Lint(parser.parse_args())
        ret = linter.process()
        if ret is False:
            print "Lint analysis failed!"

    #Returns true if everything analyzed cleanly
    @staticmethod
    def analyze():
        linter = Lint(["lint", "-s", "-u", "-p"])
        ret = linter.process()
        if ret is False:
            print "Lint analysis failed!"
        return ret

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