# Tychons

**Visual identity badges for public cryptographic keys.**

Tychons turns any public key into a deterministic, glanceable visual identity -- a small constellation-style image paired with a two-word checksum phrase. Two badges representing different keys are distinguishable at a glance, giving users a fast, human-friendly way to verify key authenticity without comparing raw fingerprints.

## The Problem

Public key fingerprints are long, opaque strings that humans are bad at comparing. SSH randomart improved on hex dumps, but it is monochrome, offers limited perceptual diversity, and provides no secondary verification channel. Tychons derives multiple independent visual signals from the key -- color, star layout, and checksum words -- so that a mismatch on *any* channel is immediately noticeable.

## What a Badge Contains

Each badge encodes three independent pieces of information derived from the key:

| Channel | What you see | What it encodes |
|---|---|---|
| **Hue** | A dominant color shared by all stars and edges | 4 bytes of key material via BLAKE3 |
| **Constellation** | 6--10 stars of varying size and brightness, connected by edges | 64 bytes of key material (positions, radii, brightness, neighbor counts) |
| **Checksum phrase** | Two words displayed at the bottom of the badge | Two independent 4-byte derivations against a wordlist |

Because each channel is derived from a separate BLAKE3 context, an attacker who matches one channel gains no advantage on the others.

## Quick Start

Tychons requires **Python 3.11+** and two dependencies:

```bash
pip install blake3 Pillow
```

### As a library

```python
from tychons.tychons import Badge

badge = Badge("ssh-rsa AAAAB3NzaC1yc2E...")
badge.save("my_key.png")
print(badge.phrase)  # e.g. "birch · nova"
```

### From the command line

```bash
python src/tychons/tychons.py "ssh-rsa AAAAB3NzaC1yc2E..." badge.png 128
```

### With a BIP-39 wordlist

For maximum entropy (22 bits across the two-word phrase), supply a 2048-word [BIP-39 wordlist](https://github.com/trezor/python-mnemonic/tree/master/src/mnemonic/wordlist):

```python
badge = Badge("ssh-rsa AAAAB3...", lang="en", wordlist_dir="wordlists/")
```

Without a wordlist file, a built-in 64-word fallback list is used. This still produces usable badges but with reduced checksum entropy.

## How It Works

1. The public key bytes are fed into **BLAKE3 in derive-key mode** with four distinct context strings, producing cryptographically independent outputs for hue, star layout, and each checksum word.
2. Star positions, sizes, brightness values, and neighbor counts are unpacked from the derived bytes and placed on a padded canvas.
3. Edges are computed using a nearest-neighbor algorithm based on each star's derived neighbor count.
4. The image is rendered at 2x resolution and downsampled with Lanczos filtering for clean antialiasing, then clipped to a rounded rectangle.

Full details are in the [specification](docs/src/tychons-spec-v0.1.0.md).

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `size` | `128` | Badge width/height in pixels (recommended 64--256) |
| `bg_color` | `(8, 13, 20)` | Background RGB; fixed dark navy by spec |
| `lang` | `None` | BIP-39 language code (`en`, `es`, `ja`, ...) |
| `wordlist_dir` | `wordlists/` | Directory containing `<lang>.txt` files |

## Accessibility

Tychons does not rely on color alone. Users with color vision deficiency can still distinguish badges by constellation shape, star count, star size distribution, and the two-word checksum phrase.

## Security

Tychons is a **human verification aid**, not a cryptographic commitment scheme. It is designed for the common case of confirming a known contact's key -- not for resisting an adversary who can generate arbitrary key pairs searching for visual collisions. In high-security contexts, supplement badge comparison with out-of-band verification of the raw key fingerprint.

With a 2048-word BIP-39 wordlist, the conservative estimate of perceptually distinct badges is approximately **1.3 billion**. The full combinatorial space is around 10^21.

## Documentation

Full project documentation is available at the [Tychons docs site](https://cwlls.github.io/tychons/).

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
