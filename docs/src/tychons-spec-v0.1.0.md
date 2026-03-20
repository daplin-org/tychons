# Tychons: Visual Identity Badges for Public Keys

**Status:** Informational Draft  
**Version:** 0.1.0  
**Date:** 2026-03-19  

---

## Abstract

This document specifies Tychons, an algorithm for generating deterministic, human-distinguishable visual identities from public cryptographic keys. A Tychon consists of two components: a constellation-style graphical badge and a two-word checksum phrase. Together these allow users to verify public key identity through rapid visual and linguistic comparison without inspecting raw key material.

---

## 1. Introduction

Verifying public key authenticity is a known usability problem. Raw key fingerprints — hexadecimal or base64 strings — are difficult for humans to compare accurately and impossible to memorize. Existing approaches such as SSH randomart (the "drunken bishop" algorithm) improve on raw fingerprints but lack color, offer limited perceptual diversity, and provide no secondary verification channel.

Tychons addresses these limitations by deriving multiple independent visual variables from a single key, each encoding distinct key material. The resulting badge is designed to be glanceable: two badges representing different keys should be distinguishable within one to two seconds of comparison, with near-zero perceptual collision probability under normal use.

### 1.1 Goals

- Deterministic: the same key always produces the same badge.
- Collision-resistant: perceptually distinct across the full expected key population.
- Locale-aware: checksum words are drawn from a language-appropriate wordlist.
- Accessible: does not rely on color alone for differentiation.
- Simple: implementable from this specification without external dependencies beyond a hash function and a 2D drawing library.

### 1.2 Non-Goals

- Tychons is not a cryptographic commitment scheme. The badge is a human verification aid, not a replacement for cryptographic signature verification.
- Tychons does not protect against an adversary with the ability to generate arbitrary key pairs and search for visual collisions. It is designed for the case where a user compares a badge they see against a badge they expect.

---

## 2. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHOULD", "RECOMMENDED", and "MAY" in this document are to be interpreted as described in RFC 2119.

**Key** — the raw bytes of the public key being visualized. String representations MUST be UTF-8 encoded before processing.

**Badge** — the complete visual output: a square raster image containing a constellation graphic and a two-word checksum phrase.

**Star** — a circular point rendered within the badge, representing a derived anchor in the constellation.

**Edge** — a line segment connecting two stars.

**Hue** — a value in [0, 359] representing a color in HSL space.

**Brightness** — a per-star scalar value in [0, 1] influencing both star size and color lightness.

**Checksum phrase** — two words drawn from a wordlist, derived independently from the key, rendered as a label on the badge.

---

## 3. Cryptographic Foundation

### 3.1 Key Derivation Function

All visual parameters MUST be derived using BLAKE3 in derive-key mode. Each derivation uses a distinct context string, ensuring that outputs are cryptographically independent even though they share the same input key.

```
output = BLAKE3_derive_key(context_string, key_bytes)
```

Implementations that cannot use BLAKE3 MAY substitute HMAC-SHA256 with the context string as the HMAC key and the public key bytes as the message. This substitution reduces the elegance of the construction but does not materially affect security for this use case.

### 3.2 Context Strings

The following context strings are defined by this specification. Implementations MUST use these exact strings to ensure interoperability. Context strings are ASCII-encoded.

| Context string | Derived value |
|---|---|
| `"tychons v1 hue"` | Dominant hue for the badge |
| `"tychons v1 stars"` | Star positions, sizes, brightness, and neighbour counts |
| `"tychons v1 word_1"` | First checksum word index |
| `"tychons v1 word_2"` | Second checksum word index |

The prefix `"tychons v1"` is included in all context strings to domain-separate this protocol from other uses of BLAKE3 derive-key and to allow future versioning.

### 3.3 Byte-to-Scalar Conversion

Unless otherwise stated, a byte value b is converted to a scalar in [0, 1] as:

```
scalar = b / 255.0
```

Multi-byte big-endian unsigned integers are decoded with:

```
value = int.from_bytes(bytes, byteorder="big", signed=False)
```

---

## 4. Derived Parameters

### 4.1 Hue

Derive 4 bytes using context `"tychons v1 hue"`. Decode as a 32-bit unsigned integer and reduce modulo 360:

```
hue = uint32(BLAKE3_derive_key("tychons v1 hue", key)) mod 360
```

The hue is shared across all stars and edges in a single badge. This ensures color coherence while allowing brightness variation to differentiate individual stars.

### 4.2 Stars

Derive 64 bytes using context `"tychons v1 stars"`. Convert all bytes to scalars in [0, 1].

The first scalar determines the star count n:

```
n = 6 + floor(scalars[0] * 4.99)       # n in {6, 7, 8, 9, 10}
```

