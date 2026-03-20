---
layout: default
title: Wordlists and Languages
nav_order: 5
---

# Wordlists and Languages

The two-word checksum phrase at the bottom of every Tychons is drawn from a wordlist. The choice of wordlist affects the entropy of the phrase and the language in which it is displayed.

## How Checksum Words Work

Two independent BLAKE3 derivations produce two 32-bit integers. Each integer is reduced modulo the wordlist length to select a word. The two words are displayed separated by an interpunct:

```
maple · frost
```

Because the derivations use separate context strings, the two words are cryptographically independent. Knowing one word gives no information about the other.

## Wordlist Entropy

The entropy of the checksum phrase depends directly on the wordlist size:

| Wordlist size | Bits per word | Bits for two words | Possible phrases |
|---|---|---|---|
| 64 (built-in fallback) | 6 | 12 | 4,096 |
| 2048 (BIP-39) | 11 | 22 | 4,194,304 |

With the full BIP-39 list, the checksum phrase alone distinguishes over 4 million keys. Combined with the visual channels (hue, constellation layout), the total discriminating power is much higher.

## Using BIP-39 Wordlists

BIP-39 is a Bitcoin standard that defines 2048-word lists in multiple languages. Tychons adopts these lists because they are widely available, carefully curated, and standardized.

### Where to Get Them

The canonical source is the Trezor project:
[github.com/trezor/python-mnemonic/tree/master/src/mnemonic/wordlist](https://github.com/trezor/python-mnemonic/tree/master/src/mnemonic/wordlist)

Available languages include English, Spanish, French, Italian, Portuguese, Czech, Japanese, Korean, Chinese (simplified and traditional), and others.

### File Format

Wordlist files are plain text, UTF-8 encoded, one word per line:

```
abandon
ability
able
about
...
```

Lines beginning with `#` and blank lines are ignored. The file should contain exactly 2048 words for a standard BIP-39 list, though Tychons will accept lists of other lengths.

### Directory Layout

Place wordlist files in a directory with filenames matching the language code:

```
wordlists/
    en.txt       # English
    es.txt       # Spanish
    ja.txt       # Japanese
    zh-hans.txt  # Chinese (Simplified)
```

Then pass the language code and directory when creating a badge:

```python
badge = Badge("ssh-rsa AAAAB3...", lang="en", wordlist_dir="wordlists/")
badge = Badge("ssh-rsa AAAAB3...", lang="es", wordlist_dir="wordlists/")
```

## The Built-in Fallback List

When no language is specified, Tychons uses a hardcoded 64-word English list:

> apple, birch, cedar, dusk, ember, frost, grove, haven, iris, jade, kelp, lunar, maple, nova, ocean, pine, quartz, river, stone, tide, umber, vale, willow, xenon, yew, zinc, amber, basil, coral, delta, echo, fern, glade, hazel, isle, juniper, kite, larch, moss, nettle, onyx, prism, reed, sage, thorn, veil, wren, yarrow, zephyr, aspen, bay, cliff, dew, estuary, flint, gorge, heath, inlet, jasper, knoll, ledge, mire, nook, ore

This produces usable badges with 12 bits of checksum entropy. It is suitable for casual use and development but not recommended for production verification workflows.

## Interoperability Note

Two Tychons implementations will produce the same badge for the same key **only if they use the same wordlist** (identical words in identical order). If you share badges across systems or teams, standardize on a specific wordlist file and distribute it alongside the implementation.
