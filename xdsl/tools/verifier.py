from z3 import *
import inspect
import sys
import importlib.util

WIDTH = 16


def getInstanceFromAbs(abs):
    inst = BitVec("inst" + getattr(abs, "__absValName__"), WIDTH)
    return (inst, abs.getInstanceConstraint(inst))


def getBaseVariable(parameter, prefix):
    if "inspect._empty" in str(parameter.annotation):
        return BitVec(prefix + parameter.name + "BitVec", WIDTH)
    assert False and "Only support integers for now"
    return None


def getAbsValue(absType, absName):
    constructor = getattr(absType, "__init__")

    sig = inspect.signature(constructor)
    argList = []
    for x, y in sig.parameters.items():
        if x != "self":
            argList.append(getBaseVariable(y, absName))
    obj = absType(*argList)
    setattr(obj, "__absValName__", absName)
    return (obj, obj.getConstraint())


class Oracle:
    @staticmethod
    def getAbsOperands(func, width):
        sig = inspect.signature(func)
        argList = []
        argConstraint = []
        for x, y in sig.parameters.items():
            if x == "self":
                continue
            absVal, absValConstraint = getAbsValue(y.annotation, x)
            argList.append(absVal)
            argConstraint.append(And(absValConstraint))
        return (argList, argConstraint)

    @staticmethod
    def getInstOperands(absOperands, width):
        instList = []
        instConstraints = []
        for arg in absOperands:
            assert getattr(arg, "__absValName__")
            inst, instConstraint = getInstanceFromAbs(arg)
            instList.append(inst)
            instConstraints.append(And(instConstraint))
        return (instList, instConstraints)


def basicConstraintCheck(absOp):
    s = Solver()
    absOperands, absConstraint = Oracle.getAbsOperands(absOp, WIDTH)
    s.add(absConstraint)
    G = absOp(*absOperands)
    s.add(Not(And(G.getConstraint())))
    checkRes = s.check()
    if str(checkRes) == 'sat':
        print("basic constraint check failed!\ncounterexample:\n")
        print(s.model())
        return -1
    elif str(checkRes) == 'unsat':
        print("basic constraint check successfully")
        return 1
    else:
        print("unknown: ", checkRes)
        return 0


def soundnessCheck(concreteOp, absOp):
    s = Solver()
    absOperands, absConstraint = Oracle.getAbsOperands(absOp, WIDTH)
    s.add(absConstraint)
    G = absOp(*absOperands)
    instList, instConstraints = Oracle.getInstOperands(absOperands, WIDTH)
    s.add(instConstraints)
    s.add(simplify(Not(And(G.getInstanceConstraint(concreteOp(*instList))))))
    checkRes = s.check()
    if str(checkRes) == 'sat':
        print("soundness check failed!\ncounterexample:\n")
        print(s.model())
        return -1
    elif str(checkRes) == 'unsat':
        print("soundness check successfully")
        return 1
    else:
        print("unknown: ", checkRes)
        return 0


def precisionCheck(concreteOp, absOp):
    s = Solver()
    absOperands, absContraint = Oracle.getAbsOperands(absOp, WIDTH)
    s.add(absContraint)
    G = absOp(*absOperands)
    setattr(G, "__absValName__", "G")
    s.add(G.getConstraint())
    instG, instGConstraint = getInstanceFromAbs(G)
    s.add(instGConstraint)
    instList, instConstraints = Oracle.getInstOperands(absOperands, WIDTH)
    # for now
    qualifier = instList
    s.add(
        ForAll(qualifier,
               Implies(And(instConstraints),
                       instG != concreteOp(*instList)))
    )
    checkRes = s.check()
    if str(checkRes) == 'sat':
        print("precision check failed!\ncounterexample:\n")
        print(s.model())
        return -1
    elif str(checkRes) == 'unsat':
        print("precision check successfully")
        return 1
    else:
        print("unknown: ", checkRes)
        return 0


IMPORT_FILE = sys.argv[1]

spec = importlib.util.spec_from_file_location(IMPORT_FILE[:-3], IMPORT_FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert hasattr(module, "NEED_VERIFY")

for job in module.NEED_VERIFY:
    print("Currently verifying:", job[0].__name__)
    basicConstraintCheck(job[1])
    soundnessCheck(job[0], job[1])
    precisionCheck(job[0], job[1])
