---
layout: default
title: Security Considerations
nav_order: 6
---

# Security Considerations

Tychon Badge is a human verification aid. Understanding what it protects against -- and what it does not -- is important for using it appropriately.

## What Tychon Badge Is

Tychon Badge helps people confirm that the public key they are looking at is the one they expect. It encodes key material into a visual format that humans can compare quickly and accurately. It is designed for the everyday scenario of verifying a known contact's key: "does this badge match the one I saw last time?"

## What Tychon Badge Is Not

Tychon Badge is **not** a cryptographic commitment scheme. It does not replace digital signatures, certificate verification, or any other cryptographic protocol. It supplements these by making the human-facing step -- "is this the right key?" -- faster and more reliable.

## Channel Independence

The security of Tychon Badge rests on the independence of its three channels:

| Channel | Derived from | Context string |
|---|---|---|
| Hue | 4 bytes | `"tychons v1 hue"` |
| Constellation | 64 bytes | `"tychons v1 stars"` |
| Word 1 | 4 bytes | `"tychons v1 word_1"` |
| Word 2 | 4 bytes | `"tychons v1 word_2"` |

Each channel uses a distinct BLAKE3 derive-key context. BLAKE3's design guarantees that outputs from different contexts are cryptographically independent: matching one channel provides zero advantage toward matching any other.

This means an attacker who finds a key that happens to produce the same hue as your key has made no progress toward matching the constellation or the checksum phrase.

## Collision Resistance

### Conservative Estimate

Assuming human observers primarily anchor on three features -- constellation layout, dominant hue, and the checksum phrase -- the estimated number of perceptually distinct badges is approximately **1.3 billion** with a 2048-word BIP-39 wordlist.

### Full Combinatorial Space

The full space of all possible derived parameter combinations is approximately **10^21**. This includes fine variations in star position, size, and brightness that may not be perceptually distinguishable at a glance but would be caught by programmatic comparison.

### Practical Implication

For any realistic population of keys a person encounters in their lifetime, the probability of two keys producing a badge that a careful observer would confuse is negligible.

## Threat Model

### Attacks Tychon Badge Mitigates

- **Accidental key substitution.** A server key changes unexpectedly, a contact's key is replaced by a compromised one -- the badge will look different.
- **Copy-paste errors.** Sharing a key over a messaging app and accidentally truncating it -- the badge will not match.
- **MITM key injection.** An attacker intercepts a key exchange and substitutes their own key -- the badge will differ from the expected one.

In all these cases, the user compares the badge they see against a badge they previously saved or were given out of band. A mismatch on any channel (color, shape, words) signals a problem.

### Attacks Tychon Badge Does Not Mitigate

- **Targeted visual collision.** An adversary who can generate arbitrary key pairs could search for a key whose badge is similar to a target badge. With approximately 1.3 billion perceptually distinct badges, this is feasible with moderate computational resources. Tychon Badge is not designed for this threat.
- **Compromised display.** If an attacker controls the rendering environment (e.g., malware on the user's machine), they can display any badge they want regardless of the actual key.
- **Social engineering.** If a user does not actually compare the badge or does not have a trusted reference badge, no visual scheme can help.

### High-Security Contexts

In environments where targeted attacks are a concern, Tychon Badge should be used alongside -- not instead of -- traditional fingerprint verification. The badge provides a fast first check; the raw fingerprint provides cryptographic certainty.

## Accessibility and Color Vision

Hue is a powerful discriminator for most users, but it is the channel most affected by color vision deficiency. Tychon Badge accounts for this:

- **Constellation shape** (star count, positions, connectivity) does not depend on color perception at all.
- **Star sizes** vary from small to large, providing a non-color visual signal.
- **Checksum phrase** is entirely independent of color.

Users with color vision deficiency lose one of three channels. The remaining two channels still provide strong discrimination. This is a deliberate design choice: accessibility is not an afterthought but a reason for having multiple channels in the first place.
