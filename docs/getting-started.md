---
layout: default
title: Getting Started
nav_order: 4
---

# Getting Started

## Requirements

- **Python 3.13** or later
- **blake3** -- BLAKE3 hashing library
- **Pillow** -- image rendering

## Installation

Tychons is not yet published to PyPI. Install from source:

```bash
git clone https://github.com/cwlls/tychons.git
cd tychons
pip install blake3 Pillow
```

If you use [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Generate a Badge

### Python API

```python
from tychons.tychons import Badge

# Create a badge from any public key string
badge = Badge("ssh-rsa AAAAB3NzaC1yc2E...")

# Save to a file
badge.save("my_key.png")

# Get the checksum phrase
print(badge.phrase)  # e.g. "birch · nova"

# Access the PIL Image object directly
img = badge.image
```

### Command Line

```bash
python src/tychons/tychons.py "ssh-rsa AAAAB3NzaC1yc2E..." badge.png 128
```

Arguments:

| Position | Description | Default |
|---|---|---|
| 1 | Public key string (required) | -- |
| 2 | Output file path | `badge.png` |
| 3 | Badge size in pixels | `128` |

## Options

The `Badge` constructor accepts several parameters:

```python
badge = Badge(
    public_key="ssh-rsa AAAAB3...",
    size=128,                      # Image size in pixels (64-256 recommended)
    bg_color=(8, 13, 20),          # Background RGB (dark navy by default)
    lang="en",                     # BIP-39 language code
    wordlist_dir="wordlists/",     # Directory containing wordlist files
)
```

### Size

The default is 128x128 pixels. The recommended range is 64--256. Badges are rendered at 2x internally and downsampled, so they look clean at any size in this range.

### Language and Wordlists

By default, Tychons uses a built-in 64-word fallback list. For better entropy, provide a BIP-39 wordlist:

1. Download a wordlist from the [Trezor BIP-39 repository](https://github.com/trezor/python-mnemonic/tree/master/src/mnemonic/wordlist).
2. Place it in a `wordlists/` directory as `<lang>.txt` (e.g., `wordlists/en.txt`).
3. Pass `lang="en"` when creating the badge.

See [Wordlists and Languages]({% link wordlists.md %}) for more detail.

## What You Get

The `Badge` object provides:

| Property / Method | Description |
|---|---|
| `badge.words` | Tuple of the two checksum words |
| `badge.phrase` | Formatted string, e.g. `"birch · nova"` |
| `badge.image` | PIL `Image` object (RGBA) |
| `badge.save(path)` | Save to a file (PNG by default) |
| `badge.show()` | Open in the system image viewer |

## BLAKE3 Fallback

If the `blake3` package is not installed, the implementation falls back to HMAC-SHA256. This produces different badges than BLAKE3 and is not interoperable with BLAKE3-based implementations. Install `blake3` for spec-conformant output.
