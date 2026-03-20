---
layout: default
title: How It Works
nav_order: 3
---

# How It Works

Tychons takes a public key and produces a small image. This page explains the process at a conceptual level. For the exact byte layouts, algorithms, and color formulas, see the [Technical Reference]({% link technical-reference.md %}).

## The Pipeline

```
Public Key (string or bytes)
        |
        v
   BLAKE3 derive-key
   (4 separate contexts)
        |
   +---------+-----------+-----------+
   |         |           |           |
   v         v           v           v
  Hue     Stars      Word 1      Word 2
(color)  (layout)   (checksum)  (checksum)
   |         |           |           |
   +----+----+           +-----+-----+
        |                      |
        v                      v
   Render image         Format phrase
        |                      |
        +----------+-----------+
                   |
                   v
            Final badge (PNG)
```

## Step 1: Key Derivation

The public key is fed into **BLAKE3 in derive-key mode** four times, each with a different context string. This is the core idea: one key, four independent outputs.

BLAKE3's derive-key mode is purpose-built for this kind of use. The context string acts as a domain separator, ensuring that the hue derivation and the star derivation produce completely unrelated byte sequences even though they start from the same key.

The four derivations are:

| Context | Bytes produced | Used for |
|---|---|---|
| `"tychons v1 hue"` | 4 | Badge color |
| `"tychons v1 stars"` | 64 | Star positions, sizes, brightness, neighbor counts |
| `"tychons v1 word_1"` | 4 | First checksum word |
| `"tychons v1 word_2"` | 4 | Second checksum word |

Implementations that lack BLAKE3 can fall back to HMAC-SHA256. The results will differ, but the security properties are comparable for this use case.

## Step 2: Deriving the Hue

The 4 hue bytes are interpreted as a big-endian unsigned integer and reduced modulo 360, giving a value in the range 0--359. This single hue is shared across all stars and edges in the badge.

Sharing the hue gives the badge visual coherence -- it looks like one thing, not a random scattering of colors. Brightness variation within the shared hue still differentiates individual stars from each other.

## Step 3: Placing the Stars

The 64 star bytes are converted to floating-point scalars (each byte divided by 255). The first scalar determines how many stars to place: between 6 and 10.

For each star, five scalars control:

- **X position** -- where the star sits horizontally
- **Y position** -- where it sits vertically (leaving room at the bottom for the label)
- **Radius** -- how large the star circle is
- **Brightness** -- how light or dark the star appears
- **Neighbor count** -- how many edges this star will draw to its nearest neighbors (1, 2, or 3)

The result is a set of 6--10 points scattered across the badge canvas, each with distinct size and brightness.

## Step 4: Connecting the Stars

Once stars are placed, edges are drawn between them. Each star connects to its *k* nearest neighbors (where *k* is the star's derived neighbor count). The nearest-neighbor rule produces organic-looking constellations: clusters of nearby stars get connected, distant outliers may have only a single link.

Edges are undirected -- if star A connects to star B, that is the same edge as B connecting to A. Duplicates are removed.

## Step 5: Deriving the Checksum Phrase

Two independent 4-byte derivations produce two word indices. Each is interpreted as a big-endian unsigned integer and reduced modulo the wordlist length.

With a 2048-word BIP-39 wordlist, each word carries 11 bits of entropy. The two-word phrase carries 22 bits total -- over 4 million possible phrases. Even with the built-in 64-word fallback list, there are 4,096 possible phrases.

The words are displayed at the bottom of the badge separated by an interpunct: `word_1 · word_2`.

## Step 6: Rendering

The badge is rendered as a square PNG image (default 128x128 pixels):

1. A dark navy background is drawn as a rounded rectangle.
2. Edges are rendered first on a separate compositing layer, with alpha transparency based on the brightness of the connected stars.
3. Stars are drawn on top as filled circles, colored by the shared hue with lightness varying by brightness.
4. A gradient fade at the bottom provides contrast for the label.
5. The two-word checksum phrase is rendered centered at the bottom.
6. The entire image is rendered at 2x resolution and downsampled with Lanczos filtering for clean antialiasing.
7. A rounded rectangle mask is applied so the final image has transparent corners.

## What Makes Two Badges Look Different?

Any change to the public key -- even a single bit -- avalanches through BLAKE3 and changes all four derivations. In practice this means:

- **Different color.** The hue shifts, often dramatically.
- **Different star count.** One badge might have 7 stars, another 10.
- **Different layout.** Star positions, sizes, and brightness all change.
- **Different connectivity.** The constellation edges form a new pattern.
- **Different words.** The checksum phrase is completely unrelated.

The combination of all these channels makes accidental confusion between two badges extremely unlikely.
