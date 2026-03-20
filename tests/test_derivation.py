# Copyright 2026 Chris Wells <chris@rhza.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for phrase and visual parameter derivation determinism."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from pathlib import Path

from tychons import Badge
from tychons.tychons import _FALLBACK_WORDLIST, _derive, _derive_hue, _derive_stars, _derive_words


def test_phrase_determinism(sample_key: bytes) -> None:
    """Same key always produces the same phrase and words."""
    badge1 = Badge(sample_key)
    badge2 = Badge(sample_key)
    assert badge1.phrase == badge2.phrase
    assert badge1.words == badge2.words


def test_phrase_differs_for_different_keys() -> None:
    """Different keys produce different phrases (collision would be a bug)."""
    badge_a = Badge(b"key-aaaaaaaaaaaaaaaa")
    badge_b = Badge(b"key-bbbbbbbbbbbbbbbb")
    assert badge_a.phrase != badge_b.phrase


def test_hue_determinism(sample_key: bytes) -> None:
    """Same key always derives the same hue."""
    badge1 = Badge(sample_key)
    badge2 = Badge(sample_key)
    assert badge1._hue == badge2._hue


def test_star_count_range(sample_key: bytes) -> None:
    """Star count must be in {6, 7, 8, 9, 10}."""
    badge = Badge(sample_key)
    assert len(badge._stars) in {6, 7, 8, 9, 10}


def test_word_derivation_uses_wordlist(tmp_path: Path) -> None:
    """Both words come from the custom wordlist when one is provided."""
    wordlist_file = tmp_path / "custom.txt"
    custom_words = ["alpha", "bravo", "charlie", "delta"]
    wordlist_file.write_text("\n".join(custom_words), encoding="utf-8")

    badge = Badge(b"test-key-1234", lang="custom", wordlist_dir=str(tmp_path))

    assert badge.words[0] in custom_words
    assert badge.words[1] in custom_words


# ---------------------------------------------------------------------------
# Task 3.1 — Regression test vectors for the spec sample key
# ---------------------------------------------------------------------------


def test_spec_test_vector_values() -> None:
    """Assert concrete derived values for the spec sample key using BLAKE3."""
    key = b"ssh-rsa AAAAB3NzaC1yc2E"
    hue = _derive_hue(key)
    stars = _derive_stars(key, 128)
    w1, w2 = _derive_words(key, _FALLBACK_WORDLIST)

    assert hue == 225, f"Expected hue=225, got {hue}"
    assert len(stars) == 7, f"Expected 7 stars, got {len(stars)}"
    assert w1 == "basil", f"Expected word1='basil', got {w1!r}"
    assert w2 == "cliff", f"Expected word2='cliff', got {w2!r}"


# ---------------------------------------------------------------------------
# Task 3.2 — HMAC-SHA256 fallback tests
# ---------------------------------------------------------------------------


def test_hmac_fallback_derive() -> None:
    """_derive() with HAS_BLAKE3=False returns correct lengths and is deterministic."""
    key = b"test-key"
    context = "tychons v1 hue"

    with patch("tychons.tychons.HAS_BLAKE3", False):
        out32 = _derive(key, context, length=32)
        assert len(out32) == 32, f"Expected 32 bytes, got {len(out32)}"

        out64 = _derive(key, context, length=64)
        assert len(out64) == 64, f"Expected 64 bytes, got {len(out64)}"

        # Deterministic: same inputs produce same output
        out32b = _derive(key, context, length=32)
        assert out32 == out32b, "HMAC fallback is not deterministic"

    # Output should differ from BLAKE3 path
    import tychons.tychons as _mod

    if _mod.HAS_BLAKE3:
        blake3_out = _derive(key, context, length=32)
        assert out32 != blake3_out, "HMAC fallback should differ from BLAKE3"


def test_hmac_fallback_badge() -> None:
    """Badge with HAS_BLAKE3=False produces valid SVG without error."""
    with patch("tychons.tychons.HAS_BLAKE3", False):
        badge = Badge(b"ssh-rsa AAAAB3NzaC1yc2E")
        svg = badge.svg
        assert svg.startswith("<svg"), "SVG output should start with <svg"
        assert svg  # just ensure no exception was raised and output is non-empty
        assert badge.phrase  # non-empty phrase
