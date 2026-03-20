---
layout: default
title: Why Tychon Badge?
nav_order: 2
---

# Why Tychon Badge?

## The Fingerprint Problem

Every time you connect to a new SSH server, accept a PGP key, or verify a contact on an encrypted messenger, you are asked to confirm a public key. In practice, this means comparing something like:

```
SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8
```

against a reference value you received out of band. Most people skip this step. The ones who try are staring at 43 characters of base64 and hoping they don't make a mistake.

This is not a failure of discipline. It is a failure of interface design. Humans are excellent at recognizing faces, comparing colors, and reading short words. They are mediocre at comparing long strings of arbitrary characters. Key verification tools should work with human perception, not against it.

## What Came Before

### Hex and Base64 Fingerprints

The original approach: display the hash of the public key as a hex or base64 string. This is perfectly precise and nearly useless for quick comparison. Studies on hash visualization consistently show that humans make errors when comparing strings longer than about 8 characters.

### SSH Randomart (The Drunken Bishop)

OpenSSH introduced randomart in 2008 -- an ASCII art image derived from the key fingerprint using the "drunken bishop" algorithm. It was a genuine improvement: users could compare two images rather than two strings.

But randomart has significant limitations:

- **Monochrome.** All randomart looks structurally similar at a glance. The differences are in subtle character density patterns.
- **Single channel.** There is only one visual signal (the ASCII pattern). If you miss a difference there, you miss it entirely.
- **Limited diversity.** The visual alphabet is a handful of ASCII characters. Many different keys produce images that feel similar.
- **No secondary verification.** There is no second factor like a word or phrase to cross-check against.

### Identicons and Gravatar-style Avatars

GitHub-style identicons and geometric avatars are visually distinct but are not derived from cryptographic key material. They serve a different purpose (visual differentiation of accounts) and are not suitable for key verification.

## What Tychon Badge Does Differently

Tychon Badge encodes key material across three independent perceptual channels:

### 1. Color (Hue)

A single dominant hue, derived from 4 bytes of key material, colors every star and edge in the badge. Hue is one of the fastest visual properties humans can assess. Two badges in different colors are immediately distinguishable, even in peripheral vision.

### 2. Constellation Layout

Six to ten stars are placed on the canvas at positions derived from the key. Each star has its own size and brightness. Stars are connected by edges using a nearest-neighbor rule, forming a constellation pattern that is unique to the key. The overall shape -- whether clustered or spread, dense or sparse -- is a strong discriminator.

### 3. Checksum Phrase

Two words drawn from a wordlist (ideally a 2048-word BIP-39 list) are displayed at the bottom of the badge. These words are derived from independent cryptographic contexts. Even if two badges happened to look similar in color and shape, the checksum phrase provides a completely separate verification factor.

The words are designed to be spoken aloud. You can tell someone "my badge says *birch nova*" over the phone and they can confirm it without any visual comparison at all.

## Why Three Channels?

Each channel is derived from a separate BLAKE3 derivation context. This means:

- An attacker who finds a key matching one channel (say, the same hue) has made zero progress toward matching the other channels.
- A user who is color-blind still has the constellation shape and the checksum phrase.
- A user in a noisy environment who can't communicate words still has the visual channels.

The channels are redundant by design. Verification should survive the loss of any single channel.

## Why Not Just Use a Longer Fingerprint?

Because the problem is not entropy -- it is human perception. A 256-bit fingerprint has vastly more entropy than any visual representation. But entropy you cannot verify is entropy you do not use. Tychon Badge trades some theoretical precision for practical verifiability. The conservative estimate of perceptually distinct badges (approximately 1.3 billion with a 2048-word wordlist) far exceeds the realistic population of keys any individual will encounter.

## Design Principles

| Principle | What it means |
|---|---|
| **Deterministic** | Same key, same badge. Always. No randomness, no state. |
| **Independent channels** | Hue, layout, and words are derived from separate cryptographic contexts. |
| **Accessible** | The badge does not rely on color alone. Shape and words work for users with color vision deficiency. |
| **Locale-aware** | Checksum words come from language-specific wordlists. |
| **Simple** | Implementable from the spec with a hash function and a 2D drawing library. No complex dependencies. |
