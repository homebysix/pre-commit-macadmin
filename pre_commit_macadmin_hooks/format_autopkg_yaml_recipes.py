#!/usr/bin/python
"""This hook auto-formats AutoPkg YAML recipes."""

import argparse
import io
import re
from typing import List, Optional

import ruamel.yaml
from ruamel.yaml.constructor import DuplicateKeyError

# YAML 1.1 boolean tokens that AutoPkg uses as strings (e.g. 'YES'/'NO').
# Force single quotes so a later load doesn't coerce them to booleans.
_YAML_11_BOOL_RE = re.compile(
    r"^(y|Y|yes|Yes|YES|n|N|no|No|NO"
    r"|true|True|TRUE|false|False|FALSE"
    r"|on|On|ON|off|Off|OFF)$"
)

_DESIRED_TOP_LEVEL_ORDER = (
    "Comment",
    "Description",
    "Identifier",
    "ParentRecipe",
    "MinimumVersion",
    "Input",
    "Process",
    "ParentRecipeTrustInfo",
)

_TOP_LEVEL_TRIGGERS = (
    "Input:",
    "Process:",
    "ParentRecipeTrustInfo:",
    "- Processor:",
)


def _represent_str_bool_safe(representer, data):
    if _YAML_11_BOOL_RE.match(data):
        return representer.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    return representer.represent_scalar("tag:yaml.org,2002:str", data)


def build_yaml() -> ruamel.yaml.YAML:
    """Build a round-trip YAML instance configured for AutoPkg recipes."""
    yaml = ruamel.yaml.YAML(typ="rt")
    yaml.width = float("inf")
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=2, offset=0)
    yaml.representer.add_representer(str, _represent_str_bool_safe)
    return yaml


def _reorder_recipe(recipe) -> None:
    """Reorder a recipe in place for readability."""
    process = recipe.get("Process")
    if process:
        for processor in process:
            if "Comment" in processor:
                processor.move_to_end("Comment")
            if "Arguments" in processor:
                processor.move_to_end("Arguments")

    input_block = recipe.get("Input")
    if input_block is not None and "NAME" in input_block:
        input_block.move_to_end("NAME", last=False)

    for key in _DESIRED_TOP_LEVEL_ORDER:
        if key in recipe:
            recipe.move_to_end(key)


def _insert_section_blank_lines(output: str) -> str:
    """Ensure a single blank line precedes each top-level recipe section."""
    result: List[str] = []
    for line in output.split("\n"):
        if not line.startswith(_TOP_LEVEL_TRIGGERS):
            result.append(line)
            continue

        while result and result[-1] == "":
            result.pop()

        is_first_processor = (
            line.startswith("- Processor:")
            and result
            and result[-1].rstrip() == "Process:"
        )
        if result and not is_first_processor:
            result.append("")
        result.append(line)

    return "\n".join(result)


def tidy_recipe(path: str, yaml: ruamel.yaml.YAML) -> None:
    """Tidy a single AutoPkg YAML recipe in place."""
    with open(path) as in_file:
        original = in_file.read()

    recipe = yaml.load(original)
    if recipe is None:
        return

    _reorder_recipe(recipe)

    buf = io.StringIO()
    yaml.dump(recipe, buf)
    formatted = _insert_section_blank_lines(buf.getvalue())

    # Skip the write so pre-commit doesn't flag the file as modified on a no-op.
    if formatted == original:
        return

    with open(path, "w") as out_file:
        out_file.write(formatted)


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to format.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main process."""
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    yaml = build_yaml()
    retval = 0
    for filename in args.filenames:
        try:
            tidy_recipe(filename, yaml)
        except DuplicateKeyError as err:
            print(f"{filename}: yaml duplicate key: {err}")
            retval = 1
        except ruamel.yaml.YAMLError as err:
            print(f"{filename}: yaml parsing error: {err}")
            retval = 1
        except Exception as err:
            print(f"{filename}: unexpected error: {err}")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
