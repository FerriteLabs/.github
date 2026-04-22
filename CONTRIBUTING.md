# Contributing to FerriteLabs

Thank you for your interest in contributing to the Ferrite ecosystem! This guide covers organization-wide guidelines. Each repository also has its own `CONTRIBUTING.md` with repo-specific details.

## Repositories

| Repository | What to Contribute |
|------------|-------------------|
| [ferrite](https://github.com/ferritelabs/ferrite) | Core engine: commands, storage, protocol, clustering |
| [ferrite-docs](https://github.com/ferritelabs/ferrite-docs) | Documentation, tutorials, API reference |
| [ferrite-ops](https://github.com/ferritelabs/ferrite-ops) | Docker, Helm, Terraform, monitoring |
| [ferrite-bench](https://github.com/ferritelabs/ferrite-bench) | Performance benchmarks |
| [vscode-ferrite](https://github.com/ferritelabs/vscode-ferrite) | VS Code extension |
| [jetbrains-ferrite](https://github.com/ferritelabs/jetbrains-ferrite) | JetBrains IDE plugin |
| [homebrew-tap](https://github.com/ferritelabs/homebrew-tap) | Homebrew formula |

## Getting Started

1. **Find an issue** — Look for issues labeled `good first issue` or `help wanted` in any repository.
2. **Fork & branch** — Fork the repo and create a feature branch from `main`.
3. **Follow repo conventions** — Each repo has its own `CONTRIBUTING.md` with build/test/lint instructions.
4. **Open a PR** — Use the PR template. Reference the issue number if applicable.

## General Guidelines

- **One PR per concern** — Keep pull requests focused on a single change.
- **Write tests** — All code changes should include appropriate tests.
- **Update docs** — If your change affects user-facing behavior, update the relevant documentation in `ferrite-docs`.
- **Follow existing style** — Match the conventions of the codebase you're working in.
- **Sign your commits** — We recommend GPG-signed commits.

## Cross-Repo Changes

Some changes span multiple repositories (e.g., a new command requires updates to `ferrite`, `ferrite-docs`, and potentially the IDE extensions). For cross-repo changes:

1. Start with the core `ferrite` repo PR.
2. Open follow-up PRs in dependent repos, referencing the core PR.
3. Coordinate merging order — core first, then docs/ops, then extensions.

## Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

If you discover a security vulnerability, please report it privately. See [SECURITY.md](SECURITY.md) for details.

## License

All contributions are made under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0). By submitting a PR, you agree to license your contribution under the same terms.
