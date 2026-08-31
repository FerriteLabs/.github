# Security Policy — FerriteLabs

This is the organization-wide security policy for all repositories under **FerriteLabs**.
Individual repositories may include additional security guidance specific to their scope.

## Scope

This policy covers all repositories in the FerriteLabs organization:

- [.github](https://github.com/ferritelabs/.github) — Organization community health files and profile
- [ferrite](https://github.com/ferritelabs/ferrite) — Core database engine
- [ferrite-docs](https://github.com/ferritelabs/ferrite-docs) — Documentation website
- [ferrite-ops](https://github.com/ferritelabs/ferrite-ops) — Docker, Helm, packaging
- [ferrite-bench](https://github.com/ferritelabs/ferrite-bench) — Performance benchmarks
- [vscode-ferrite](https://github.com/ferritelabs/vscode-ferrite) — VS Code extension
- [jetbrains-ferrite](https://github.com/ferritelabs/jetbrains-ferrite) — JetBrains plugin
- [homebrew-tap](https://github.com/ferritelabs/homebrew-tap) — Homebrew formula

## Reporting a Vulnerability

**DO NOT** open a public GitHub issue for security vulnerabilities.

### GitHub Private Vulnerability Reporting

1. Navigate to the **Security** tab of the affected repository
2. Click **"Report a vulnerability"**
3. Fill out the private disclosure form

GitHub private vulnerability reporting is the only published security intake. If the private reporting option is unavailable on the affected repository, use the [Ferrite private vulnerability report](https://github.com/ferritelabs/ferrite/security/advisories/new) and identify the affected repository. Do not disclose sensitive details in a public issue or discussion.

Private vulnerability reporting is enabled across all eight FerriteLabs repositories as a release prerequisite.

### Response Timeline

| Stage | Timeline |
|-------|----------|
| Acknowledgment | Within 48 hours |
| Initial assessment | Within 5 business days |
| Fix or mitigation plan | Within 15 business days |
| Public disclosure | After fix is released (coordinated with reporter) |

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release (0.x) | ✅ Security patches provided |
| Previous release | ⚠️ Critical issues only |
| Pre-release / dev | ❌ No security guarantees |

After Ferrite reaches v1.0, we will support the current and previous major versions.

## Security Practices

All FerriteLabs repositories follow these practices:

- **Dependency scanning**: Dependabot and `cargo audit` / `cargo deny` on every PR
- **Secret scanning**: Gitleaks runs in CI across all repositories
- **Container scanning**: Trivy scans Docker images for CVEs
- **SBOM generation**: SPDX and CycloneDX SBOMs generated for releases
- **Signed releases**: Cosign keyless signing for container images
- **SLSA provenance**: Supply chain attestation for release artifacts

## Disclosure Policy

We follow coordinated disclosure:

1. Reporter submits a vulnerability through GitHub private vulnerability reporting
2. We acknowledge and begin assessment
3. We develop and test a fix
4. We release the fix and publish a security advisory
5. Reporter is credited (unless they prefer anonymity)

We will never take legal action against security researchers who follow responsible disclosure.

## Contact

- **Security reports**: Use **Report a vulnerability** on the affected repository's **Security** tab
- **General questions only**: [GitHub Discussions](https://github.com/ferritelabs/ferrite/discussions) — never post vulnerability details publicly
