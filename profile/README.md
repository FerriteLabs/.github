# Ferrite

[![CI](https://github.com/ferritelabs/ferrite/actions/workflows/ci.yml/badge.svg)](https://github.com/ferritelabs/ferrite/actions/workflows/ci.yml)
[![Redis Compat](https://img.shields.io/badge/Redis_compatibility-~92%25-brightgreen)](https://github.com/ferritelabs/ferrite/blob/main/docs/REDIS_COMPAT.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](https://github.com/ferritelabs/ferrite/blob/main/LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.80%2B-orange)](https://www.rust-lang.org/)
[![Docs](https://img.shields.io/badge/docs-ferrite.rs-blue)](https://ferrite.rs)

**The speed of memory, the capacity of disk, the economics of cloud.**

Ferrite is a high-performance, tiered-storage key-value store designed as a drop-in Redis replacement. Built in Rust with epoch-based concurrency and io_uring-first persistence.

## Why Ferrite?

| Challenge | Redis | Ferrite |
|-----------|-------|---------|
| Data > RAM | ❌ Eviction or cluster scale-out | ✅ Automatic tiering to disk & cloud |
| Cost at scale | 💰 All data in RAM | 💚 Hot/warm/cold tiers cut memory 5–10× |
| Multi-model queries | 🔌 Separate modules (RedisSearch, RedisJSON) | 🧩 Native: vectors, search, graph, time-series, documents |
| AI/ML workloads | ❌ External vector DB needed | ✅ Built-in vector search, semantic caching, RAG |

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Ferrite Server                  │
│  RESP2/RESP3 · gRPC · HTTP · Memcached protocol │
├─────────┬───────────┬───────────┬───────────────┤
│ Vectors │ Search    │ Graph     │ Time-Series   │
│ CDC     │ Documents │ Streaming │ WASM Plugins  │
├─────────┴───────────┴───────────┴───────────────┤
│              HybridLog Storage Engine            │
│  ┌──────────┐ ┌────────────┐ ┌────────────────┐ │
│  │ 🔥 Hot   │ │ 🟡 Warm    │ │ 🧊 Cold       │ │
│  │ Memory   │ │ mmap       │ │ Disk / S3      │ │
│  └──────────┘ └────────────┘ └────────────────┘ │
│        Epoch-Based Reclamation · io_uring        │
└─────────────────────────────────────────────────┘
```

## Repositories

| Repository | Description | Status |
|-----------|-------------|--------|
| [**ferrite**](https://github.com/ferritelabs/ferrite) | Core database engine (Cargo workspace, 12 crates) | [![CI](https://github.com/ferritelabs/ferrite/actions/workflows/ci.yml/badge.svg)](https://github.com/ferritelabs/ferrite/actions/workflows/ci.yml) |
| [**ferrite-docs**](https://github.com/ferritelabs/ferrite-docs) | Documentation website (Docusaurus) | [![CI](https://github.com/ferritelabs/ferrite-docs/actions/workflows/ci.yml/badge.svg)](https://github.com/ferritelabs/ferrite-docs/actions/workflows/ci.yml) |
| [**ferrite-ops**](https://github.com/ferritelabs/ferrite-ops) | Docker, Helm, Grafana, packaging, scripts | [![CI](https://github.com/ferritelabs/ferrite-ops/actions/workflows/ci.yml/badge.svg)](https://github.com/ferritelabs/ferrite-ops/actions/workflows/ci.yml) |
| [**ferrite-bench**](https://github.com/ferritelabs/ferrite-bench) | Performance benchmarks vs Redis, Dragonfly, KeyDB | [![Nightly](https://github.com/ferritelabs/ferrite-bench/actions/workflows/nightly-bench.yml/badge.svg)](https://github.com/ferritelabs/ferrite-bench/actions/workflows/nightly-bench.yml) |
| [**vscode-ferrite**](https://github.com/ferritelabs/vscode-ferrite) | VS Code extension (FerriteQL, snippets, connection manager) | [![CI](https://github.com/ferritelabs/vscode-ferrite/actions/workflows/ci.yml/badge.svg)](https://github.com/ferritelabs/vscode-ferrite/actions/workflows/ci.yml) |
| [**jetbrains-ferrite**](https://github.com/ferritelabs/jetbrains-ferrite) | JetBrains IDE plugin (IntelliJ, PyCharm, WebStorm, etc.) | [![CI](https://github.com/ferritelabs/jetbrains-ferrite/actions/workflows/ci.yml/badge.svg)](https://github.com/ferritelabs/jetbrains-ferrite/actions/workflows/ci.yml) |
| [**homebrew-tap**](https://github.com/ferritelabs/homebrew-tap) | Homebrew formula for macOS/Linux | [![CI](https://github.com/ferritelabs/homebrew-tap/actions/workflows/ci.yml/badge.svg)](https://github.com/ferritelabs/homebrew-tap/actions/workflows/ci.yml) |

## Quick Start

```bash
# Install via Homebrew
brew tap ferritelabs/ferrite && brew install ferrite

# Or build from source
git clone https://github.com/ferritelabs/ferrite && cd ferrite
cargo build --release && ./target/release/ferrite

# Or use Docker
docker compose up -d
```

```bash
# Connect with any Redis client
redis-cli PING    # PONG
redis-cli SET mykey "Hello, Ferrite!"
redis-cli GET mykey
```

## Key Features

- **Drop-in Redis replacement** — RESP2/RESP3 protocol compatible
- **Tiered storage** — Hot data in memory, warm data on mmap, cold data on disk
- **Multi-model** — Key-value, vectors, full-text search, time-series, graph, documents
- **Built in Rust** — Memory-safe, zero-cost abstractions, fearless concurrency
- **io_uring-first** — Modern Linux I/O with automatic fallback on other platforms

## License

All FerriteLabs repositories are licensed under [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Quick Links

📖 [Documentation](https://ferrite.rs) · 🐛 [Report a Bug](https://github.com/ferritelabs/ferrite/issues/new?template=bug_report.md) · 💡 [Request a Feature](https://github.com/ferritelabs/ferrite/issues/new?template=feature_request.md) · 💬 [Discussions](https://github.com/ferritelabs/ferrite/discussions) · 🔒 [Security Policy](https://github.com/ferritelabs/.github/blob/main/SECURITY.md)
