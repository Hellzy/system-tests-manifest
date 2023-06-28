from typing import Optional, List
import libcst as cst
import yaml
import collections


# Set of helpers to generate verbose cst types

def cstContextArg(ctxArg: str, val: str) -> cst.Arg:
    return  cst.Arg(keyword=cst.Attribute(value=cst.Name("context"), attr=cst.Name(ctxArg)), value=cst.SimpleString(f'"{val}"'))

def cstArg(arg: str, val: str) -> cst.Arg:
    return cst.Arg(keyword=cst.Name(value=arg), value=cst.SimpleString(f'"{val}"'))

def cstDecorator(funcName: str, args: List[cst.Arg]) -> cst.Decorator:
    return cst.Decorator(decorator=cst.Call(
        func=cst.Name(value=funcName),
        args=args
    ))

def genReleasedDec(version):
    args = [cst.Arg(keyword=cst.Name(value="golang"), value=cst.SimpleString(f'"{version}"'))]
    return cstDecorator("released", args)

def genIrrelevantDec(map):
    reason = map["reason"]
    args = [cstContextArg("library", "golang"), cstArg("reason", reason)]
    return cst.Decorator(decorator=cst.Call(
        func=cst.Name(value="irrelevant"),
        args=args
    ))

def gen_decorators(yml) -> 'dict[str, list]':
    decs = collections.defaultdict(list)

    for keyDec, decorators in yml.items():
        for map in decorators:
            testName = map["test_name"]
            if keyDec == "released":
                decs[testName].append(genReleasedDec(map["version"]))
            elif keyDec == "irrelevant":
                decs[testName].append(genIrrelevantDec(map))

    return decs

class MetadataWriter(cst.CSTTransformer):
    def __init__(self):
        super().__init__()
        #TODO: store manifest parsed metadata

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node : cst.FunctionDef) -> cst.FunctionDef:
        if original_node.name.value in decs:
            print("True for " + original_node.name.value)
            return updated_node.with_changes(decorators=decs[original_node.name.value])
        return updated_node

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node : cst.ClassDef) -> cst.ClassDef:
        if original_node.name.value in decs:
            return updated_node.with_changes(decorators=decs[original_node.name.value])
        return updated_node


with open("manifest.yaml", "r") as yml_file:
    yml = yaml.safe_load(yml_file)


mapping={key: yml["golang"][key] for key in yml["golang"]}
decs = gen_decorators(mapping)
module = cst.parse_module(open("test_blocking_addresses.py").read()).visit(MetadataWriter())
with open("modified.py", "w+") as out:
    out.write(module.code)