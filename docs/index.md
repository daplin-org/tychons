---
layout: default
title: Home
nav_order: 1
permalink: /
---

# Tychon Badge

**Deterministic, glanceable visual identities for public cryptographic keys.**
{: .fs-6 .fw-300 }

Tychon Badge turns any public key into a small constellation-style image paired with a two-word checksum phrase. Different keys produce visibly different badges, giving people a fast and intuitive way to verify key authenticity without reading hex strings.

---

## At a Glance

Every Tychon Badge encodes three independent signals derived from the key:

- **Color** -- a dominant hue shared across stars and edges, immediately visible.
- **Constellation** -- 6 to 10 stars of varying size and brightness connected by nearest-neighbor edges, forming a unique shape.
- **Checksum phrase** -- two words drawn from a wordlist, displayed at the bottom of the badge.

Because each signal is derived from a separate cryptographic context, matching one channel tells an attacker nothing about the others. A mismatch on *any* channel is a clear warning.

---

## Why Does This Exist?

Public key fingerprints are hard for humans. They look like this:

```
SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8
```

Most people cannot reliably compare two fingerprints side by side. SSH randomart tried to solve this with ASCII art, but it is monochrome, limited in diversity, and offers only one verification channel.

Tychon Badge gives you three channels at once -- color, shape, and words -- in a format you can compare in one to two seconds.

[Learn more about the motivation]({% link why.md %}){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[Get started]({% link getting-started.md %}){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## Quick Example

```python
from tychons.tychons import Badge

badge = Badge("ssh-rsa AAAAB3NzaC1yc2E...")
badge.save("my_key.png")
print(badge.phrase)  # e.g. "birch · nova"
```

The same key always produces the same badge. Different keys produce different badges. That is the entire idea.

---

## Project Status

Tychon Badge is in **early draft** (v0.1.0). The specification and reference implementation are functional but the project is still maturing. Contributions and feedback are welcome.

---

## License

Apache License 2.0
