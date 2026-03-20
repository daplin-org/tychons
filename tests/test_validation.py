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

"""Tests for Badge parameter validation: size, lang, and bg_color."""

from __future__ import annotations

import pytest

from tychons import Badge


def test_size_zero_raises() -> None:
    with pytest.raises(ValueError):
        Badge("key", size=0)


def test_size_negative_raises() -> None:
    with pytest.raises(ValueError):
        Badge("key", size=-1)


def test_size_too_small_raises() -> None:
    with pytest.raises(ValueError):
        Badge("key", size=15)


def test_size_too_large_raises() -> None:
    with pytest.raises(ValueError):
        Badge("key", size=5000)


def test_size_minimum_succeeds() -> None:
    badge = Badge("key", size=16)
    assert badge is not None


def test_size_maximum_succeeds() -> None:
    badge = Badge("key", size=4096)
    assert badge is not None


def test_size_float_raises() -> None:
    with pytest.raises((ValueError, TypeError)):
        Badge("key", size=128.0)  # type: ignore[arg-type]


def test_size_default_succeeds() -> None:
    badge = Badge("key")
    assert badge is not None


# ---------------------------------------------------------------------------
# Task 3.3 — lang path traversal security tests
# ---------------------------------------------------------------------------


def test_lang_path_traversal_dot_dot() -> None:
    """lang='../../etc/passwd' raises ValueError before any filesystem access."""
    with pytest.raises(ValueError, match="Invalid lang code"):
        Badge("key", lang="../../etc/passwd")


def test_lang_path_traversal_slash() -> None:
    """lang='foo/bar' raises ValueError before any filesystem access."""
    with pytest.raises(ValueError, match="Invalid lang code"):
        Badge("key", lang="foo/bar")


def test_lang_null_byte() -> None:
    """lang with a null byte raises ValueError before any filesystem access."""
    with pytest.raises(ValueError, match="Invalid lang code"):
        Badge("key", lang="en\x00")


def test_lang_valid_codes() -> None:
    """Valid lang codes pass the validation step (may raise FileNotFoundError if no wordlist)."""
    for code in ("en", "zh-hans", "chinese_simplified"):
        try:
            Badge("key", lang=code)
        except FileNotFoundError:
            pass  # acceptable — wordlist file simply not present in test environment
        except ValueError as exc:
            pytest.fail(f"lang={code!r} should not raise ValueError, got: {exc}")


# ---------------------------------------------------------------------------
# Task 3.4 — bg_color validation tests
# ---------------------------------------------------------------------------


def test_bg_color_default_succeeds() -> None:
    badge = Badge("key", bg_color=(8, 13, 20))
    assert badge is not None


def test_bg_color_black_succeeds() -> None:
    badge = Badge("key", bg_color=(0, 0, 0))
    assert badge is not None


def test_bg_color_white_succeeds() -> None:
    badge = Badge("key", bg_color=(255, 255, 255))
    assert badge is not None


def test_bg_color_value_too_high_raises() -> None:
    with pytest.raises(ValueError):
        Badge("key", bg_color=(256, 0, 0))


def test_bg_color_negative_value_raises() -> None:
    with pytest.raises(ValueError):
        Badge("key", bg_color=(-1, 0, 0))


def test_bg_color_wrong_length_raises() -> None:
    with pytest.raises(ValueError):
        Badge("key", bg_color=(0, 0))  # type: ignore[arg-type]


def test_bg_color_list_raises() -> None:
    with pytest.raises(ValueError):
        Badge("key", bg_color=[8, 13, 20])  # type: ignore[arg-type]


def test_bg_color_float_element_raises() -> None:
    with pytest.raises(ValueError):
        Badge("key", bg_color=(8.0, 13, 20))  # type: ignore[arg-type]
