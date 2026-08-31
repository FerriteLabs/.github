# FerriteLabs organization release audit

This dependency-free audit validates the eight repositories in a side-by-side FerriteLabs checkout without changing them. It is the canonical tooling for release-readiness evidence; generated JSON and Markdown reports are outputs, not hand-edited sources of truth.

## Checkout layout

The workspace must contain exactly these immediate Git repository children:

```text
FerriteLabs/
├── .github/
├── ferrite/
├── ferrite-docs/
├── ferrite-ops/
├── ferrite-bench/
├── vscode-ferrite/
├── jetbrains-ferrite/
└── homebrew-tap/
```

Hidden repositories are included in discovery, so `.github` is audited rather than silently skipped.

## Runbook

From the workspace root:

```bash
.github/org_audit/run.sh
```

The default pre-merge branch contract matches the coordinated readiness work: `.github` on `release/org-readiness` and the other seven repositories on `refactor/clean-code-srp`.

```bash
.github/org_audit/run.sh
```

After merging this repository while the seven release PRs remain open, override only its branch:

```bash
.github/org_audit/run.sh --github-branch main
```

After all coordinated PRs merge, override both branch expectations:

```bash
.github/org_audit/run.sh --github-branch main --release-branch main
```

Before a release, the default `--mode unreleased` checks every versioned repository against its own newest semantic `vX.Y.Z` remote tag. Ferrite, documentation, operations, benchmarks, and Homebrew form the Ferrite version group; VS Code and JetBrains form the independently versioned IDE group. Each proposed version must be strictly newer than its repository's newest remote release tag, preventing reuse or rollback without comparing incompatible Ferrite and IDE version lines.

After publishing tags and merging all coordinated branches, use `--mode tagged`; the aligned manifest version must equal each newest relevant remote release tag:

```bash
.github/org_audit/run.sh --mode tagged --github-branch main --release-branch main
```

Use `--allow-dirty REPOSITORY` only for a deliberately modified worktree under active review. Proposed release versions are read from the worktree so the audit can validate pending manifest and changelog changes. Command catalogs, metrics, and configuration contracts continue to use committed `HEAD`.

Reports are written to `org_audit/evidence/` by default and are intentionally ignored. Preserve a report as release evidence in the release system or CI artifact store rather than editing it or treating it as canonical configuration. Set `ORG_AUDIT_EVIDENCE_DIR` to choose another output directory.

## Public promotion prerequisite

Deploy and verify the GitHub Pages fallback at `https://ferritelabs.github.io/ferrite-docs/` before public promotion. Public profile links must continue using the reachable [`ferrite-docs` GitHub repository](https://github.com/ferritelabs/ferrite-docs) until that deployment is live. Advertise a custom domain only after its DNS, hosting, TLS, redirects, and ownership are verified, and do not add a custom funding URL without a working destination.

GitHub private vulnerability reporting must remain enabled on all eight repositories. Verify each repository with `gh api repos/FerriteLabs/<repo>/private-vulnerability-reporting --jq .enabled`.

## Checks

- Exact repository inventory, including the hidden `.github` repository
- Expected branch and clean-worktree state
- Compatible version-group alignment across all seven versioned repositories and their release surfaces
- Per-repository remote tag/version collision safety for unreleased and tagged modes
- Core and IDE command catalogs
- Core-emitted and operations-referenced metrics
- Core and operations configuration views
- Rejection of the non-canonical `VECTOR.DELETE` command spelling

Run only the unit tests with:

```bash
cd .github
python3 -m unittest org_audit.test_contracts
```
