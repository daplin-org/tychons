---
layout: default
title: Interoperability
nav_order: 8
---

# Interoperability

Tychons is designed so that different implementations produce the same badge for the same input. This page explains what "same" means and what is allowed to vary.

## Conformance Requirements

Two conforming implementations must produce identical badges for the same input when:

1. **The same key bytes** are used (string keys must be UTF-8 encoded before hashing).
2. **The same badge size** is specified.
3. **The same wordlist** is used (identical words in identical order).
4. **BLAKE3 derive-key mode** is used with the exact context strings defined in the spec.

Under these conditions, the following derived values must be identical across implementations:

- Hue (integer, 0--359)
- Star count
- Star positions, radii, brightness values, and neighbor counts
- Edge set
- Checksum word indices

## What May Vary

Pixel-level rendering is not required to be identical. Acceptable differences include:

- **Font selection and rendering.** Different systems have different fonts. The checksum words will look slightly different but read the same.
- **Sub-pixel antialiasing.** Font smoothing and edge rendering vary by OS and graphics library.
- **Lanczos filter implementation.** Slight differences in downsampling filter coefficients are acceptable.
- **Line rendering.** Different drawing libraries may rasterize lines differently at sub-pixel resolution.

These differences are cosmetic. The derived parameters -- which encode the key material -- are what matter for verification.

## Programmatic Verification

To check whether two badges represent the same key, compare the derived parameters rather than the pixel data:

```python
# Correct: compare derived values
assert badge_a._hue == badge_b._hue
assert badge_a.words == badge_b.words
# Compare star positions, etc.

# Incorrect: compare pixels
# (will fail across different platforms even for the same key)
```

## HMAC-SHA256 Fallback

Implementations that use HMAC-SHA256 instead of BLAKE3 will produce different derived values and therefore different badges. The fallback exists for environments where BLAKE3 is unavailable, but it is **not interoperable** with BLAKE3-based implementations.

If you need cross-implementation consistency, all implementations in your ecosystem must use the same hash function.

## Wordlist Consistency

The checksum phrase depends on both the derived word indices and the wordlist contents. Two implementations using different wordlists (or the same words in a different order) will produce different phrases even for the same key.

To ensure consistency:

- Standardize on a specific wordlist file (the BIP-39 English list from the Trezor project is recommended).
- Distribute the wordlist alongside the implementation or pin it to a known commit hash.
- The built-in 64-word fallback list is hardcoded and identical across all copies of the reference implementation.

## Future Versioning

The context string prefix `"tychons v1"` allows future versions of the specification to change the derivation without conflicting with v1 badges. A `v2` specification would use context strings like `"tychons v2 hue"`, producing entirely different badges from the same key.
