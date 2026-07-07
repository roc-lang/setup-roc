[![Roc-Lang][roc_badge]][roc_link]

[roc_badge]: https://img.shields.io/endpoint?url=https%3A%2F%2Fpastebin.com%2Fraw%2FcFzuCCd7
[roc_link]: https://github.com/roc-lang/roc

# Setup Roc

A GitHub Action to download and setup the Roc compiler for Linux and macOS.

## Usage

Add this step to your CI workflow:

### For New Compiler Nightly Releases

```yaml
- uses: roc-lang/setup-roc@cbe782d6f165b89c87d99f50a59ac4f5f73b4427
  with:
    version: nightly-new-compiler
    nightly-tag: nightly-2026-June-27-127861d # remove nightly-tag to just get the latest one
```

### For Old Major Releases

```yaml
- uses: roc-lang/setup-roc@cbe782d6f165b89c87d99f50a59ac4f5f73b4427
  with:
    version: alpha4-rolling
```
> Note: we recommend using this @commit-sha way to specify the setup-roc version. This makes sure that the alpha4 release can not be altered if one of our github accounts is hacked.  

### For Old Nightly Releases

```yaml
- uses: roc-lang/setup-roc@cbe782d6f165b89c87d99f50a59ac4f5f73b4427
  with:
    # Note: nightly hashes are not verified because they are updated regularly.
    version: nightly
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
3. Verifies the SHA256 checksum to ensure file integrity (skipped for nightly releases)
4. Extracts the compiler
5. Adds the Roc executable to the PATH

For new-compiler nightlies that include glue support, this action also exports:

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
    version: nightly-new-compiler

- run: roc glue "$ROC_RUST_GLUE" ./platform/main.roc --output-dir ./platform
```

Pin to a `setup-roc` commit that includes glue support; older pinned commits do
not export these variables.

## Security

For major releases, the action verifies the SHA256 checksum of the downloaded file to ensure it hasn't been tampered with. If the checksum doesn't match, the action will fail.

For nightly releases, SHA256 verification is skipped because the files are updated regularly.
