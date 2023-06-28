import pathlib
from typing import Dict, Optional, List, TypedDict, cast, overload
import typing
import libcst as cst
import yaml
import collections

import argparse
from copy import deepcopy
from ast import literal_eval
from typing import Union

import libcst as cst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor


class TestDeclaration(TypedDict):
    name: str
    version: str
    reason: str


class TracerManifest(TypedDict):
    released: Optional[List[TestDeclaration]]
    irrelevant: Optional[List[TestDeclaration]]
    bug: Optional[List[TestDeclaration]]

    tracer: str


# Set of helpers to generate verbose cst types
def context_arg(ctxArg: str, val: str) -> cst.Arg:
    return cst.Arg(
        keyword=cst.Attribute(value=cst.Name("context"), attr=cst.Name(ctxArg)),
        value=cst.SimpleString(val),
    )


def arg(arg: str, val: str) -> cst.Arg:
    return cst.Arg(keyword=cst.Name(value=arg), value=cst.SimpleString(val))


def decorator(funcName: str, args: List[cst.Arg]) -> cst.Decorator:
    return cst.Decorator(decorator=cst.Call(func=cst.Name(value=funcName), args=args))


def released_decorator(version) -> cst.Decorator:
    args = [cst.Arg(keyword=cst.Name(value="golang"), value=cst.SimpleString(version))]
    return decorator("released", args)


def genIrrelevantDec(map):
    reason = map["reason"]
    args = [context_arg("library", "golang"), arg("reason", reason)]
    return cst.Decorator(
        decorator=cst.Call(func=cst.Name(value="irrelevant"), args=args)
    )


def gen_decorators(yml) -> Dict[str, list]:
    decs = collections.defaultdict(list)

    for keyDec, decorators in yml.items():
        for map in decorators:
            testName = map["test_name"]
            if keyDec == "released":
                decs[testName].append(released_decorator(map["version"]))
            elif keyDec == "irrelevant":
                decs[testName].append(genIrrelevantDec(map))

    return decs


class TestNameStack:
    def __init__(self) -> None:
        self.__stack = []

    def push(self, name: str):
        self.__stack.append(name)

    def pop(self):
        self.__stack.pop()

    def fullname(self) -> str:
        return ".".join(*self.__stack)


class ConvertConstantCommand(VisitorBasedCodemodCommand):
    DESCRIPTION: str = "Update system-tests test files with the relevant decorator"
    test_name_stack: TestNameStack
    context: CodemodContext
    manifest: TracerManifest

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        arg_parser.add_argument(
            "--manifest",
            dest="manifest_path",
            metavar="STRING",
            help="Path to the manifest file",
            type=pathlib.Path,
            required=True,
        )

    @overload
    def __init__(self, context: CodemodContext, manifest_path: pathlib.Path) -> None:
        super().__init__(context)

        self.test_name_stack = TestNameStack()
        self.context = context
        with open(manifest_path) as fp:
            self.manifest = cast(TracerManifest, yaml.load(fp, yaml.CLoader))

    @overload
    def visit_Module(self, _: cst.Module):
        self.test_name_stack.push(self.context.full_module_name)

    @overload
    def visit_ClassDef(self, node: cst.ClassDef):
        self.test_name_stack.push(node.name)

    @overload
    def visit_FunctionDef(self, node: cst.FunctionDef):
        self.test_name_stack.push(node.name)

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        return updated_node.with_changes(
            decorators=self.update_decorators(updated_node.decorators)
        )

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        return updated_node.with_changes(
            decorators=self.update_decorators(updated_node.decorators)
        )

    @overload
    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        # TODO: Add imports properly
        # AddImportsVisitor.add_needed_import(
        #    self.context,
        #    "utils.constants",
        #    self.constant,
        # )
        self.test_name_stack.pop()
        return updated_node

    def update_decorators(self, decorators: List[cst.Decorator]) -> List[cst.Decorator]:
        # Sanitize our list of decorators with only functions
        decorator_funcs = [
            cast(cst.Call, dec.decorator)
            for dec in decorators
            if isinstance(dec.decorator, cst.Call)
        ]
        maybe_released_dec = next(
            (dec for dec in decorators if dec.func == "released"), None
        )
        if not maybe_released_dec:
            decorators.append(self.build_released())
        else:
            self.update_released(maybe_released_dec)

    def find_released(self, decorators: List[cst.Call]) -> Optional[cst.Call]:
        return any(dec for dec in decorators if dec.func)

    def build_released(self) -> cst.Decorator:
        pass

    def update_released(self, call: cst.Call):
        pass


"""class MetadataWriter(cst.CSTTransformer):
    def __init__(self):
        super().__init__()
        # TODO: store manifest parsed metadata

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        if original_node.name.value in decs:
            return updated_node.with_changes(decorators=decs[original_node.name.value])
        return updated_node

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        if original_node.name.value in decs:
            return updated_node.with_changes(decorators=decs[original_node.name.value])
        return updated_node


with open("manifest.yaml", "r") as yml_file:
    yml = yaml.safe_load(yml_file)

mapping = {key: yml["golang"][key] for key in yml["golang"]}
decs = gen_decorators(mapping)
module = cst.parse_module(open("test_blocking_addresses.py").read()).visit(
    MetadataWriter()
)
with open("modified.py", "w+") as out:
    out.write(module.code)"""
