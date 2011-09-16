import re

class objCProperty:
    findIVarExp = r'(?:(?:__block|IBOutlet)\s+)*%s\s+%s\s*;'
    atomicity = "atomic"
    memory = "__strong"
    readonly = False
    block = ""
    iboutlet = ""
    type = None
    name = None
    pointer = False
    valid = True
    property = False
    dealloced = False

    def __init__(self, match, property):
        self.property = property
        self.valid = list()
        self.block = ""
        self.iboutlet = ""
        self.pointer = ""
        if self.property:
            self.memory = "strong"
            self.makeProperty(match)
        else:
            self.makeIVar(match)
        if len(self.valid) == 0:
            self.valid = True

    def correctNameAndType(self):
        if self.type.endswith("*"):
            self.valid.append("Invalid pointer '*' association")
            self.pointer = "*"
            self.type = self.type[:-1];
        if self.name.startswith("*"):
            self.pointer = "*"
            self.name = self.name[1:]

    def makeProperty(self, match):
        #read in the property modifiers
        if match.group(1):
            for modifier in match.group(1).lower().split(","):
                modifier = modifier.strip()
                if modifier.endswith("atomic"):
                    self.atomicity = modifier
                elif modifier == "readonly":
                    self.readonly = True
                elif modifier in ("strong", "weak", "autoreleasing", "unsafe_unretained", "copy", "retain", "assign"):
                    self.memory = modifier
                else:
                    self.valid.append("Unsupported property modifier %s" % modifier)
                    print "Unsupported property modifier %s" % modifier
                    raise NotImplementedError
                    self.memory = "UNDEFINED"
                    self.atomicity = "UNDEFINED"

        mod1 = None
        mod2 = None
        if match.group(2):
            mod1 = match.group(2).strip()
        if match.group(3):
            mod2 = match.group(2).strip()
        if mod1 == "IBOutlet" or mod2 == "IBOutlet":
            self.iboutlet = "IBOutlet "
        if mod1 == "__block" or mod2 == "__block":
            self.block = "__block "

        if self.iboutlet:
            if self.atomicity != "nonatomic" or self.memory not in ("weak", "strong"):
                self.valid.append("IBOutlet not declared (nonatomic, weak|strong)")
                self.atomicity = "nonatomic"
                self.memory = "weak"

        self.type = match.group(4).strip()
        self.name = match.group(5).strip()
        self.correctNameAndType()
        #make sure objects are declared copy when they could be mutable but aren't the mutable version
        if not self.readonly and self.type in ("NSArray", "NSSet", "NSDictionary", "NSString"):
            if self.memory != "copy":
                self.valid.append("Potentially mutable type %s not declared copy" % self.type)
                self.memory = "copy"

    def makeIVar(self, match):
        self.atomicity = match[0];
        modifiers = (match[1], match[2], match[3])
        for modifier in filter(lambda x:x, modifiers):
            modifier = modifier.strip()
            text = modifier.lower()
            if text == "__block":
                self.block = modifier
            elif text == "iboutlet":
                self.iboutlet = modifier
            elif text in ("__strong", "__weak", "__autoreleasing", "__unsafe_unretained"):
                self.memory = modifier
            else:
                self.valid.append("Unsupported property modifier %s" % modifier)
                print "Unsupported property modifier %s" % modifier
                raise NotImplementedError
                self.memory = "UNDEFINED"
                self.atomicity = "UNDEFINED"
        self.type = match[4]
        self.name = match[5]
        self.correctNameAndType()

    @staticmethod
    def audit(file, header=None):
        if "properties" not in file.metaData:
            if header:
                file.metaData["properties"] = header.metaData["properties"]
            else:
                file.metaData["properties"] = list()
        objCProperty.findProperties(file)
        objCProperty.findIVars(file)
        if file.type() != "header":
            objCProperty.fixSynthesis(file)

    @staticmethod
    def findProperties(file):
        data = file.get()
        findProperty = re.compile(r'@property\s+(?:\(((?:[^\,)],?)+)\)\s+)?(?:(__block|IBOutlet)\s+)?(?:(__block|IBOutlet)\s+)?(\S+)\s+(\S+?)\s*;', re.IGNORECASE)
        matches = findProperty.finditer(data)
        properties = list()
        for match in matches:
            #print match.groups()
            property = objCProperty(match, True)
            if property.valid is not True:
                for error in property.valid:
                    if file.reportError(error, match, 1, False):
                        data = data.replace(match.group(0), property.__str__())
            file.metaData["properties"].append(property)
        file.set(data)

    @staticmethod
    def findIVars(file):
        data = file.get()
        findIVarSection = re.compile(r'@interface[^@]*?\{([^}]*?)\}', re.DOTALL)
        section = findIVarSection.search(data)
        if section:
            #(IBOutlet|__block|__memoryType) type *? name;
            findIVars = re.compile(r'(\s*)((?:(?:__|IBO)\w+)\s+)?((?:(?:__|IBO)\w+)\s+)?((?:(?:__|IBO)\w+)\s+)?([^\s;]+)\s+((?:[^\s;]+\s*,?\s*)+);', re.DOTALL)
            propertyNames = map(lambda x:x.name, file.metaData["properties"])
            matches = findIVars.finditer(section.group(1))
            out = list()
            for match in matches:
                names = match.group(6).split(",")
                if len(names) > 1:
                    file.reportError("Multiple ivar declarations on the same line", match, 1, False)
                type = match.group(5)
                if type.endswith("*"):
                    names[0] = "*%s" % names[0].strip()
                    type = type[:-1]
                ivars = list()
                for name in names:
                    ivar = objCProperty((match.group(1), match.group(2), match.group(3), match.group(4), type.strip(), name.strip()), False)
                    if ivar.name in propertyNames and file.reportError("Unnecessary ivar declaration %s" % ivar.name, match, 1, False):
                        pass
                    else:
                        ivars.append(ivar.__str__())
                        file.metaData["properties"].append(ivar)
                data = data.replace(match.group(0), "".join(ivars))
        file.set(data)

    @staticmethod
    def fixSynthesis(file):
        data = file.get()
        findSynthesis = re.compile(r'(\s*)@(?:synthesize|dynamic)\s*((?:[^\s;]+\s*,?\s*)+);', re.DOTALL | re.IGNORECASE)
        matches = findSynthesis.finditer(data)
        properties = file.metaData["properties"]

        for match in matches:
            names = match.group(2).strip().split(",")
            if len(names) > 1:
                file.reportError("Synthesizing multiple properties on the same line", match, 1, False)
            out = list()
            for name in names:
                out.append("%s@synthesize %s;" % (match.group(1), name.strip()))
            if len(names) > 1:
                data = data.replace(match.group(0), "".join(out))
        file.set(data)

    @staticmethod
    def fixMemoryInImplementation(file):
        findPropertyAssignment = r'[^\.\w]%s\s*='
        findValidPropertyAssignment = r'self\.%s\s*=\s*'
        findCustomSetter = objCAuditor.findMethod % (r'-', r'void', r'set%s:')

        #fix property assignment without self.
        for property in objCProperty.properties:
            if property.property and property.memory != "readonly":
                name = property.name
                if property.name.startswith("*"):
                    name = name[1:]
                exp = re.compile(findPropertyAssignment % name)
                matches = exp.finditer(file)
                #if pretend, count how many we would fix and then subtract the number we revert in custom setters. If that's > 0, pretend fail
                count = 0
                for match in matches:
                    count += 1
                    if not pretend:
                        file = file.replace(match.group(0), "%sself.%s" % (match.group(0)[0], match.group(0)[1:]))
                ucfirstname = "%s%s" % (name[0].upper(), name[1:])
                exp = re.compile(findCustomSetter % ucfirstname, re.DOTALL)
                setter = exp.search(file)
                if setter:
                    exp = re.compile(findValidPropertyAssignment % name)
                    matches = exp.finditer(setter.group(1))
                    setterBlock = setter.group(0)
                    for match in matches:
                        count -= 1
                        if not pretend:
                            setterBlock = setterBlock.replace(match.group(0), "%s = " % name)
                    if not pretend:
                        file = file.replace(setter.group(0), setterBlock)
                if pretend and count != 0:
                    return False
            elif property.property and property.memory == "readonly":
                name = property.name
                if property.name.startswith("*"):
                    name = name[1:]
                exp = re.compile(findValidPropertyAssignment % name)
                matches = exp.finditer(file)
                for match in matches:
                    if pretend:
                        return False
                    file = file.replace(match.group(0), "%s = " % name)

        #fix init/dealloc and viewDidLoad/Unload
        findInit = re.compile(findMethod % (r'-', r'id', r'init'), re.IGNORECASE | re.DOTALL)
        findDealloc = re.compile(findMethod % (r'-', r'void', r'dealloc'), re.IGNORECASE | re.DOTALL)
        findViewDidLoad = re.compile(findMethod % (r'-', r'void', r'viewDidLoad'), re.IGNORECASE | re.DOTALL)
        findViewDidUnload = re.compile(findMethod % (r'-', r'void', r'viewDidUnload'), re.IGNORECASE | re.DOTALL)
        findAssignment = re.compile(r'(\w+)\s*=')

        matches = findInit.finditer(file)
        assignedInInit = list()
        for match in matches:
            matches2 = findAssignment.finditer(match.group(1))
            for match in matches2:
                name = match.group(1)
                if name != "self":
                    assignedInInit.append(name)
        assignedInViewDidLoad = list()
        viewDidLoad = findViewDidLoad.search(file)
        if viewDidLoad:
            matches = findAssignment.finditer(viewDidLoad.group(1))
            for match in matches:
                name = match.group(1)
                if name not in assignedInInit:
                    assignedInViewDidLoad.append(name)
            print assignedInInit
            print assignedInViewDidLoad

            if len(assignedInViewDidLoad) > 0:
                viewDidUnload = findViewDidUnload.search(file)
                if not viewDidUnload:
                    if pretend:
                        return False
                    viewDidUnload = "-(void)viewDidUnload {\n}"
                    file = file.replace(viewDidLoad.group(0), "%s\n\n%s" % (viewDidLoad.group(0), viewDidUnload))
                for property in objCProperty.properties:
                    if property.iboutlet or property.name in assignedInViewDidLoad:
                        #convert [self set%s:nil] calls to self.%s = nil
                        pass

        return file

    def __str__(self):
        if self.property:
            if self.readonly:
                memory = "readonly, %s" % self.memory
            else:
                memory = self.memory
            pointer = ""
            if self.pointer:
                pointer = "*"
            return "@property (%s, %s) %s%s%s %s%s;" % (self.atomicity, memory, self.block, self.iboutlet, self.type, pointer, self.name)
        else:
            #atomicty is hacked for ivars to contain the leading whitespace
            return "%s%s %s%s%s %s%s;" % (self.atomicity, self.memory, self.block, self.iboutlet, self.type, self.pointer, self.name)