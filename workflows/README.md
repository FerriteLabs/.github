# FerriteLabs org-level workflows

This directory holds workflows that live in the `ferritelabs/.github` repository
and span **multiple** Ferrite repos.

| Workflow | Trigger | Purpose |
|---|---|---|
| [`release-orchestration.yml`](release-orchestration.yml) | Manual (`workflow_dispatch`) or `repository_dispatch` of type `ferrite-released` | Coordinates a Ferrite release across `ferrite-ops`, `ferrite-docs`, `homebrew-tap` (required) and the IDE plugins (optional). |

## Release-orchestration usage

### Manual trigger

```bash
gh workflow run release-orchestration.yml \
  --repo ferritelabs/.github \
  --field version=v0.4.0 \
  --field include_optional=true \
  --field dry_run=false
```

### Automatic trigger

`ferrite/.github/workflows/release.yml` should send a repository dispatch when
a release tag is published:

```yaml
- name: Notify org orchestrator
  uses: peter-evans/repository-dispatch@v3
  with:
    token: ${{ secrets.ORG_RELEASE_PAT }}
    repository: ferritelabs/.github
    event-type: ferrite-released
    client-payload: |
      { "version": "${{ github.ref_name }}" }
```

## Required secret

`ORG_RELEASE_PAT` — a fine-grained PAT (or GitHub App installation token) with
`actions: write` on every downstream repo. The default `GITHUB_TOKEN` cannot
dispatch workflows in another repository.

## Downstream contract

Each downstream repo participating in orchestration must provide a workflow
file `.github/workflows/version-bump.yml` that:

1. Accepts a string input named `version` (e.g. `v0.4.0`).
2. Performs the per-repo bump (Dockerfile, Helm chart, Homebrew formula, etc.).
3. Opens a PR (or commits directly on a release branch).

The orchestrator does not require any specific PR strategy; it only triggers
the workflow and surfaces the dispatch result in its job summary.
