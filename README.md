[![Roc-Lang][roc_badge]][roc_link]

[roc_badge]: https://img.shields.io/endpoint?url=https%3A%2F%2Fpastebin.com%2Fraw%2FcFzuCCd7
[roc_link]: https://github.com/roc-lang/roc

# Setup Roc

A GitHub Action to download and setup the Roc compiler for Linux, macOS and Windows.

## Usage

Add this step to your CI workflow:

Recommended setup, which also caches Roc's build and `roc test` results between runs (see [Caching](#caching)):

```yaml
on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: '0 18 * * *' # Optional: run once a day to keep the main branch cache warm. Adjust this based on how active your project is.

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3

      - id: roc
        uses: roc-lang/setup-roc@<commit-sha-with-cache-support>
        with:
          version: nightly
          nightly-tag: nightly-2026-June-27-127861d # remove nightly-tag to just get the latest one
          # cache-key-suffix: ${{ matrix.os }} # needed when matrix jobs share a name

      - run: roc test main.roc

      # Also save the cache when the job fails, so tests that passed stay cached.
      - uses: actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
        if: always() && steps.roc.outputs.cache-key != ''
        with:
          path: ${{ steps.roc.outputs.cache-path }}
          key: ${{ steps.roc.outputs.cache-key }}
```

## Platform Support

This action supports the following platforms:

| OS | Architecture | Status |
|----|--------------|--------|
| Linux | x86_64 | ✅ |
| Linux | arm64 | ✅ |
| macOS | x86_64 (Intel) | ✅ |
| macOS | arm64 (Apple Silicon) | ✅ |
| Windows | x86_64 | ✅ |
| Windows | arm64 | ❌ |

Windows arm64 can be made available again with the next zig release (after 0.16.0).

## What it does

1. Detects your operating system and architecture
2. Downloads the appropriate Roc compiler release for your platform
3. Extracts the compiler
4. Adds the Roc executable to the PATH
5. Restores and saves the Roc cache

For nightlies that include glue support, this action also exports:

| Environment variable | Description |
| --- | --- |
| `ROC_GLUE_DIR` | Directory containing generated glue specs for the installed Roc version |
| `ROC_RUST_GLUE` | Rust glue spec path |
| `ROC_ZIG_GLUE` | Zig glue spec path |
| `ROC_C_GLUE` | C glue spec path |
| `ROC_GLUE_PLATFORM_URL` | URL of the matching glue platform package |

Example:

```yaml
- uses: roc-lang/setup-roc@<commit-sha-with-glue-support>
  with:
    version: nightly

- run: roc glue "$ROC_RUST_GLUE" ./platform/main.roc --output-dir ./platform
```

Pin to a `setup-roc` commit that includes glue support; older pinned commits do
not export these variables.

## Caching

The action restores the Roc cache at the start of the job and saves it when the job succeeds (using [actions/cache](https://github.com/actions/cache)). Cached `roc test` results are part of that cache, so unchanged tests are not run again; the output shows `(cached)`.

- The cache lives in `$RUNNER_TEMP/roc-cache`, the action sets `ROC_CACHE_DIR` to this path. A `ROC_CACHE_DIR` you set yourself is respected.
- Each OS, architecture and job name gets its own cache. A run restores the newest cache from the same Roc nightly, or else from any other nightly: Roc keys its entries by the compiler's content, so entries from a different compiler are ignored, while a nightly with an unchanged compiler reuses them. Add `cache-key-suffix` when jobs share a name, for example matrix jobs:

```yaml
- uses: roc-lang/setup-roc@<commit-sha-with-cache-support>
  with:
    version: nightly
    cache-key-suffix: ${{ matrix.os }}
```

- The `cache-hit` output is `true` when the cache was restored with an exact key match.
- Set `cache: false` to disable caching.

The cache is saved automatically when the job succeeds. The recommended setup at the top adds an `actions/cache/save` step with `if: always()` to also save it when the job fails, so tests that passed stay cached for the next run. It uses the `cache-path` and `cache-key` outputs.

When the job succeeds, the automatic save finds this key already reserved and does nothing.

### Warm the cache on your default branch

GitHub only lets a run restore caches from its own branch, its base branch and the default branch, and a fork PR cannot write to the default branch's caches. A PR's first run is therefore cold unless a run on the default branch has saved a cache. Run your Roc workflow on the default branch too, and on a schedule, as in the recommended setup at the top, so the cache on the default branch follows the latest nightly.

Matrix jobs need a distinct `cache-key-suffix` so that the entries saved on the default branch match the same jobs on PR branches. GitHub deletes caches unused for 7 days and evicts the least recently used ones when a repository exceeds 10 GB.

## Security

Downloaded nightlies are not checksum-verified, because they are updated regularly. To get a fixed, immutable release, set `nightly-tag`. Pin the action itself to a commit sha too, so the action code cannot be altered if one of our github accounts is hacked.
