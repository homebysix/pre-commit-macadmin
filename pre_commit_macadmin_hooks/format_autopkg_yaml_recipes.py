#!/usr/bin/python
"""This hook auto-formats AutoPkg YAML recipes."""

import argparse
import io
import re

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


def _insert_section_blank_lines(
    output: str, blank_line_before_processor: bool = True
) -> str:
    """Ensure a single blank line precedes each top-level recipe section.

    When blank_line_before_processor is False, "- Processor:" lines are left
    untouched (no blank line inserted before them), which keeps a comment tight
    against the processor it documents. Use this when a separate hook manages
    blank lines between processors.
    """
    triggers = _TOP_LEVEL_TRIGGERS
    if not blank_line_before_processor:
        triggers = tuple(t for t in triggers if t != "- Processor:")

    result: list[str] = []
    for line in output.split("\n"):
        if not line.startswith(triggers):
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


def _realign_comments(output: str) -> str:
    """Reindent comment-only lines to match the surrounding content.

    ruamel.yaml round-trips comments at their original absolute column, so a
    comment does not move when the structural indentation around it changes
    (most visibly on Process list items, which are re-emitted with the dash at
    column 0). Reindent each comment-only line to the indentation of the next
    content line, falling back to the previous content line for trailing
    comments at the end of a block. Inline (trailing) comments are untouched
    because they are not comment-only lines.
    """

    def _indent_of(text: str) -> int:
        return len(text) - len(text.lstrip(" "))

    def _is_comment(text: str) -> bool:
        return text.lstrip(" ").startswith("#")

    lines = output.split("\n")
    result = list(lines)
    for idx, line in enumerate(lines):
        if not _is_comment(line):
            continue
        target = next(
            (
                _indent_of(nxt)
                for nxt in lines[idx + 1 :]
                if nxt.strip() and not _is_comment(nxt)
            ),
            None,
        )
        if target is None:
            target = next(
                (
                    _indent_of(prev)
                    for prev in reversed(result[:idx])
                    if prev.strip() and not _is_comment(prev)
                ),
                None,
            )
        if target is not None:
            result[idx] = " " * target + line.lstrip(" ")

    return "\n".join(result)


def tidy_recipe(
    path: str, yaml: ruamel.yaml.YAML, blank_line_before_processor: bool = True
) -> None:
    """Tidy a single AutoPkg YAML recipe in place."""
    with open(path) as in_file:
        original = in_file.read()

    recipe = yaml.load(original)
    if recipe is None:
        return

    _reorder_recipe(recipe)

    buf = io.StringIO()
    yaml.dump(recipe, buf)
    formatted = _insert_section_blank_lines(
        buf.getvalue(), blank_line_before_processor=blank_line_before_processor
    )
    formatted = _realign_comments(formatted)

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
    parser.add_argument(
        "--no-blank-line-before-processor",
        action="store_true",
        help=(
            "Do not insert a blank line before each '- Processor:' entry. "
            "Useful when a separate hook manages spacing between processors; "
            "also keeps comments tight against the processor they document."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main process."""
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    yaml = build_yaml()
    retval = 0
    for filename in args.filenames:
        try:
            tidy_recipe(
                filename,
                yaml,
                blank_line_before_processor=not args.no_blank_line_before_processor,
            )
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
