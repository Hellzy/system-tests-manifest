from typing import Optional
import libcst as cst
import yaml
import collections

def gen_decorators(releasedDic) -> 'dict[str, list]':
    decs = collections.defaultdict(list)
    for testName, version in releasedDic.items():
        args = [cst.Arg(keyword=cst.Name(value="golang"), value=cst.SimpleString(f'"{version}"'))]
        dec = cst.Decorator(decorator=cst.Call(
            func=cst.Name(value="released"),
            args=args
        ))
        decs[testName].append(dec)

    return decs

class MetadataWriter(cst.CSTTransformer):
    def __init__(self):
        super().__init__()
        #TODO: store manifest parsed metadata

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node : cst.FunctionDef) -> cst.FunctionDef:
        if not original_node.name.value.startswith("test_"):
            return original_node
        if original_node.name.value in released:
            return updated_node.with_changes(decorators=decs[original_node.name.value])

        return original_node

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node : cst.ClassDef) -> cst.ClassDef:
        if not original_node.name.value.startswith("Test_"):
            return original_node
        return updated_node.with_changes(decorators=decs[original_node.name.value])


with open("manifest.yaml", "r") as yml_file:
    yml = yaml.safe_load(yml_file)


released = {entry["test_name"]: entry["version"] for entry in yml["library"]["released"]}
decs = gen_decorators(released)

module = cst.parse_module(open("test_blocking_addresses.py").read()).visit(MetadataWriter())
with open("modified.py", "w+") as out:
    out.write(module.code)