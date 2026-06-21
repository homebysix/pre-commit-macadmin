#!/usr/bin/env python
"""Generate AutoPkg processor MinimumVersion data from release history."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import io
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

GENERATOR_VERSION = 1
SOURCE_URL = "https://github.com/autopkg/autopkg"
INTRODUCED_KEY = "_introduced_"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "pre_commit_macadmin_hooks"
    / "autopkg_processor_versions.py"
)


@dataclass(frozen=True)
class Release:
    version: str
    ref: str


@dataclass
class ProcessorInfo:
    args: set[str]
    bases: set[str]
    defines_input_variables: bool = False
    lifecycle_introduced: str | None = None


def git(repo: Path, *args: str, check: bool = True) -> str:
    """Run git in repo and return stdout."""

    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed with exit code {result.returncode}:\n"
            f"{result.stderr}"
        )
    return result.stdout


def normalize_tag_version(tag: str) -> tuple[str, Version] | None:
    """Return normalized version text and Version for a bare AutoPkg tag."""

    raw_version = tag
    if raw_version.startswith("v."):
        raw_version = raw_version[2:]
    elif raw_version.startswith("v") and len(raw_version) > 1:
        raw_version = raw_version[1:]

    try:
        parsed = Version(raw_version)
    except InvalidVersion:
        return None
    return str(parsed), parsed


def public_releases(
    autopkg_repo: Path,
    baseline_ref: str | None = None,
    include_prereleases: bool = False,
    require_baseline: bool = True,
) -> list[Release]:
    """Return sorted AutoPkg release refs to scan."""

    releases_by_version: dict[Version, Release] = {}
    for tag in git(autopkg_repo, "tag", "--list").splitlines():
        normalized = normalize_tag_version(tag)
        if normalized is None:
            continue
        version_text, parsed_version = normalized
        if parsed_version.is_prerelease and not include_prereleases:
            continue
        releases_by_version[parsed_version] = Release(version_text, tag)

    baseline_version = Version("0.1.0")
    if baseline_version not in releases_by_version:
        if require_baseline and baseline_ref is None:
            raise ValueError(
                "AutoPkg 0.1.0 tag was not found. Pass --baseline-ref to label "
                "a historical snapshot as 0.1.0."
            )
        if baseline_ref is not None:
            releases_by_version[baseline_version] = Release("0.1.0", baseline_ref)

    return [
        releases_by_version[version]
        for version in sorted(releases_by_version)
        if version >= baseline_version
    ]


def literal_string(value: ast.AST | None) -> str | None:
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    if isinstance(value, ast.Str):
        return value.s
    return None


def ast_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def ast_processor_info(source: str) -> dict[str, ProcessorInfo]:
    """Extract processor info from source with ast when Python 3 can parse it."""

    tree = ast.parse(source)
    processors: dict[str, ProcessorInfo] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name == "Processor":
            continue

        input_variables_seen = False
        args: set[str] = set()
        bases = {base_name for base in node.bases if (base_name := ast_name(base))}
        lifecycle_introduced: str | None = None

        for item in node.body:
            target_name = None
            value = None
            if isinstance(item, ast.Assign):
                value = item.value
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        target_name = target.id
                        break
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                target_name = item.target.id
                value = item.value

            if target_name == "input_variables":
                input_variables_seen = True
                if isinstance(value, ast.Dict):
                    for key in value.keys:
                        key_string = literal_string(key)
                        if key_string is not None:
                            args.add(key_string)
            elif target_name == "lifecycle" and isinstance(value, ast.Dict):
                for key, lifecycle_value in zip(value.keys, value.values):
                    if literal_string(key) == "introduced":
                        lifecycle_introduced = literal_string(lifecycle_value)

        processors[node.name] = ProcessorInfo(
            args,
            bases,
            input_variables_seen,
            lifecycle_introduced,
        )

    return processors


def line_offsets(text: str) -> list[int]:
    offsets = [0]
    total = 0
    for line in text.splitlines(keepends=True):
        total += len(line)
        offsets.append(total)
    return offsets


def position_to_offset(offsets: list[int], position: tuple[int, int]) -> int:
    row, column = position
    return offsets[row - 1] + column


def dict_text_after_assignment(source: str, attr_name: str) -> str | None:
    """Return the literal dict text assigned to attr_name, if one is present."""

    marker = f"{attr_name}"
    attr_index = source.find(marker)
    while attr_index != -1:
        line_start = source.rfind("\n", 0, attr_index) + 1
        prefix = source[line_start:attr_index]
        if prefix.strip() == "":
            equals_index = source.find("=", attr_index + len(marker))
            next_line_index = source.find("\n", attr_index)
            if equals_index != -1 and (
                next_line_index == -1 or equals_index < next_line_index
            ):
                brace_index = source.find("{", equals_index)
                if brace_index != -1:
                    break
        attr_index = source.find(marker, attr_index + len(marker))
    else:
        return None

    dict_source = source[brace_index:]
    offsets = line_offsets(dict_source)
    level = 0
    started = False
    try:
        tokens = tokenize.generate_tokens(io.StringIO(dict_source).readline)
        for token in tokens:
            if token.type != tokenize.OP:
                continue
            if token.string == "{":
                started = True
                level += 1
            elif token.string == "}":
                level -= 1
                if started and level == 0:
                    end = position_to_offset(offsets, token.end)
                    return dict_source[:end]
    except tokenize.TokenError:
        return None
    return None


def string_keys_at_top_dict_level(dict_source: str) -> set[str]:
    """Return string keys from the top level of a dict literal."""

    keys: set[str] = set()
    level = 0
    previous_significant = ""
    try:
        tokens = tokenize.generate_tokens(io.StringIO(dict_source).readline)
        for token in tokens:
            if token.type == tokenize.OP:
                if token.string in "{[(":
                    level += 1
                elif token.string in "}])":
                    level -= 1
                if token.string not in ",\n":
                    previous_significant = token.string
                continue
            if token.type == tokenize.STRING and level == 1:
                try:
                    value = ast.literal_eval(token.string)
                except (SyntaxError, ValueError):
                    continue
                if isinstance(value, str) and previous_significant in {"{", ","}:
                    keys.add(value)
                previous_significant = "STRING"
            elif token.type not in {
                tokenize.COMMENT,
                tokenize.ENCODING,
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
            }:
                previous_significant = token.string
    except tokenize.TokenError:
        return keys
    return keys


def introduced_version_from_lifecycle(dict_source: str) -> str | None:
    """Return lifecycle['introduced'] from a literal dict, if present."""

    try:
        value = ast.literal_eval(dict_source)
    except (SyntaxError, ValueError):
        return None
    if isinstance(value, dict) and isinstance(value.get("introduced"), str):
        return value["introduced"]
    return None


def fallback_processor_info(source: str) -> dict[str, ProcessorInfo]:
    """Extract processor info from simple class blocks when ast cannot parse."""

    processors: dict[str, ProcessorInfo] = {}
    class_offsets: list[tuple[str, set[str], int]] = []
    for match in re.finditer(r"(?m)^class\s+(\w+)(?:\(([^)]*)\))?:", source):
        class_name = match.group(1)
        if class_name == "Processor":
            continue
        bases = {
            base.strip().split(".")[-1]
            for base in (match.group(2) or "").split(",")
            if base.strip()
        }
        class_offsets.append((class_name, bases, match.start()))

    for index, (class_name, bases, start) in enumerate(class_offsets):
        end = (
            class_offsets[index + 1][2]
            if index + 1 < len(class_offsets)
            else len(source)
        )
        block = source[start:end]

        input_variables = dict_text_after_assignment(block, "input_variables")
        lifecycle = dict_text_after_assignment(block, "lifecycle")

        args = (
            string_keys_at_top_dict_level(input_variables) if input_variables else set()
        )
        lifecycle_introduced = (
            introduced_version_from_lifecycle(lifecycle) if lifecycle else None
        )
        processors[class_name] = ProcessorInfo(
            args,
            bases,
            input_variables is not None,
            lifecycle_introduced,
        )

    return processors


def parse_processor_source(source: str) -> dict[str, ProcessorInfo]:
    try:
        return ast_processor_info(source)
    except SyntaxError:
        return fallback_processor_info(source)


def is_core_processor_source_path(path: str) -> bool:
    """Return True for top-level AutoPkg core processor modules."""

    parts = Path(path).parts
    lower_parts = {part.lower() for part in parts}
    if lower_parts & {"test", "tests"}:
        return False
    if parts[-1] == "__init__.py":
        return False

    return any(
        part == "autopkglib" and index == len(parts) - 2
        for index, part in enumerate(parts)
    )


def processor_files_at_ref(autopkg_repo: Path, ref: str) -> dict[str, str]:
    """Return candidate Python source files from a release ref."""

    sources: dict[str, str] = {}
    for path in git(autopkg_repo, "ls-tree", "-r", "--name-only", ref).splitlines():
        if not path.endswith(".py"):
            continue
        if not is_core_processor_source_path(path):
            continue
        source = git(autopkg_repo, "show", f"{ref}:{path}", check=False)
        sources[path] = source
    return sources


def scan_release(autopkg_repo: Path, release: Release) -> dict[str, ProcessorInfo]:
    parsed_classes: dict[str, ProcessorInfo] = {}
    for source in processor_files_at_ref(autopkg_repo, release.ref).values():
        for name, info in parse_processor_source(source).items():
            parsed_classes[name] = info

    processor_names = {
        name
        for name, info in parsed_classes.items()
        if info.defines_input_variables
        or info.lifecycle_introduced
        or "Processor" in info.bases
    }
    while True:
        inherited_processor_names = {
            name
            for name, info in parsed_classes.items()
            if name not in processor_names and info.bases & processor_names
        }
        if not inherited_processor_names:
            break
        processor_names.update(inherited_processor_names)

    processors = {
        name: info for name, info in parsed_classes.items() if name in processor_names
    }
    return processors


def compact_argument_versions(
    proc_min_versions: dict[str, str], proc_arg_min_versions: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    compacted: dict[str, dict[str, str]] = {}
    for proc_name, arg_versions in proc_arg_min_versions.items():
        proc_version = proc_min_versions.get(proc_name)
        if proc_version is None:
            continue
        newer_args = {
            arg: version
            for arg, version in arg_versions.items()
            if Version(version) > Version(proc_version)
        }
        if newer_args:
            compacted[proc_name] = newer_args
    return compacted


def scan_releases(
    autopkg_repo: Path,
    releases: list[Release],
    proc_min_versions: dict[str, str] | None = None,
    proc_arg_min_versions: dict[str, dict[str, str]] | None = None,
) -> tuple[dict[str, str], dict[str, dict[str, str]], list[str]]:
    """Scan releases and return processor versions, argument versions, warnings."""

    proc_min_versions = dict(proc_min_versions or {})
    proc_arg_min_versions = {
        proc: dict(arg_versions)
        for proc, arg_versions in (proc_arg_min_versions or {}).items()
    }
    warnings: list[str] = []
    lifecycle_warnings_seen: set[tuple[str, str, str]] = set()

    for release in releases:
        release_processors = scan_release(autopkg_repo, release)
        for proc_name, info in sorted(release_processors.items()):
            proc_min_versions.setdefault(proc_name, release.version)
            if info.lifecycle_introduced:
                first_seen = proc_min_versions[proc_name]
                if Version(info.lifecycle_introduced) != Version(first_seen):
                    warning_key = (proc_name, first_seen, info.lifecycle_introduced)
                    if warning_key not in lifecycle_warnings_seen:
                        lifecycle_warnings_seen.add(warning_key)
                        warnings.append(
                            f"{proc_name}: overriding git first-seen {first_seen} "
                            f"with lifecycle introduced {info.lifecycle_introduced}"
                        )
                    proc_min_versions[proc_name] = str(
                        Version(info.lifecycle_introduced)
                    )

            arg_versions = proc_arg_min_versions.setdefault(proc_name, {})
            for arg in sorted(info.args):
                arg_versions.setdefault(arg, release.version)

    return (
        proc_min_versions,
        compact_argument_versions(proc_min_versions, proc_arg_min_versions),
        warnings,
    )


def split_processor_versions(
    processor_versions: dict[str, dict[str, str]],
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    proc_min_versions: dict[str, str] = {}
    proc_arg_min_versions: dict[str, dict[str, str]] = {}
    for proc_name, versions in processor_versions.items():
        introduced_version = versions.get(INTRODUCED_KEY)
        if introduced_version is None:
            continue
        proc_min_versions[proc_name] = introduced_version
        arg_versions = {
            key: version for key, version in versions.items() if key != INTRODUCED_KEY
        }
        if arg_versions:
            proc_arg_min_versions[proc_name] = arg_versions
    return proc_min_versions, proc_arg_min_versions


def load_existing_data(
    output_path: Path,
) -> tuple[dict[str, str], dict[str, dict[str, str]], dict[str, Any]]:
    if not output_path.exists():
        return {}, {}, {}

    spec = importlib.util.spec_from_file_location(
        "_autopkg_processor_versions", output_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {output_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    proc_min_versions, proc_arg_min_versions = split_processor_versions(
        {
            proc: dict(versions)
            for proc, versions in getattr(module, "PROC_VERSIONS", {}).items()
        }
    )

    return (
        proc_min_versions,
        proc_arg_min_versions,
        dict(getattr(module, "GENERATION_METADATA", {})),
    )


def format_processor_versions(
    proc_min_versions: dict[str, str],
    proc_arg_min_versions: dict[str, dict[str, str]],
) -> list[str]:
    lines = ["PROC_VERSIONS = {"]
    for proc_name in sorted(proc_min_versions):
        lines.append(f'    "{proc_name}": {{')
        introduced_version = proc_min_versions[proc_name]
        lines.append(f'        "{INTRODUCED_KEY}": "{introduced_version}",')
        for key in sorted(proc_arg_min_versions.get(proc_name, {})):
            lines.append(f'        "{key}": "{proc_arg_min_versions[proc_name][key]}",')
        lines.append("    },")
    lines.append("}")
    return lines


def format_metadata(metadata: dict[str, Any]) -> list[str]:
    lines = ["GENERATION_METADATA = {"]
    for key in sorted(metadata):
        value = metadata[key]
        if value is None:
            lines.append(f'    "{key}": None,')
        elif isinstance(value, int):
            lines.append(f'    "{key}": {value},')
        else:
            lines.append(f'    "{key}": "{value}",')
    lines.append("}")
    return lines


def render_module(
    proc_min_versions: dict[str, str],
    proc_arg_min_versions: dict[str, dict[str, str]],
    metadata: dict[str, Any],
) -> str:
    lines = [
        "# This file is generated by scripts/generate_autopkg_processor_versions.py.",
        "# Do not edit it by hand.",
        "",
        *format_processor_versions(proc_min_versions, proc_arg_min_versions),
        "",
        *format_metadata(metadata),
        "",
    ]
    return "\n".join(lines)


def generation_mode(args: argparse.Namespace, metadata: dict[str, Any]) -> str:
    if args.full:
        return "full"
    if args.incremental:
        return "incremental"
    if metadata.get("last_walked_version"):
        return "incremental"
    return "full"


def generate(args: argparse.Namespace) -> tuple[str, list[str]]:
    autopkg_repo = Path(args.autopkg_repo).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    existing_proc_versions, existing_arg_versions, existing_metadata = (
        load_existing_data(output_path)
    )
    mode = generation_mode(args, existing_metadata)

    releases = public_releases(
        autopkg_repo,
        baseline_ref=args.baseline_ref,
        include_prereleases=args.include_prereleases,
        require_baseline=(mode == "full"),
    )
    if mode == "incremental":
        last_walked = existing_metadata.get("last_walked_version")
        if not last_walked:
            raise ValueError(
                "Incremental generation requires last_walked_version metadata."
            )
        releases_to_scan = [
            release
            for release in releases
            if Version(release.version) > Version(str(last_walked))
        ]
        proc_versions = existing_proc_versions
        arg_versions = existing_arg_versions
    else:
        releases_to_scan = releases
        proc_versions = {}
        arg_versions = {}

    proc_versions, arg_versions, warnings = scan_releases(
        autopkg_repo,
        releases_to_scan,
        proc_versions,
        arg_versions,
    )

    if releases_to_scan:
        last_release = releases_to_scan[-1]
        last_walked_version = last_release.version
        last_walked_ref = last_release.ref
    else:
        last_walked_version = existing_metadata.get("last_walked_version")
        last_walked_ref = existing_metadata.get("last_walked_ref")

    metadata = {
        "generator_version": GENERATOR_VERSION,
        "last_walked_ref": last_walked_ref,
        "last_walked_version": last_walked_version,
        "source": SOURCE_URL,
    }
    return render_module(proc_versions, arg_versions, metadata), warnings


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--autopkg-repo",
        required=True,
        help="Path to a local AutoPkg Git checkout.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Generated Python module path. Defaults to {DEFAULT_OUTPUT}.",
    )
    parser.add_argument(
        "--baseline-ref",
        help="Ref to label as AutoPkg 0.1.0 when no 0.1.0 tag exists.",
    )
    parser.add_argument(
        "--include-prereleases",
        action="store_true",
        help="Include beta and release-candidate tags.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Rebuild from AutoPkg 0.1.0 instead of appending newer releases.",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Append releases newer than the output file's last_walked_version.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if generated output differs from the output file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if args.full and args.incremental:
        parser.error("--full and --incremental are mutually exclusive")

    output_path = Path(args.output).expanduser().resolve()
    generated, warnings = generate(args)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    existing = output_path.read_text(encoding="utf-8") if output_path.exists() else None
    if args.check:
        if existing != generated:
            print(f"{output_path} is not current.", file=sys.stderr)
            return 1
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generated, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
