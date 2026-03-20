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

"""Tests for Badge size parameter validation."""

import pytest
from tychons import Badge


def test_size_zero_raises():
    with pytest.raises(ValueError):
        Badge("key", size=0)


def test_size_negative_raises():
    with pytest.raises(ValueError):
        Badge("key", size=-1)


def test_size_too_small_raises():
    with pytest.raises(ValueError):
        Badge("key", size=15)


def test_size_too_large_raises():
    with pytest.raises(ValueError):
        Badge("key", size=5000)


def test_size_minimum_succeeds():
    badge = Badge("key", size=16)
    assert badge is not None


def test_size_maximum_succeeds():
    badge = Badge("key", size=4096)
    assert badge is not None


def test_size_float_raises():
    with pytest.raises((ValueError, TypeError)):
        Badge("key", size=128.0)


def test_size_default_succeeds():
    badge = Badge("key")
    assert badge is not None
