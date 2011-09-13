import re
from objCProperty import objCProperty
from ReSubLogger import ReSubLogger

class objCAuditor:
    #Usage: (+|-), returnType, methodName
    findMethod = r'%s\s*\(\s*%s\s*\)\s*%s[^\{]*\{(.*?)\n\}'
    #Usage: (+|-), returnType, methodName
    findMethodDeclaration = r'%s\s*\(\s*%s\s*\)\s*%s[^\{]*\{'

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
        objCProperty.audit(implementation, self.file)
        self.fixWhiteSpaceInImplementation(implementation)
        return (implementation,)

    @staticmethod
    def methodWhiteSpaceSubHelper(match):
        return "}\n\n%s" % match.group(0)[1:]

    def fixWhiteSpaceInImplementation(self, file):
        data = file.get()
        exp = re.compile(objCAuditor.findMethodDeclaration % (r'}\n(?: |\t)*(?:\+|-)', r'\w+', r''))
        func = ReSubLogger(file, objCAuditor.methodWhiteSpaceSubHelper, "Insufficient newlines between method declarations.")
        data = exp.sub(func.subAndLogFunc, data)
        file.set(data)