For each star i in [0, n), read five consecutive scalars starting at index (1 + i * 5), wrapping modulo the available scalar count:

| Parameter | Derivation | Range |
|---|---|---|
| x position | `pad + scalars[idx] * inner_width` | [pad, size - pad] |
| y position | `pad + scalars[idx+1] * inner_height` | [pad, size - pad - label_reserve] |
| size (radius) | `1.5 + scalars[idx+2] * 3.0` | [1.5, 4.5] pixels at size=128 |
| brightness | `0.45 + scalars[idx+3] * 0.55` | [0.45, 1.0] |
| neighbour count | `1 + floor(scalars[idx+4] * 2.99)` | {1, 2, 3} |

Where:

- `pad` = max(8, floor(size / 12))
- `inner_width` = size - 2 * pad
- `inner_height` = inner_width - label_reserve
- `label_reserve` = 18 pixels at size=128, scaled proportionally

### 4.3 Edges

Edges are computed from star positions using a nearest-neighbour algorithm. For each star, the `neighbour_count` nearest other stars (by Euclidean distance) are identified and connected with an edge. Edges are undirected; duplicate edges from symmetric neighbour relationships MUST be deduplicated.

Formally, for each star i with neighbour count k:

1. Compute distances from star i to all other stars j ≠ i.
2. Sort by ascending distance.
3. For each of the k nearest stars j, add edge (min(i,j), max(i,j)) to the edge set.

### 4.4 Checksum Words

Derive 4 bytes using context `"tychons v1 word_1"` and 4 bytes using context `"tychons v1 word_2"`. For each, decode as a 32-bit unsigned integer and reduce modulo the wordlist length W:

```
word_1 = wordlist[ uint32(BLAKE3_derive_key("tychons v1 word_1", key)) mod W ]
word_2 = wordlist[ uint32(BLAKE3_derive_key("tychons v1 word_2", key)) mod W ]
```

The two words MUST be derived from independent contexts. Implementations MUST NOT derive both words from a single hash output to preserve their independence as verification factors.

---

## 5. Color Model

All colors are computed in HSL space and converted to RGB for rendering. The background color is fixed and MUST NOT be derived from the key.

### 5.1 Background

The background color is fixed at RGB (8, 13, 20), a dark navy chosen to maximize contrast with derived star and edge colors.

### 5.2 Star Color

Star lightness is clamped to ensure visibility against the fixed dark background:

```
lightness = 0.60 + brightness * 0.28       # range [0.60, 0.88]
star_color = HSL(hue, saturation=0.65, lightness)
```

### 5.3 Edge Color

Edges use the same hue with reduced saturation and lightness. The mid-brightness of the two connected stars is used:

```
mid_brightness = (star_i.brightness + star_j.brightness) / 2
lightness = 0.50 + mid_brightness * 0.25   # range [0.50, 0.75]
alpha = 0.30 + mid_brightness * 0.40       # range [0.30, 0.70]
edge_color = HSLA(hue, saturation=0.50, lightness, alpha)
```

### 5.4 HSL to RGB Conversion

Standard HSL-to-RGB conversion applies. Implementations SHOULD use a well-tested library function. The conversion formula is defined in CSS Color Module Level 3 (W3C).

### 5.5 Label Color

The checksum phrase label uses the badge hue at fixed saturation and lightness:

```
label_color = HSLA(hue, saturation=0.55, lightness=0.72, alpha=0.86)
```

---

## 6. Rendering

### 6.1 Canvas

The badge is a square raster image of configurable size. The RECOMMENDED default size is 128×128 pixels. Implementations SHOULD support sizes in the range [64, 256] pixels. The badge MUST be rendered with a transparent alpha channel to allow compositing.

Implementations SHOULD render at 2× the target size and downsample using a high-quality filter (e.g. Lanczos) to achieve sub-pixel antialiasing without requiring a vector renderer.

### 6.2 Background

A filled rounded rectangle covering the full canvas is drawn first, using the fixed background color defined in Section 5.1. Corner radius SHOULD be approximately size / 10.

### 6.3 Edges

Edges MUST be rendered before stars so that stars appear on top. Each edge is drawn as a straight line segment between the pixel coordinates of its two endpoint stars. Edge width SHOULD be approximately 0.6 pixels at size=128, scaled proportionally. Edge color and alpha are computed per Section 5.3.

Implementations SHOULD render edges on a separate compositing layer to allow correct alpha blending against the background.

### 6.4 Stars

Each star is rendered as a filled circle centered at its derived position with radius equal to its derived size. Star color is computed per Section 5.2.

### 6.5 Label

A gradient fade from transparent to the background color is rendered at the bottom of the badge, covering approximately the bottom 17% of the canvas height. This provides contrast for the label text.

The checksum phrase is rendered centered horizontally at the bottom of the badge in the format:

