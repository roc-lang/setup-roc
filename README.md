# Setup Roc

A GitHub Action to download and setup the Roc compiler for Linux and macOS.

## Usage

Add this step to your CI workflow:

```yaml
TODO
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
3. Verifies the SHA256 checksum to ensure file integrity
4. Extracts the compiler
5. Adds the Roc executable to the PATH

## Security

The action verifies the SHA256 checksum of the downloaded file to ensure it hasn't been tampered with. If the checksum doesn't match, the action will fail.
