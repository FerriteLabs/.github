from __future__ import annotations

import unittest
from pathlib import Path

from org_audit.contracts import (
    DEFAULT_GITHUB_BRANCH,
    DEFAULT_RELEASE_BRANCH,
    RELEASE_TAG_PREFIXES,
    VERSION_GROUPS,
    config_keys,
    discover_repositories,
    extract_assignment,
    extract_cargo_version,
    extract_changelog_version,
    extract_formula_version,
    extract_gradle_version,
    extract_json_version,
    newest_release_tag,
    newest_repository_release_tag,
    parse_version,
    release_alignment_errors,
    release_collision_errors,
    repository_inventory_errors,
    render_markdown,
)


def grouped_versions(
    ferrite_version: str = "0.5.0",
    ide_version: str = "1.4.0",
) -> dict[str, str]:
    versions = {
        surface: ferrite_version for surface in VERSION_GROUPS["ferrite"]
    }
    versions.update({surface: ide_version for surface in VERSION_GROUPS["ide"]})
    return versions


class FakeRoot:
    def __init__(self, names: list[str]) -> None:
        self.names = names

    def iterdir(self) -> list[Path]:
        return [Path("/workspace") / name for name in self.names]


class ContractAuditTests(unittest.TestCase):
    def test_public_org_files_do_not_publish_unverified_domains(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        forbidden = (
            "@" + "ferritelabs.dev",
            "ferrite" + ".dev",
            "ferrite" + ".rs",
        )
        offenders: list[str] = []
        for path in repository.rglob("*"):
            if ".git" in path.parts or not path.is_file():
                continue
            if path.suffix.lower() not in {".md", ".yml", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for value in forbidden:
                if value in text:
                    offenders.append(f"{path.relative_to(repository)}: {value}")
        self.assertEqual(offenders, [])

    def test_defaults_match_coordinated_pre_merge_branches(self) -> None:
        self.assertEqual(DEFAULT_GITHUB_BRANCH, "release/org-readiness")
        self.assertEqual(DEFAULT_RELEASE_BRANCH, "refactor/clean-code-srp")

    def test_discovers_hidden_git_repository(self) -> None:
        repositories = {".github", "ferrite", "ferrite-ops"}
        discovered = discover_repositories(
            FakeRoot(["notes", ".github", "ferrite-ops", "ferrite"]),
            lambda child: child.name in repositories,
        )
        self.assertEqual(discovered, (".github", "ferrite", "ferrite-ops"))

    def test_repository_inventory_uses_explicit_allowlist(self) -> None:
        errors = repository_inventory_errors((".github", "ferrite", "scratch"))
        self.assertIn("unexpected repository in workspace: scratch", errors)
        self.assertIn("missing expected repository: ferrite-ops", errors)

    def test_extracts_workspace_version(self) -> None:
        text = '[workspace.package]\nversion = "0.4.0"\nedition = "2021"\n'
        self.assertEqual(extract_cargo_version(text), "0.4.0")

    def test_extracts_operations_assignment(self) -> None:
        self.assertEqual(
            extract_assignment("FERRITE_VERSION=0.5.0\n", "FERRITE_VERSION"),
            "0.5.0",
        )

    def test_extracts_docs_and_benchmark_changelog_versions(self) -> None:
        for project in ("Ferrite Documentation", "ferrite-bench"):
            text = f"# {project}\n\n## [Unreleased]\n\n## [0.5.0] - 2026-09-02\n"
            self.assertEqual(extract_changelog_version(text), "0.5.0")

    def test_extracts_vscode_and_homebrew_json_versions(self) -> None:
        self.assertEqual(extract_json_version('{"version": "1.4.0"}'), "1.4.0")
        self.assertEqual(extract_json_version('{"version": "0.5.0"}'), "0.5.0")

    def test_extracts_jetbrains_gradle_version(self) -> None:
        text = 'plugins { id("java") }\nversion = "1.4.0"\n'
        self.assertEqual(extract_gradle_version(text), "1.4.0")

    def test_extracts_homebrew_formula_version(self) -> None:
        text = 'url "https://github.com/ferritelabs/ferrite/archive/refs/tags/v0.5.0.tar.gz"\n'
        self.assertEqual(extract_formula_version(text), "0.5.0")

    def test_config_keys_include_commented_examples(self) -> None:
        text = '[server]\nbind = "127.0.0.1"\n# timeout = 10\n# [tls]\n# enabled = false\n'
        self.assertEqual(
            config_keys(text),
            {"server.bind", "server.timeout", "tls.enabled"},
        )

    def test_release_alignment_keeps_ferrite_and_ide_groups_separate(self) -> None:
        versions = grouped_versions()
        data = {"release_versions": versions}
        self.assertEqual(release_alignment_errors(data), [])
        versions["jetbrains"] = "1.3.1"
        self.assertEqual(
            release_alignment_errors(data),
            [
                "ide group jetbrains='1.3.1' does not match "
                "vscode='1.4.0'"
            ],
        )

    def test_newest_release_tag_ignores_unrelated_tags(self) -> None:
        refs = "\n".join(
            (
                "abc refs/tags/v0.4.0",
                "def refs/tags/nightly",
                "ghi refs/tags/v0.5.0-rc.1",
                "jkl refs/tags/v0.4.1",
            )
        )
        self.assertEqual(newest_release_tag(refs), "v0.5.0-rc.1")

    def test_newest_ops_release_tag_uses_canonical_prefix(self) -> None:
        refs = "\n".join(
            (
                "abc refs/tags/v0.4.1",
                "def refs/tags/ferrite-ops-v0.5.0-rc.1",
                "ghi refs/tags/ferrite-ops-v0.5.0",
            )
        )
        self.assertEqual(
            newest_repository_release_tag(
                refs,
                RELEASE_TAG_PREFIXES["ferrite-ops"],
            ),
            "ferrite-ops-v0.5.0",
        )

    def test_ops_release_tags_fall_back_to_legacy_prefix(self) -> None:
        refs = "abc refs/tags/v0.4.1"
        self.assertEqual(
            newest_repository_release_tag(
                refs,
                RELEASE_TAG_PREFIXES["ferrite-ops"],
            ),
            "v0.4.1",
        )

    def test_release_tags_reject_duplicated_prefixes(self) -> None:
        self.assertIsNone(newest_release_tag("abc refs/tags/vv9.0.0"))
        self.assertIsNone(
            newest_repository_release_tag(
                "abc refs/tags/ferrite-ops-vv9.0.0",
                RELEASE_TAG_PREFIXES["ferrite-ops"],
            )
        )

    def test_rejects_invalid_semver_prerelease_identifiers(self) -> None:
        for version in (
            "v1.2.3",
            "1.2.3-01",
            "1.2.3-alpha..1",
            "1.2.3-alpha.",
        ):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    parse_version(version)

    def test_unreleased_mode_checks_all_seven_versioned_repositories(self) -> None:
        versions = grouped_versions("0.4.1", "1.3.1")
        data = {
            "release_versions": versions,
            "remote_release_tags": {
                "ferrite": "v0.4.1",
                "ferrite-docs": "v0.4.1",
                "ferrite-ops": "ferrite-ops-v0.4.1",
                "ferrite-bench": "v0.4.1",
                "vscode-ferrite": "v1.3.1",
                "jetbrains-ferrite": "v1.3.1",
                "homebrew-tap": "v0.4.1",
            },
        }
        errors = release_collision_errors(data, "unreleased")
        self.assertEqual(len(errors), 7)
        for repository in data["remote_release_tags"]:
            self.assertTrue(
                any(error.startswith(f"{repository} ") for error in errors),
                repository,
            )
        data["release_versions"] = grouped_versions("0.5.0", "1.4.0")
        self.assertEqual(release_collision_errors(data, "unreleased"), [])

    def test_tagged_version_must_equal_newest_remote_tag(self) -> None:
        data = {
            "release_versions": grouped_versions("0.4.1", "1.3.1"),
            "remote_release_tags": {"ferrite": "v0.4.1"},
        }
        self.assertEqual(release_collision_errors(data, "tagged"), [])
        data["release_versions"]["ferrite"] = "0.4.2"
        self.assertEqual(
            release_collision_errors(data, "tagged"),
            [
                "ferrite post-release version '0.4.2' must equal "
                "newest remote release tag 'v0.4.1'"
            ],
        )

    def test_primary_chart_package_version_participates_in_alignment(self) -> None:
        versions = grouped_versions()
        versions["ops_ferrite_chart"] = "0.4.1"
        self.assertEqual(
            release_alignment_errors({"release_versions": versions}),
            [
                "ferrite group ops_ferrite_chart='0.4.1' does not match "
                "ferrite='0.5.0'"
            ],
        )

    def test_markdown_surfaces_dirty_repository(self) -> None:
        data = {
            "repository_inventory": {
                "expected": [".github"],
                "discovered": [".github"],
                "errors": [],
            },
            "repositories": [
                {
                    "name": ".github",
                    "branch": "main",
                    "clean": False,
                    "commits": 1,
                    "diffstat": "1 file changed",
                }
            ],
            "release_versions": grouped_versions(),
            "remote_release_tags": {"ferrite": "v0.4.1"},
            "commands": {
                "counts": {"core_parser": 1, "vscode": 1, "jetbrains": 1},
                "vscode_only": [],
                "jetbrains_only": [],
                "vscode_not_in_parser_scan": [],
                "jetbrains_not_in_parser_scan": [],
            },
            "metrics": {
                "emitted_count": 1,
                "referenced_count": 1,
                "ops_without_exact_core_match": [],
            },
            "config": {"shared_count": 1, "core_only": [], "ops_only": []},
        }
        self.assertIn(
            "| `.github` | `main` | **No** |",
            render_markdown(data, "unreleased"),
        )


if __name__ == "__main__":
    unittest.main()
