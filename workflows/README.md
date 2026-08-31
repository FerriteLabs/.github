# FerriteLabs org-level workflows

The `.github` repository does not orchestrate releases or version bumps.

`ferrite-ops` is the sole cross-repository release and version orchestrator. It receives the canonical `ferrite-release` event emitted by Ferrite and coordinates downstream release notifications from its own workflows.

The former duplicate `release-orchestration.yml` in this repository was removed because it listened for the wrong event, targeted incorrect branches, and depended on version-bump workflows that do not exist.

If an `ORG_RELEASE_PAT` secret was created for the removed workflow, an organization administrator must revoke it in GitHub and remove any corresponding secret configuration. Secret revocation is an out-of-band administrative action and must not be performed or documented with credential values in this repository.
