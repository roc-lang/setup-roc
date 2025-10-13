[![Roc-Lang][roc_badge]][roc_link]

[roc_badge]: https://img.shields.io/endpoint?url=https%3A%2F%2Fpastebin.com%2Fraw%2FcFzuCCd7
[roc_link]: https://github.com/roc-lang/roc

# Setup Roc

A GitHub Action to download and setup the Roc compiler for Linux and macOS.

## Usage

Add this step to your CI workflow:

### Using Major Releases

```yaml
- uses: roc-lang/setup-roc@e2e4452c2bfb0380daadefdb23b989bc9748c63b
  with:
    version: alpha4-rolling
```
> Note: we recommend using this @commit-sha way to specify the version. This makes sure that the included alpha4 release sha256 hashes can not be altered if a github account with access to this repo is hacked.  

### Using Nightly Releases

```yaml
- uses: roc-lang/setup-roc@e2e4452c2bfb0380daadefdb23b989bc9748c63b
  with:
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

## What it does

1. Detects your operating system and architecture
2. Downloads the appropriate Roc compiler release for your platform
3. Verifies the SHA256 checksum to ensure file integrity (skipped for nightly releases)
4. Extracts the compiler
5. Adds the Roc executable to the PATH

## Security

For major releases, the action verifies the SHA256 checksum of the downloaded file to ensure it hasn't been tampered with. If the checksum doesn't match, the action will fail.

For nightly releases, SHA256 verification is skipped since the files are updated regularly.
