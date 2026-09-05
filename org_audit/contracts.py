#!/usr/bin/env python3
"""Report FerriteLabs cross-repository release and contract drift."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable


EXPECTED_REPOS = (
    ".github",
    "ferrite",
    "ferrite-docs",
    "ferrite-ops",
    "ferrite-bench",
    "vscode-ferrite",
    "jetbrains-ferrite",
    "homebrew-tap",
)
DEFAULT_GITHUB_BRANCH = "release/org-readiness"
DEFAULT_RELEASE_BRANCH = "refactor/clean-code-srp"
RELEASE_TAG_REPOS = EXPECTED_REPOS[1:]
RELEASE_TAG_PREFIXES = {
    name: (("ferrite-ops-v", "v") if name == "ferrite-ops" else ("v",))
    for name in RELEASE_TAG_REPOS
}
VERSION_GROUPS = {
    "ferrite": (
        "ferrite",
        "ferrite_docs",
        "ferrite_ops",
        "ferrite_bench",
        "homebrew_metadata",
        "homebrew_formula",
        "ops_dockerfile",
        "ops_dockerfile_moonshot",
        "ops_dockerfile_playground",
        "ops_ferrite_chart",
        "ops_ferrite_app",
        "ops_ferrite-sidecar_app",
    ),
    "ide": ("vscode", "jetbrains"),
}
REPOSITORY_VERSION_SURFACES = {
    "ferrite": "ferrite",
    "ferrite-docs": "ferrite_docs",
    "ferrite-ops": "ferrite_ops",
    "ferrite-bench": "ferrite_bench",
    "vscode-ferrite": "vscode",
    "jetbrains-ferrite": "jetbrains",
    "homebrew-tap": "homebrew_metadata",
}
VERSION_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@dataclass
class RepoState:
    name: str
    branch: str
    clean: bool
    commits: int
    diffstat: str


@dataclass(frozen=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()

    def compare(self, other: SemanticVersion) -> int:
        core = (self.major, self.minor, self.patch)
        other_core = (other.major, other.minor, other.patch)
        if core != other_core:
            return (core > other_core) - (core < other_core)
        if not self.prerelease or not other.prerelease:
            return (not self.prerelease) - (not other.prerelease)
        for left, right in zip(self.prerelease, other.prerelease):
            if left == right:
                continue
            left_numeric = left.isdigit()
            right_numeric = right.isdigit()
            if left_numeric and right_numeric:
                return (int(left) > int(right)) - (int(left) < int(right))
            if left_numeric != right_numeric:
                return -1 if left_numeric else 1
            return (left > right) - (left < right)
        return (len(self.prerelease) > len(other.prerelease)) - (
            len(self.prerelease) < len(other.prerelease)
        )


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def committed_text(repo: Path, path: str) -> str:
    return git(repo, "show", f"HEAD:{path}")


def working_text(repo: Path, path: str) -> str:
    return (repo / path).read_text(encoding="utf-8")


def committed_files(repo: Path, prefix: str, suffixes: tuple[str, ...]) -> list[str]:
    entries = git(repo, "ls-tree", "-r", "--name-only", "HEAD", prefix).splitlines()
    return [entry for entry in entries if entry.endswith(suffixes)]


def discover_repositories(
    root: Path,
    is_repository: Callable[[Path], bool] | None = None,
) -> tuple[str, ...]:
    predicate = is_repository or (
        lambda child: child.is_dir() and (child / ".git").exists()
    )
    return tuple(sorted(child.name for child in root.iterdir() if predicate(child)))


def repository_inventory_errors(discovered: Iterable[str]) -> list[str]:
    discovered_set = set(discovered)
    expected_set = set(EXPECTED_REPOS)
    errors = [
        f"missing expected repository: {name}"
        for name in sorted(expected_set - discovered_set)
    ]
    errors.extend(
        f"unexpected repository in workspace: {name}"
        for name in sorted(discovered_set - expected_set)
    )
    return errors


def repo_state(root: Path, name: str) -> RepoState:
    repo = root / name
    branch = git(repo, "branch", "--show-current").strip()
    clean = not git(repo, "status", "--porcelain").strip()
    commits_text = git(
        repo, "rev-list", "--count", "origin/main..HEAD", check=False
    ).strip()
    commits = int(commits_text) if commits_text.isdigit() else 0
    diffstat = (
        git(repo, "diff", "--shortstat", "origin/main...HEAD", check=False).strip()
        or "No changes"
    )
    return RepoState(name, branch, clean, commits, diffstat)


def extract_assignment(text: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}=(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_cargo_version(text: str) -> str | None:
    workspace = re.search(r"\[workspace\.package\](.*?)(?:\n\[|\Z)", text, re.DOTALL)
    if not workspace:
        return None
    match = re.search(r'^version\s*=\s*"([^"]+)"', workspace.group(1), re.MULTILINE)
    return match.group(1) if match else None


def extract_changelog_version(text: str) -> str | None:
    match = re.search(r"^## \[([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)\]", text, re.MULTILINE)
    return match.group(1) if match else None


def extract_json_version(text: str) -> str | None:
    value = json.loads(text).get("version")
    return value if isinstance(value, str) else None


def extract_gradle_version(text: str) -> str | None:
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else None


def extract_formula_version(text: str) -> str | None:
    match = re.search(r"/tags/v([^/]+)\.tar\.gz", text)
    return match.group(1) if match else None


def parse_version(value: str) -> SemanticVersion:
    match = VERSION_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(f"not a supported semantic version: {value!r}")
    prerelease = tuple((match.group("prerelease") or "").split("."))
    if prerelease == ("",):
        prerelease = ()
    for identifier in prerelease:
        if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
            raise ValueError(
                f"not a supported semantic version: {value!r} "
                "(numeric prerelease identifiers cannot contain leading zeroes)"
            )
    return SemanticVersion(
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        prerelease,
    )


def newest_release_tag(refs: str, prefix: str = "v") -> str | None:
    versions: list[tuple[SemanticVersion, str]] = []
    for line in refs.splitlines():
        ref = line.rsplit(maxsplit=1)[-1] if line.strip() else ""
        tag = ref.removeprefix("refs/tags/")
        if not tag.startswith(prefix):
            continue
        try:
            versions.append((parse_version(tag.removeprefix(prefix)), tag))
        except ValueError:
            continue
    if not versions:
        return None
    newest = versions[0]
    for candidate in versions[1:]:
        if candidate[0].compare(newest[0]) > 0:
            newest = candidate
    return newest[1]


def newest_repository_release_tag(
    refs: str,
    prefixes: tuple[str, ...],
) -> str | None:
    for prefix in prefixes:
        newest = newest_release_tag(refs, prefix)
        if newest is not None:
            return newest
    return None


def release_tag_version(repo: str, tag: str) -> SemanticVersion:
    for prefix in RELEASE_TAG_PREFIXES[repo]:
        if tag.startswith(prefix):
            return parse_version(tag.removeprefix(prefix))
    raise ValueError(f"{repo} has an unsupported release tag: {tag!r}")


def remote_release_tags(root: Path) -> tuple[dict[str, str | None], list[str]]:
    newest: dict[str, str | None] = {}
    errors: list[str] = []
    for name in RELEASE_TAG_REPOS:
        repo = root / name
        prefixes = RELEASE_TAG_PREFIXES[name]
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "ls-remote",
                "--tags",
                "--refs",
                "origin",
                *(f"{prefix}*" for prefix in prefixes),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            newest[name] = None
            errors.append(
                f"could not read remote release tags for {name}: "
                f"{result.stderr.strip() or 'git ls-remote failed'}"
            )
            continue
        newest[name] = newest_repository_release_tag(result.stdout, prefixes)
        if newest[name] is None:
            errors.append(f"no semantic release tags found on {name} origin")
    return newest, errors


def release_versions(root: Path) -> dict[str, str | None]:
    ferrite = root / "ferrite"
    docs = root / "ferrite-docs"
    ops = root / "ferrite-ops"
    bench = root / "ferrite-bench"
    vscode = root / "vscode-ferrite"
    jetbrains = root / "jetbrains-ferrite"
    tap = root / "homebrew-tap"

    metadata = working_text(tap, "release-metadata.json")
    formula = working_text(tap, "ferrite.rb")
    active = working_text(ops, "active-release.env")

    versions: dict[str, str | None] = {
        "ferrite": extract_cargo_version(working_text(ferrite, "Cargo.toml")),
        "ferrite_docs": extract_changelog_version(working_text(docs, "CHANGELOG.md")),
        "ferrite_ops": extract_assignment(active, "FERRITE_VERSION"),
        "ferrite_bench": extract_changelog_version(working_text(bench, "CHANGELOG.md")),
        "vscode": extract_json_version(working_text(vscode, "package.json")),
        "jetbrains": extract_gradle_version(
            working_text(jetbrains, "build.gradle.kts")
        ),
        "homebrew_metadata": extract_json_version(metadata),
        "homebrew_formula": extract_formula_version(formula),
    }
    for dockerfile in ("Dockerfile", "Dockerfile.moonshot", "Dockerfile.playground"):
        text = working_text(ops, dockerfile)
        match = re.search(r"^ARG FERRITE_VERSION=(.+)$", text, re.MULTILINE)
        versions[f"ops_{dockerfile.lower().replace('.', '_')}"] = (
            match.group(1).strip() if match else None
        )
    for chart in ("charts/ferrite/Chart.yaml", "charts/ferrite-sidecar/Chart.yaml"):
        text = working_text(ops, chart)
        version_match = re.search(r'^version:\s*"?([^"\s]+)"?', text, re.MULTILINE)
        match = re.search(r'^appVersion:\s*"?([^"\s]+)"?', text, re.MULTILINE)
        if chart == "charts/ferrite/Chart.yaml":
            versions["ops_ferrite_chart"] = (
                version_match.group(1) if version_match else None
            )
        versions[f"ops_{Path(chart).parent.name}_app"] = (
            match.group(1) if match else None
        )
    return versions


def extract_commands(text: str, pattern: str) -> set[str]:
    return {match.upper() for match in re.findall(pattern, text)}


def command_catalogs(root: Path) -> dict[str, set[str]]:
    ferrite = root / "ferrite"
    core: set[str] = set()
    for path in committed_files(ferrite, "src/commands/parser", (".rs",)):
        core.update(
            extract_commands(
                committed_text(ferrite, path),
                r'"([A-Z][A-Z0-9_. ]+)"\s*=>',
            )
        )

    vscode_text = committed_text(root / "vscode-ferrite", "src/ferriteql-completions.ts")
    jetbrains_text = committed_text(
        root / "jetbrains-ferrite",
        "src/main/kotlin/dev/ferrite/jetbrains/language/FerriteQLCompletionContributor.kt",
    )
    return {
        "core_parser": core,
        "vscode": extract_commands(vscode_text, r"cmd:\s*'([A-Z][A-Z0-9_. ]+)'"),
        "jetbrains": extract_commands(jetbrains_text, r'"([A-Z][A-Z0-9_. ]+)"\s+to\s+"'),
    }


def metric_contract(root: Path) -> tuple[set[str], set[str]]:
    ferrite = root / "ferrite"
    ops = root / "ferrite-ops"
    pattern = re.compile(r"\bferrite_[a-zA-Z0-9_:]+")
    emitted: set[str] = set()
    referenced: set[str] = set()

    for prefix in ("crates/ferrite-core/src/metrics", "src"):
        for path in committed_files(ferrite, prefix, (".rs",)):
            emitted.update(pattern.findall(committed_text(ferrite, path)))
    for prefix in ("grafana", "monitoring"):
        for path in committed_files(ops, prefix, (".json", ".yaml", ".yml")):
            referenced.update(pattern.findall(committed_text(ops, path)))
    return emitted, referenced


def config_keys(text: str) -> set[str]:
    section = ""
    keys: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        section_match = re.match(r"^#?\s*\[([^\]]+)\]", line)
        if section_match:
            section = section_match.group(1)
            continue
        key_match = re.match(r"^#?\s*([a-z][a-z0-9_]*)\s*=", line)
        if key_match:
            key = key_match.group(1)
            keys.add(f"{section}.{key}" if section else key)
    return keys


def analyze(root: Path) -> dict:
    discovered = discover_repositories(root)
    states = [
        repo_state(root, name) for name in EXPECTED_REPOS if name in discovered
    ]
    versions = release_versions(root)
    release_tags, tag_errors = remote_release_tags(root)
    catalogs = command_catalogs(root)
    emitted, referenced = metric_contract(root)
    core_config = config_keys(committed_text(root / "ferrite", "ferrite.example.toml"))
    ops_config = config_keys(committed_text(root / "ferrite-ops", "ferrite.example.toml"))

    return {
        "repository_inventory": {
            "expected": list(EXPECTED_REPOS),
            "discovered": list(discovered),
            "errors": repository_inventory_errors(discovered),
        },
        "repositories": [asdict(state) for state in states],
        "release_versions": versions,
        "remote_release_tags": release_tags,
        "remote_tag_errors": tag_errors,
        "commands": {
            "counts": {name: len(values) for name, values in catalogs.items()},
            "vscode_only": sorted(catalogs["vscode"] - catalogs["jetbrains"]),
            "jetbrains_only": sorted(catalogs["jetbrains"] - catalogs["vscode"]),
            "vscode_not_in_parser_scan": sorted(
                catalogs["vscode"] - catalogs["core_parser"]
            ),
            "jetbrains_not_in_parser_scan": sorted(
                catalogs["jetbrains"] - catalogs["core_parser"]
            ),
        },
        "metrics": {
            "emitted_count": len(emitted),
            "referenced_count": len(referenced),
            "ops_without_exact_core_match": sorted(referenced - emitted),
        },
        "config": {
            "core_only": sorted(core_config - ops_config),
            "ops_only": sorted(ops_config - core_config),
            "shared_count": len(core_config & ops_config),
        },
    }


def release_alignment_errors(data: dict) -> list[str]:
    versions = data["release_versions"]
    errors: list[str] = []
    for group, surfaces in VERSION_GROUPS.items():
        canonical_name = surfaces[0]
        canonical = versions.get(canonical_name)
        for name in surfaces[1:]:
            value = versions.get(name)
            if value != canonical:
                errors.append(
                    f"{group} group {name}={value!r} does not match "
                    f"{canonical_name}={canonical!r}"
                )
    return errors


def release_collision_errors(data: dict, mode: str) -> list[str]:
    errors: list[str] = []
    for repo, tag in data.get("remote_release_tags", {}).items():
        surface = REPOSITORY_VERSION_SURFACES[repo]
        candidate = data["release_versions"].get(surface)
        if candidate is None:
            errors.append(f"{repo} proposed version is missing from {surface}")
            continue
        try:
            manifest = parse_version(candidate)
        except ValueError as error:
            errors.append(f"{repo}: {error}")
            continue
        if tag is None:
            continue
        remote = release_tag_version(repo, tag)
        comparison = manifest.compare(remote)
        if mode == "unreleased" and comparison <= 0:
            errors.append(
                f"{repo} proposed unreleased version {candidate!r} must be newer than "
                f"newest remote release tag {tag!r}"
            )
        if mode == "tagged" and comparison != 0:
            errors.append(
                f"{repo} post-release version {candidate!r} must equal "
                f"newest remote release tag {tag!r}"
            )
    return errors


def branch_errors(
    data: dict,
    github_branch: str,
    release_branch: str,
) -> list[str]:
    errors: list[str] = []
    for repo in data["repositories"]:
        expected = github_branch if repo["name"] == ".github" else release_branch
        if repo["branch"] != expected:
            errors.append(
                f"{repo['name']} is on {repo['branch']!r}; expected {expected!r}"
            )
    return errors


def render_markdown(data: dict, mode: str) -> str:
    inventory = data["repository_inventory"]
    lines = [
        "# FerriteLabs Cross-Repository Contract Report",
        "",
        "Generated from proposed worktree versions plus committed `HEAD` command, metrics, and configuration contracts.",
        "",
        "## Repository Inventory",
        "",
        f"- Expected repositories: {len(inventory['expected'])}",
        f"- Discovered repositories: {len(inventory['discovered'])}",
        f"- Inventory errors: {len(inventory['errors'])}",
        "",
        "## Repository State",
        "",
        "| Repository | Branch | Clean | Commits | Diffstat |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for repo in data["repositories"]:
        lines.append(
            f"| `{repo['name']}` | `{repo['branch']}` | "
            f"{'Yes' if repo['clean'] else '**No**'} | {repo['commits']} | {repo['diffstat']} |"
        )

    lines.extend(
        [
            "",
            "## Release Contract",
            "",
            f"Validation mode: `{mode}`.",
            "",
            "| Group | Surface | Version |",
            "| --- | --- | --- |",
        ]
    )
    for group, surfaces in VERSION_GROUPS.items():
        for name in surfaces:
            value = data["release_versions"].get(name)
            lines.append(f"| `{group}` | `{name}` | `{value or 'missing'}` |")
    alignment = release_alignment_errors(data)
    collisions = release_collision_errors(data, mode)
    lines.extend(
        [
            "",
            "**Alignment:** aligned."
            if not alignment
            else "**Alignment:** mismatch — " + "; ".join(alignment),
            "",
            "| Remote | Newest release tag |",
            "| --- | --- |",
        ]
    )
    for name, value in data["remote_release_tags"].items():
        lines.append(f"| `{name}` | `{value or 'missing'}` |")
    lines.extend(
        [
            "",
            "**Tag/version safety:** valid."
            if not collisions
            else "**Tag/version safety:** invalid — " + "; ".join(collisions),
        ]
    )

    commands = data["commands"]
    lines.extend(
        [
            "",
            "## Command Catalogs",
            "",
            f"- Parser scan: {commands['counts']['core_parser']} entries",
            f"- VS Code: {commands['counts']['vscode']} entries",
            f"- JetBrains: {commands['counts']['jetbrains']} entries",
            f"- VS Code-only vs JetBrains: {len(commands['vscode_only'])}",
            f"- JetBrains-only vs VS Code: {len(commands['jetbrains_only'])}",
            "",
            "These differences remain advisory because command maturity, aliases, and IDE UX need a human-owned metadata policy.",
            "",
            "## Metrics Contract",
            "",
            f"- Core metric tokens scanned: {data['metrics']['emitted_count']}",
            f"- Operations metric tokens referenced: {data['metrics']['referenced_count']}",
            f"- Operations references without exact core match: {len(data['metrics']['ops_without_exact_core_match'])}",
            "",
        ]
    )
    for metric in data["metrics"]["ops_without_exact_core_match"]:
        lines.append(f"- `{metric}`")

    lines.extend(
        [
            "",
            "## Configuration Views",
            "",
            f"- Shared keys: {data['config']['shared_count']}",
            f"- Core-only keys: {len(data['config']['core_only'])}",
            f"- Ops-only keys: {len(data['config']['ops_only'])}",
            "",
            "The copies remain separate actor-owned views; a future versioned schema should validate them without making one repository import the other.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="FerriteLabs workspace containing all eight repositories",
    )
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--allow-dirty", action="append", default=[])
    parser.add_argument("--github-branch", default=DEFAULT_GITHUB_BRANCH)
    parser.add_argument("--release-branch", default=DEFAULT_RELEASE_BRANCH)
    parser.add_argument(
        "--mode",
        choices=("unreleased", "tagged"),
        default="unreleased",
        help="Require a newer manifest version before release, or tag equality after release",
    )
    args = parser.parse_args()

    inventory_errors = repository_inventory_errors(discover_repositories(args.root))
    missing_repositories = [
        error for error in inventory_errors if error.startswith("missing expected")
    ]
    if missing_repositories:
        for error in inventory_errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    data = analyze(args.root)
    if args.json:
        write_report(args.json, json.dumps(data, indent=2) + "\n")
    if args.markdown:
        write_report(args.markdown, render_markdown(data, args.mode))

    errors = list(data["repository_inventory"]["errors"])
    errors.extend(data["remote_tag_errors"])
    errors.extend(release_alignment_errors(data))
    errors.extend(release_collision_errors(data, args.mode))
    errors.extend(branch_errors(data, args.github_branch, args.release_branch))

    allowed_dirty = set(args.allow_dirty)
    for repo in data["repositories"]:
        if not repo["clean"] and repo["name"] not in allowed_dirty:
            errors.append(f"{repo['name']} worktree is dirty")

    ide_text = (
        committed_text(args.root / "vscode-ferrite", "src/ferriteql-completions.ts")
        + committed_text(
            args.root / "jetbrains-ferrite",
            "src/main/kotlin/dev/ferrite/jetbrains/language/FerriteQLAnnotator.kt",
        )
    )
    if "VECTOR.DELETE" in ide_text:
        errors.append("IDE catalogs still contain non-canonical VECTOR.DELETE")

    if args.check and errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
