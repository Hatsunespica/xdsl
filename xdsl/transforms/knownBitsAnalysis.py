import xdsl.parser
from xdsl.ir import *
from xdsl.irdl import *
from xdsl.printer import Printer
from xdsl.parser import Parser
from xdsl.dialects.builtin import *
from xdsl.dialects.arith import *
from xdsl.dialects.scf import *
from xdsl.pattern_rewriter import *
from functools import singledispatch
from abc import ABC
from typing import TypeVar, cast
from dataclasses import dataclass
from xdsl.utils.knownBits import KnownBits
from xdsl.passes import ModulePass


from xdsl.utils.hints import isa
from xdsl.dialects.builtin import Signedness, IntegerType, i32, i64, IndexType
from xdsl.dialects.memref import MemRefType
from xdsl.ir import Operation, SSAValue, OpResult, Attribute, MLContext

from xdsl.pattern_rewriter import (RewritePattern, PatternRewriter,
                                   op_type_rewrite_pattern,
                                   PatternRewriteWalker,
                                   GreedyRewritePatternApplier)
from xdsl.dialects import mpi, llvm, func, memref, arith, builtin


@dataclass
class ConstantFolding(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: Addi, rewriter: PatternRewriter):
        if isinstance(op.lhs.op, Constant) and isinstance(op.rhs.op, Constant):
            rewriter.replace_matched_op(
                Constant.from_int_and_width(
                    op.lhs.op.value.value.data + op.rhs.op.value.value.data,
                    op.lhs.op.value.typ.width.data))


ATTR_NAME = 'knownBits'


def getBitsAnalysis(op, width):
    if isinstance(op, Operation) and ATTR_NAME in op.attributes:
        return op.attributes[ATTR_NAME]
    return StringAttr('X' * width)


@singledispatch
def transferFunction(op, str: StringAttr):
    pass


@transferFunction.register
def _(op: Addi, str: StringAttr):
    width = op.results[0].typ.width.data
    lBitsAnalysisStr = getBitsAnalysis(op.lhs.owner, width).data
    lBits = KnownBits.from_string(lBitsAnalysisStr)
    rBits = KnownBits.from_string(getBitsAnalysis(op.rhs.owner, width).data)

    knownBits = AddImpl(lBits, rBits)
    op.attributes[ATTR_NAME] = StringAttr(knownBits.to_string())


@transferFunction.register
def _(op: Constant, str: StringAttr):
    width = op.results[0].typ.width.data
    analysisStr = getBitsAnalysis(op, width).data
    resStr = ""
    for i in range(len(analysisStr)):
        if (op.value.value.data & (1 << i)) != 0:
            resStr += '1'
        else:
            resStr += '0'
    op.attributes[ATTR_NAME] = StringAttr(resStr)


@transferFunction.register
def _(op: AndI, str: StringAttr):
    width = op.results[0].typ.width.data
    lBitsAnalysisStr = getBitsAnalysis(op.lhs.owner, width).data
    lBits = KnownBits.from_string(lBitsAnalysisStr)
    rBits = KnownBits.from_string(getBitsAnalysis(op.rhs.owner, width).data)

    knownBits = AndImpl(lBits, rBits)
    op.attributes[ATTR_NAME] = StringAttr(knownBits.to_string())


@transferFunction.register
def _(op: OrI, str: StringAttr):
    width = op.results[0].typ.width.data
    lBitsAnalysisStr = getBitsAnalysis(op.lhs.owner, width).data
    lBits = KnownBits.from_string(lBitsAnalysisStr)
    rBits = KnownBits.from_string(getBitsAnalysis(op.rhs.owner, width).data)

    knownBits = orImpl(lBits, rBits)
    op.attributes[ATTR_NAME] = StringAttr(knownBits.to_string())


@transferFunction.register
def _(op: XOrI, str: StringAttr):
    width = op.results[0].typ.width.data
    lBitsAnalysisStr = getBitsAnalysis(op.lhs.owner, width).data
    lBits = KnownBits.from_string(lBitsAnalysisStr)
    rBits = KnownBits.from_string(getBitsAnalysis(op.rhs.owner, width).data)

    knownBits = XorImpl(lBits, rBits)
    op.attributes[ATTR_NAME] = StringAttr(knownBits.to_string())


@dataclass
class AssignAttributes(RewritePattern):
    @op_type_rewrite_pattern
    def match_and_rewrite(self, op: Operation, rewriter: PatternRewriter):
        strAttr = StringAttr("123123123")
        transferFunction(op, strAttr)

@dataclass
class KnownBitsAnalysisPass(ModulePass):
    name = "kb"
    def apply(self, ctx: MLContext, op: builtin.ModuleOp) -> None:
        walker = PatternRewriteWalker(GreedyRewritePatternApplier([
            AssignAttributes()
        ]),
            walk_regions_first=True,
            apply_recursively=True,
            walk_reverse=False)
        walker.rewrite_module(op)