```
<word_1>  ·  <word_2>
```

The interpunct (U+00B7) is used as the separator. Font size SHOULD be approximately 8.5pt at size=128. Label color is computed per Section 5.4.

### 6.6 Clipping

The final image MUST be clipped to a rounded rectangle mask matching the background shape to produce clean rounded corners on the transparent canvas.

---

## 7. Wordlists

### 7.1 Format

Wordlists MUST be plain text files encoded in UTF-8, with one word per line. Lines beginning with `#` and blank lines MUST be ignored. The canonical wordlist length is 2048 words, providing 11 bits of entropy per word and 22 bits across the two-word phrase.

Implementations MAY accept wordlists of other lengths. The effective entropy per word is floor(log2(W)) bits where W is the wordlist length.

### 7.2 Language Support

Wordlists are identified by an IETF language tag (e.g. `en`, `es`, `ja`, `zh-hans`). Implementations SHOULD locate wordlist files at:

```
<wordlist_dir>/<lang>.txt
```

Where `wordlist_dir` defaults to a `wordlists/` directory co-located with the implementation. The BIP-39 wordlists maintained by the Trezor project are RECOMMENDED as the canonical source for each supported language.

### 7.3 Fallback

If no language is specified, implementations MAY use a built-in fallback wordlist. The fallback list SHOULD contain at least 64 words. Implementations MUST document the reduced entropy when a non-standard wordlist is in use.

---

## 8. Security Considerations

### 8.1 Perceptual Collision Resistance

The estimated number of perceptually distinct badges under this specification, assuming human observers anchor primarily on constellation layout, dominant hue, and checksum phrase, is approximately 1.3 billion with a 2048-word BIP-39 wordlist. This figure is conservative; the full combinatorial space across all derived channels is approximately 10²¹.

### 8.2 Independence of Visual Channels

Each visual channel (hue, star layout, checksum words) is derived from a distinct BLAKE3 context. An adversary attempting to forge a badge that matches on one channel gains no advantage on any other channel.

### 8.3 Brute Force Resistance

An adversary searching for a key that produces a target badge must match all visual channels simultaneously. Given the independence of channels established in Section 3.2, this requires matching the full BLAKE3 output, which is computationally infeasible.

### 8.4 Limitations

Tychons is designed for human verification in the context of confirming a known contact's key. It is not designed to withstand adversaries capable of:

- Generating large numbers of key pairs to search for visual near-collisions.
- Exploiting perceptual limitations of specific observers (e.g. color vision deficiency).

Deployments in high-security contexts SHOULD supplement Tychons comparison with out-of-band verification of the raw key fingerprint.

### 8.5 Color Vision Deficiency

Star and edge color vary by hue only. Users with color vision deficiency may find hue variation less useful. Constellation shape, star count, star size distribution, and the checksum phrase all remain fully effective independent verification channels for such users.

---

## 9. Interoperability

Two implementations conforming to this specification MUST produce identical badges for the same input key and size, subject to the following:

- The same BLAKE3 context strings defined in Section 3.2 are used.
- The same wordlist (identical word ordering) is used for checksum derivation.
- Rendering differences arising from font selection, sub-pixel rendering, or downsampling filter choice are acceptable and do not constitute non-conformance.

Badge identity SHOULD be verified programmatically by comparing derived parameters (hue, star positions, word indices) rather than pixel-level image comparison.

---

## 10. References

- Aumasson, J-P. et al. "BLAKE3 — One Function, Fast Everywhere." 2020.
- Palatinus, M. et al. "BIP-0039: Mnemonic Code for Generating Deterministic Keys." Bitcoin Improvement Proposals, 2013.
- Loss, D. et al. "The Drunken Bishop: An Analysis of the OpenSSH Fingerprint Visualization Algorithm." 2009.
- Perrig, A. and Song, D. "Hash Visualization: A New Technique to Improve Real-World Security." 1999.
- Park, D. "Identicon." 2007. https://identicon.net
- Bradner, S. "Key Words for Use in RFCs to Indicate Requirement Levels." RFC 2119, 1997.

---

## Appendix A: Test Vectors

Implementations SHOULD verify conformance against the following test vectors. Input keys are UTF-8 strings. All derived values are computed using BLAKE3 derive-key mode.

```
Input:  "ssh-rsa AAAAB3NzaC1yc2E"
Hue:    [to be completed by reference implementation]
Stars:  [to be completed by reference implementation]
Word 1: [to be completed by reference implementation]
Word 2: [to be completed by reference implementation]
```

Test vectors will be populated upon publication of the reference implementation.

---

## Appendix B: Changelog

| Version | Date | Notes |
|---|---|---|
| 0.1.0 | 2026-03-19 | Initial draft |
