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

import pathlib
import tempfile

import pytest
from tychons import Badge


def test_phrase_determinism(sample_key):
    """Same key always produces the same phrase and words."""
    badge1 = Badge(sample_key)
    badge2 = Badge(sample_key)
    assert badge1.phrase == badge2.phrase
    assert badge1.words == badge2.words


def test_phrase_differs_for_different_keys():
    """Different keys produce different phrases (collision would be a bug)."""
    badge_a = Badge(b"key-aaaaaaaaaaaaaaaa")
    badge_b = Badge(b"key-bbbbbbbbbbbbbbbb")
    assert badge_a.phrase != badge_b.phrase


def test_hue_determinism(sample_key):
    """Same key always derives the same hue."""
    badge1 = Badge(sample_key)
    badge2 = Badge(sample_key)
    assert badge1._hue == badge2._hue


def test_star_count_range(sample_key):
    """Star count must be in {6, 7, 8, 9, 10}."""
    badge = Badge(sample_key)
    assert len(badge._stars) in {6, 7, 8, 9, 10}


def test_word_derivation_uses_wordlist(tmp_path):
    """Both words come from the custom wordlist when one is provided."""
    wordlist_file = tmp_path / "custom.txt"
    custom_words = ["alpha", "bravo", "charlie", "delta"]
    wordlist_file.write_text("\n".join(custom_words), encoding="utf-8")

    badge = Badge(b"test-key-1234", lang="custom", wordlist_dir=str(tmp_path))

    assert badge.words[0] in custom_words
    assert badge.words[1] in custom_words
