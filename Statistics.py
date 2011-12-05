#!/bin/python
import re
from SourceFile import SourceFile

class Statistics:
    filesByType={}
    files=[]

    def analyze(self, sourceFile):
        statFile = StatFile(sourceFile)
        self.files.append(statFile)
        if not sourceFile.ext in self.filesByType:
            self.filesByType[sourceFile.ext] = []
        self.filesByType[sourceFile.ext].append(statFile)

    def __str__(self):
        ret = "Statistics:\n"
        types = ""
        files = len(self.files)
        for type,fileList in self.filesByType.iteritems():
            types += "%d *%s, " % (len(fileList), type)
        ret += "Files: %d (%s)\n" % (len(self.files), types[:-2])
        lines = reduce(lambda tot,file: tot+file.lines, self.files, 0)
        ret += "Lines: %d\n" % lines
        code = reduce(lambda tot,file: tot+file.code, self.files, 0)
        ret += "Lines of Code: %d\n" % code
        comment = reduce(lambda tot,file: tot+file.comments, self.files, 0)
        ret += "Lines of Comment: %d\n" % comment
        ret += "Lines of Whitespace: %d\n" % (lines-(code+comment))
        ret += "Avg LOC/File: %.2f" % (code/files)
        return ret

class StatFile:
    singleLineComment = re.compile(r'^\s*//', re.MULTILINE)
    multiLineComment = re.compile(r'/\*(.+?)\*/')
    findCode = re.compile(r'^[^\n\r\S]*?\S', re.MULTILINE)

    lines=0
    comments=0
    code=0
    sourceFile=None

    def __init__(self, sourceFile):
        self.sourceFile = sourceFile

        file = self.sourceFile.get()
        self.lines = self.linesInStr(file)
        slc = len(StatFile.singleLineComment.findall(file))
        mlcIter = StatFile.multiLineComment.finditer(file)
        mlc = 0
        for match in mlcIter:
            newlines = self.linesInStr(match)
            if newlines > 0:
                mlc += newlines+1
        self.comments = slc+mlc
        self.code = len(StatFile.findCode.findall(file))

    def linesInStr(self, str):
        return str.count("\n")+1
