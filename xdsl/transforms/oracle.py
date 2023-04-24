from z3 import *

def contains(x,y):
    return (x|y)==x

def getAbsValue(name, width, s):
    zeros=BitVec('zeros'+name,width)
    ones=BitVec('ones'+name,width)
    s.add(zeros & ones == 0)
    return (zeros,ones)

#check is a given value is an abstract value

def isAbsValue(value):
    return isinstance(value,tuple) and len(value)==2

def getMaxFromAbsValue(absVal):
    return ~absVal[0]

def getMinFromAbsValue(absVal):
    return absVal[1]

def getInstanceFromAbsValue(name, width,absValue,s):
    inst=BitVec(name,width)
    s.add(contains(inst,absValue[1]))
    s.add(contains(~inst,absValue[0]))
    return inst


class Oracle:
    @staticmethod
    def getOperands(opName, width, solver):
        if opName=="OR" or opName=="XOR" or opName=="AND" or opName=='ADD' or opName=='SUB':
            X = getAbsValue('Op0',width, solver)
            Y = getAbsValue('Op1',width, solver)
            return [X,Y]
        elif opName=="TRUNC":
            X=getAbsValue('Op0',width,solver)
            newWidth=BitVec("newWidth",width)
            solver.add(newWidth<width)
            return [X,newWidth]
        else:
            print("Operation not supported yet")
        assert False
