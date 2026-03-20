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

"""Tests for SVG output validity and XSS-escaping."""

import xml.etree.ElementTree as ET

import pytest
from tychons import Badge


def test_svg_is_well_formed_xml(fallback_badge):
    """The SVG output must parse as well-formed XML without errors."""
    svg = fallback_badge.svg
    # fromstring raises xml.etree.ElementTree.ParseError on malformed input
    root = ET.fromstring(svg)
    assert root is not None


def test_svg_contains_expected_elements(fallback_badge):
    """The SVG must contain circle, line, and text elements."""
    svg = fallback_badge.svg
    assert "<circle" in svg
    assert "<line" in svg
    assert "<text" in svg


def test_svg_xss_escape(tmp_path):
    """Words containing XML-special characters must be escaped in SVG output."""
    wordlist_file = tmp_path / "xss.txt"
    # Two words with characters that are dangerous in XML contexts.
    xss_words = ["<script>alert(1)</script>", "foo&bar"]
    wordlist_file.write_text("\n".join(xss_words), encoding="utf-8")

    badge = Badge(b"xss-test-key", lang="xss", wordlist_dir=str(tmp_path))
    svg = badge.svg

    # Literal unescaped tags must not appear.
    assert "<script>" not in svg
    assert "</script>" not in svg

    # Escaped forms must appear.
    assert "&lt;script&gt;" in svg
    assert "&amp;" in svg

    # The SVG must still be well-formed after escaping.
    ET.fromstring(svg)


def test_svg_dimensions(sample_key):
    """The SVG root element must report width and height matching the requested size."""
    size = 200
    badge = Badge(sample_key, size=size)
    svg = badge.svg
    root = ET.fromstring(svg)
    assert root.attrib["width"] == str(size)
    assert root.attrib["height"] == str(size)
