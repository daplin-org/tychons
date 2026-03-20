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

import pytest

from tychons import Badge

# The spec's test vector input key.
SAMPLE_KEY = b"ssh-rsa AAAAB3NzaC1yc2E"


@pytest.fixture
def sample_key() -> bytes:
    """The spec's test vector input key."""
    return SAMPLE_KEY


@pytest.fixture
def fallback_badge() -> Badge:
    """A Badge constructed from SAMPLE_KEY with no lang (uses fallback wordlist)."""
    return Badge(SAMPLE_KEY)
