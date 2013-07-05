from nineml.abstraction_layer.readers import XMLReader

class CgClosure:
    def __init__ (self, formals, pyFunc):
        self.formals = formals
        self.function = pyFunc

    def __call__ (self, parameterSet):
        args = map (lambda p: parameterSet[p.name].value, self.formals)
        return self.function (*args)

def alConnectionRuleFromURI (uri):
    component = XMLReader.read (uri)
    return CgClosure (component.parameters, component.connection_rule)
