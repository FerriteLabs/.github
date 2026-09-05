#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${REPOSITORY_DIR}/.." && pwd)"
EVIDENCE_DIR="${ORG_AUDIT_EVIDENCE_DIR:-${SCRIPT_DIR}/evidence}"

cd "$REPOSITORY_DIR"

python3 -m unittest org_audit.test_contracts
python3 -m org_audit.contracts \
  --root "$WORKSPACE_ROOT" \
  --check \
  --json "${EVIDENCE_DIR}/ORG-CONTRACT-REPORT.json" \
  --markdown "${EVIDENCE_DIR}/ORG-CONTRACT-REPORT.md" \
  "$@"
