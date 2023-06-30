from typing import Dict, Optional, List, TypedDict, cast, overload
import libcst as cst
import yaml
import sys
import collections

class TestDeclaration(TypedDict):
    name: str
    version: str
    reason: str


class TracerManifest(TypedDict):
    released: Optional[List[TestDeclaration]]
    irrelevant: Optional[List[TestDeclaration]]
    bug: Optional[List[TestDeclaration]]

    tracer: str


def comp_operator(op: str) -> cst.BaseCompOp:
    if op == "==":
        return cst.Equal()
    elif op == "!=":
        return cst.NotEqual()
    elif op == "<=":
        return cst.LessThanEqual()
    elif op == "<":
        return cst.LessThan
    elif op == ">=":
        return cst.GreaterThanEqual()
    elif op == ">":
        return cst.GreaterThan()

# Set of helpers to generate verbose cst types

def str_comp(lhs: cst.BaseExpression, rhs: str, op: str) -> cst.Comparison:
    return cst.Comparison(left=lhs,
                          comparisons=[cst.ComparisonTarget(operator=comp_operator(op),
                                                            comparator=string(rhs))])

def context_arg(ctxArg: str, val: str) -> cst.Arg:
    return  cst.Arg(keyword=cst.Attribute(value=cst.Name("context"), attr=cst.Name(ctxArg)), value=string(val))

def string(s: str) -> cst.SimpleString:
    return cst.SimpleString(f'"{s}"')

def arg(val: cst.BaseExpression) -> cst.Arg:
    return cst.Arg(value=val)

def kw_arg(kw: str, val) -> cst.Arg:
    return cst.Arg(keyword=cst.Name(value=kw), value=val)

def attr(base: str, attribute: str) -> cst.Attribute:
    return cst.Attribute(value=cst.Name(base), attr=cst.Name(attribute))

def decorator(funcName: str, args: List[cst.Arg]) -> cst.Decorator:
    return cst.Decorator(decorator=cst.Call(
        func=cst.Name(value=funcName),
        args=args
    ))

# Generate @release decorator
def release(library: str, version: str) -> cst.Decorator:
    args = [cst.Arg(keyword=cst.Name(value=library), value=string(version))]
    return decorator("released", args)

# Generate @irrelevant decorator
def irrelevant(library: str, reason: str) -> cst.Decorator:
    args = [arg(str_comp(attr("context", "library"),library, "==")), kw_arg("reason", string(reason))]
    return cst.Decorator(decorator=cst.Call(
        func=cst.Name(value="irrelevant"),
        args=args
    ))

# Generate @irrelevant decorator
def bug(library,reason) -> cst.Decorator:
    return

def gen_decorators(manifest: TracerManifest) -> Dict[str, List[cst.Decorator]]:
    decs = collections.defaultdict(list)
    lib = manifest["tracer"]

    if "released" in manifest:
        for test_entry in manifest["released"]:
            decs[test_entry["name"]].append(release(lib, test_entry["version"]))
    if "irrelevant" in manifest:
        for test_entry in manifest["irrelevant"]:
            decs[test_entry["name"]].append(irrelevant(lib, test_entry["reason"]))

    return decs

class MetadataWriter(cst.CSTTransformer):
    def __init__(self):
        super().__init__()
        with open(manifest_path) as fp:
            self.manifest = cast(TracerManifest, yaml.load(fp, yaml.CLoader))
            self.decs = gen_decorators(self.manifest)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node : cst.ClassDef) -> cst.ClassDef:
        if not original_node.name.value.startswith("Test_"):
            return updated_node
        decorators = [release("golang", "?")]
        if original_node.name.value in self.decs:
            decorators = self.decs[original_node.name.value]
        return updated_node.with_changes(decorators=decorators)

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node : cst.FunctionDef) -> cst.FunctionDef:
        if not original_node.name.value.startswith("test_"):
            return updated_node
        decorators = []
        if original_node.name.value in self.decs:
            decorators = self.decs[original_node.name.value]
        return updated_node.with_changes(decorators=decorators)

file="test_addresses.py"
if len(sys.argv) != 3:
    print("Usage: %s <path/to/manifest.yaml> <path/to/test.py>")
manifest_path = sys.argv[1]
file=sys.argv[2]
module = cst.parse_module(open(file).read()).visit(MetadataWriter())
with open(file, "w+") as out:
    out.write(module.code)