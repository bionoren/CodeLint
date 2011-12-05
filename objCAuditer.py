import re
from objCProperty import objCProperty
from ReSubLogger import ReSubLogger

class objCAuditor:
    #Usage: (+|-), returnType, methodName
    findMethod = r'%s\s*\(\s*%s\s*\)\s*%s[^\{]*\{(.*?)\n\}'
    #Usage: (+|-), returnType, methodName
    findMethodDeclaration = r'%s\s*\(\s*%s\s*\)\s*%s[^\{@]*\{'
    noPropertyAudit = re.compile(r'^\s*//\s*!lint-ignoreProperties')

    file = None

    def __init__(self, file):
        self.file = file

    @staticmethod
    def implementationExists(file):
        if file.fileWithExtension(".m"):
            return True
        return False

    def audit(self):
        objCProperty.audit(self.file)
        implementation = self.file.fileWithExtension(".m")
        if objCAuditor.noPropertyAudit.search(implementation.get()) is None:
            objCProperty.audit(implementation, self.file)
        self.fixSemicolonAfterMethod(implementation)
        self.fixWhiteSpaceInImplementation(implementation)
        self.fixSelfAssignment(implementation)
        return (implementation,)

    @staticmethod
    def methodWhiteSpaceSubHelper(match):
        return "%s\n\n%s" % (match.group(1), match.group(0)[1:])

    def fixWhiteSpaceInImplementation(self, file):
        data = file.get()
        exp = re.compile(objCAuditor.findMethodDeclaration % (r'(}|;)\n(?: |\t)*(?:\+|-)', r'\w+', r''))
        func = ReSubLogger(file, objCAuditor.methodWhiteSpaceSubHelper, "Insufficient newlines between method declarations.")
        data = exp.sub(func.subAndLogFunc, data)
        file.set(data)

    @staticmethod
    def semicolonAfterMethodHelper(match):
        return "%s%s" % (match.group(1), match.group(2))

    def fixSemicolonAfterMethod(self, file):
        data = file.get()
        exp = re.compile(r'((?:\+|-)\s*\(\s*\w+\s*\)\s*[^\{;]*);(\s*\{)')
        func = ReSubLogger(file, objCAuditor.semicolonAfterMethodHelper, "Why... do you have a semicolon here?", 1)
        data = exp.sub(func.subAndLogFunc, data)
        file.set(data)

    @staticmethod
    def selfAssignmentSubHelper(match):
        return 'if((self = [%s]))' % match.group(1)

    def fixSelfAssignment(self, file):
        data = file.get()
        exp = re.compile(r'self\s*=\s*\[\s*([^\]]+)\]\s*;\s*if\(\s*self\s*\)')
        func = ReSubLogger(file, objCAuditor.selfAssignmentSubHelper, "Improper initialization of self")
        data = exp.sub(func.subAndLogFunc, data)
        file.set(data)