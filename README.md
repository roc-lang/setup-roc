# Setup Roc

A GitHub Action to download and setup the Roc compiler for Linux x86_64.

## Usage

Add this step to your CI workflow:

```yaml
TODO
```

## Platform Support

This action currently supports:
- **OS**: Linux
- **Architecture**: x86_64

## What it does

1. Downloads the Roc compiler (`roc-linux_x86_64-alpha4-rolling.tar.gz`) from the official releases
2. Verifies the SHA256 checksum to ensure file integrity
3. Extracts the compiler
4. Adds the Roc executable to the PATH

## Security

The action verifies the SHA256 checksum of the downloaded file to ensure it hasn't been tampered with. If the checksum doesn't match, the action will fail.
