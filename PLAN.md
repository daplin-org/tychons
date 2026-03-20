# Implementation Plan -- Ruff + Mypy Adoption (2026-03-19)

Based on the blueprint at `.state/OVERVIEW.md`.
All file paths are absolute from the repository root `/Users/wells/Projects/tychons`.

---

## Wave 1 -- Configuration Only (no source edits)

Commit message: `chore: add ruff and mypy configuration to pyproject.toml`

### Task 1.1 -- Add ruff and mypy config sections to pyproject.toml
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/pyproject.toml`
- **What to change:**
  Append the following TOML sections after the existing `[tool.uv]` block (after line 34):

  1. `[tool.ruff]` section:
     - `target-version = "py311"`
     - `line-length = 100`
     - `src = ["src", "tests"]`

  2. `[tool.ruff.lint]` section:
     - `select` array with these 16 rule sets: `F`, `E`, `W`, `I`, `N`, `UP`, `B`, `A`, `SIM`, `TCH`, `RUF`, `PT`, `S`, `C4`, `PIE`, `T20`
     - `ignore` array: `["E501", "S311", "T201"]`

  3. `[tool.ruff.lint.per-file-ignores]` section:
     - `"tests/**/*.py" = ["S101", "PT011"]`

  4. `[tool.ruff.lint.isort]` section:
     - `known-first-party = ["tychons"]`

  5. `[tool.ruff.format]` section:
     - `quote-style = "double"`
     - `indent-style = "space"`
     - `line-ending = "lf"`

  6. `[tool.mypy]` section:
     - `python_version = "3.11"`
     - `mypy_path = "src"`
     - `packages = ["tychons"]`
     - `strict = true`
     - `warn_return_any = true`
     - `warn_unused_configs = true`
     - `warn_unreachable = true`
     - `show_error_codes = true`
     - `show_column_numbers = true`

  7. Two `[[tool.mypy.overrides]]` blocks:
     - `module = "blake3.*"` with `ignore_missing_imports = true`
     - `module = "PIL.*"` with `ignore_missing_imports = true`

- **Acceptance criteria:**
  - `ruff check --config pyproject.toml src/ tests/` runs without config errors (violations are expected and acceptable at this stage).
  - `mypy --config-file pyproject.toml` runs without config errors (type errors are expected and acceptable at this stage).
  - No source files are modified.
  - The existing `[tool.hatch.*]` and `[tool.uv]` sections remain unchanged.

### Task 1.2 -- Add ruff, mypy, and pre-commit to dev dependencies
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/pyproject.toml`
- **What to change:**
  In the `[tool.uv]` section (lines 30-34), add `"ruff"`, `"mypy"`, and `"pre-commit"` to the `dev-dependencies` list. The result should be:
  ```toml
  [tool.uv]
  dev-dependencies = [
      "Pillow",
      "pytest",
      "ruff",
      "mypy",
      "pre-commit",
  ]
  ```
- **Acceptance criteria:**
  - `uv sync --dev` (or equivalent) installs ruff, mypy, and pre-commit into the dev environment.
  - Existing dev dependencies (Pillow, pytest) are preserved.

---

## Wave 2 -- Auto-fixes (ruff --fix + ruff format)

Commit message: `style: apply ruff formatting and auto-fixes`

Depends on: Wave 1 complete.

### Task 2.1 -- Run ruff auto-fix on all source files
- **Status:** [x] complete
- **Agent:** @developer
- **Files affected (expected changes):**
  - `/Users/wells/Projects/tychons/src/tychons/tychons.py`
    - **Line 43**: `from typing import Optional` -- will be removed or modified by UP007 (Optional -> X | None).
    - **Line 106**: `import re as _re` -- will be moved to the top import block by I001 (isort).
    - **Lines 715-716**: `Optional["Image.Image"]` and `Optional[str]` will become `"Image.Image" | None` and `str | None` by UP007.
    - **Line 148**: Possible extra blank line removal by E303.
  - `/Users/wells/Projects/tychons/src/tychons/__init__.py` -- import ordering if needed.
  - `/Users/wells/Projects/tychons/tests/*.py` -- import ordering if needed.
- **Command:** `ruff check --fix src/ tests/`
- **Acceptance criteria:**
  - `import re as _re` (currently line 106) is relocated to the stdlib import block at the top of `tychons.py`, grouped with `import math`, `import struct`, etc.
  - `from typing import Optional` (line 43) is either removed entirely (if all uses are replaced) or retained only if needed.
  - `Optional["Image.Image"]` on line 715 becomes `"Image.Image" | None`.
  - `Optional[str]` on line 716 becomes `str | None`.
  - `ruff check src/ tests/` reports zero auto-fixable violations remaining.
  - All existing tests pass (`pytest tests/`).

### Task 2.2 -- Run ruff format on all source files
- **Status:** [x] complete
- **Agent:** @developer
- **Files affected (expected changes):**
  - `/Users/wells/Projects/tychons/src/tychons/tychons.py`
    - **Lines 393-398**: The compressed `if/elif` chain in `_hsl_to_rgb` will be expanded to multi-line form. Each branch (`if h < 60:`, `elif h < 120:`, etc.) will get its assignment on a separate line.
    - **Lines 151-160**: The `_FALLBACK_WORDLIST` compact formatting may be reflowed.
    - General: trailing whitespace, blank line normalization, quote consistency.
  - All `.py` files in `src/` and `tests/` will be formatted.
- **Command:** `ruff format src/ tests/`
- **Acceptance criteria:**
  - `ruff format --check src/ tests/` exits with code 0 (no formatting changes needed).
  - All existing tests pass (`pytest tests/`).

---

## Wave 3 -- Manual Fixes (ruff noqa + mypy type annotations)

Commit message: `fix: resolve mypy strict mode and remaining ruff violations`

Depends on: Wave 2 complete.

### Task 3.1 -- Rename `_SVG_FONT_FAMILY` inside `_render_svg` to lowercase
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/src/tychons/tychons.py`
- **What to change:**
  In `_render_svg()` (approximately line 559 before formatting, may shift after Wave 2), the local variable `_SVG_FONT_FAMILY` uses UPPER_CASE naming which triggers ruff N806 (variable in function should be lowercase). Rename it to `svg_font_family`. Two occurrences:
  1. The dict definition: `_SVG_FONT_FAMILY = {` becomes `svg_font_family = {`
  2. The `.get()` call: `_SVG_FONT_FAMILY.get(normalized, ...)` becomes `svg_font_family.get(normalized, ...)`
- **Acceptance criteria:**
  - `ruff check src/tychons/tychons.py` reports no N806 violation for this variable.
  - All tests pass.

### Task 3.2 -- Add `from __future__ import annotations` to tychons.py
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/src/tychons/tychons.py`
- **What to change:**
  Add `from __future__ import annotations` as the first import statement, immediately after the module docstring (after the closing `"""`). This enables PEP 604 union syntax (`X | None`) in annotations at runtime on 3.11 and makes all annotations strings (deferred evaluation), which is safe for this codebase (no runtime annotation inspection).
- **Acceptance criteria:**
  - `from __future__ import annotations` is the first import in the file.
  - All tests pass (no runtime annotation inspection breaks).

### Task 3.3 -- Add TYPE_CHECKING guard for PIL imports
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/src/tychons/tychons.py`
- **What to change:**
  After the existing `from __future__ import annotations` (added in Task 3.2), add a `TYPE_CHECKING` import block so mypy can see the PIL types:
  ```python
  from typing import TYPE_CHECKING

  if TYPE_CHECKING:
      from PIL import Image, ImageDraw, ImageFont
  ```
  The existing runtime `try/except ImportError` block for PIL (lines 57-61) must remain unchanged -- it handles runtime availability. The `TYPE_CHECKING` block gives mypy visibility into PIL types without requiring PIL at import time.

  If ruff TCH rules flag the `from typing import Optional` import (if it still exists after Wave 2 auto-fixes), remove it since all `Optional[X]` uses have been replaced with `X | None`.
- **Acceptance criteria:**
  - `TYPE_CHECKING` block exists with PIL imports.
  - Runtime `try/except ImportError` block for PIL is preserved.
  - mypy can resolve `Image.Image`, `ImageDraw.ImageDraw`, `ImageFont.FreeTypeFont` type references.
  - `python -c "import tychons"` succeeds without PIL installed (TYPE_CHECKING block is not executed at runtime).

### Task 3.4 -- Fix `struct.unpack` return type for mypy strict mode
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/src/tychons/tychons.py`
- **What to change:**
  `struct.unpack(">I", raw)[0]` returns `Any` under strict mode because `struct.unpack` returns `tuple[Any, ...]`. This occurs in three places:
  1. `_derive_hue()` (line 364): `struct.unpack(">I", raw)[0] % 360`
  2. `_derive_words()` (line 410): `struct.unpack(">I", raw1)[0] % len(wordlist)`
  3. `_derive_words()` (line 411): `struct.unpack(">I", raw2)[0] % len(wordlist)`

  Fix by assigning to a typed intermediate variable or casting. Preferred approach -- use an intermediate with annotation:
  ```python
  (val,) = struct.unpack(">I", raw)
  return int(val) % 360
  ```
  Or add a `# type: ignore[no-any-return]` with the specific error code if the cast approach is too verbose. The blueprint prefers targeted `# type: ignore[specific-code]` over bare `# type: ignore`.
- **Acceptance criteria:**
  - `mypy --strict src/tychons/` reports no errors on struct.unpack lines.
  - All tests pass.

### Task 3.5 -- Fix `_load_font` return type annotation
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/src/tychons/tychons.py`
- **What to change:**
  `_load_font()` (line 415) has return annotation `"ImageFont.FreeTypeFont"` but `ImageFont.load_default()` (line 441) returns a different type (`ImageFont.ImageFont`). Under strict mode mypy will flag this as an incompatible return type.

  Options (choose one):
  1. Widen the return annotation to `ImageFont.FreeTypeFont | ImageFont.ImageFont` (the latter is the base class).
  2. Add `# type: ignore[return-value]` on the `return ImageFont.load_default()` line with a comment explaining PIL stub limitations.

  Option 2 is recommended per the blueprint since PIL stub quality is an acknowledged gap.
- **Acceptance criteria:**
  - `mypy --strict src/tychons/` reports no return-type error for `_load_font`.
  - All tests pass.

### Task 3.6 -- Fix `_nn_edges` lambda type inference under strict mode
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/src/tychons/tychons.py`
- **What to change:**
  In `_nn_edges()` (line 348), the `key=lambda t: t[1]` in `sorted()` may trigger `no-any-return` or need explicit annotation under strict mode. The list comprehension produces `list[tuple[int, float]]`, so the lambda's parameter type should be inferable, but if mypy flags it:
  1. Replace `key=lambda t: t[1]` with `key=lambda t: t[1]  # type: ignore[no-any-return]`, OR
  2. Extract to a named function with explicit annotation.

  Only apply this fix if mypy actually reports an error here after Tasks 3.2-3.4 are complete. This task is conditional.
- **Acceptance criteria:**
  - `mypy --strict src/tychons/` reports no errors on the `_nn_edges` function.

### Task 3.7 -- Ensure all test functions have `-> None` return annotations
- **Status:** [x] complete
- **Agent:** @developer
- **Files:**
  - `/Users/wells/Projects/tychons/tests/test_svg.py`
  - `/Users/wells/Projects/tychons/tests/test_derivation.py`
  - `/Users/wells/Projects/tychons/tests/test_validation.py`
  - `/Users/wells/Projects/tychons/tests/conftest.py`
- **What to change:**
  Under `mypy --strict`, `disallow_untyped_defs` requires all functions to have annotations. Examine every `def test_*` and `def` in the test files. Any function missing a `-> None` return annotation must have one added.

  Current state based on reading:
  - `tests/test_svg.py`: `test_svg_is_well_formed_xml(fallback_badge)`, `test_svg_contains_expected_elements(fallback_badge)`, `test_svg_xss_escape(tmp_path)`, `test_svg_dimensions(sample_key)` -- all missing `-> None`.
  - `tests/test_validation.py`: All `test_*` functions -- all missing `-> None`. The `fallback_badge` fixture parameter in test_svg.py also needs a type annotation (it is `Badge`).
  - `tests/conftest.py`: Fixtures have return annotations already (`-> bytes`, `-> Badge`). OK.
  - `tests/test_derivation.py`: Need to check; likely missing `-> None` on test functions.

  For fixture parameters in test functions, add the type:
  - `fallback_badge` parameter: type is `Badge`
  - `sample_key` parameter: type is `bytes`
  - `tmp_path` parameter: type is `Path` (from `pathlib`)

  Add necessary imports (`from pathlib import Path`, `from tychons import Badge`) to each test file if not already present.
- **Acceptance criteria:**
  - Every function in `tests/` has a return type annotation.
  - Every function parameter in `tests/` has a type annotation.
  - `mypy --strict tests/` reports no `no-untyped-def` errors.
  - All tests pass.

### Task 3.8 -- Fix any remaining mypy errors revealed after Tasks 3.2-3.7
- **Status:** [x] complete
- **Agent:** @developer
- **Files:** `/Users/wells/Projects/tychons/src/tychons/tychons.py`, `/Users/wells/Projects/tychons/src/tychons/__init__.py`
- **What to change:**
  Run `mypy --strict src/tychons/` and fix any remaining errors not covered by prior tasks. Potential issues:
  1. `_hsl_to_rgb` -- if the `if/elif` chain lacks an explicit `else` with a return, mypy may report "missing return statement". Verify the final `else:` branch is present (it is, at line 398: `else: r, g, b = c, 0, x`).
  2. `__init__.py` line 16 re-exports -- `no_implicit_reexport` under strict mode means `Badge`, `load_wordlist`, etc. must be in `__all__` (they already are on line 20, so this should be fine).
  3. Any `Any` type leaking from blake3 calls (covered by `ignore_missing_imports`).

  This is a catch-all task. If Tasks 3.2-3.7 resolve everything, mark this complete with a note that no additional fixes were needed.
- **Acceptance criteria:**
  - `mypy --strict src/tychons/` exits with code 0 (zero errors).
  - `ruff check src/ tests/` exits with code 0 (zero violations).
  - All tests pass (`pytest tests/`).

---

## Wave 4 -- Pre-commit + CI Enforcement

Commit message: `ci: add ruff + mypy pre-commit hooks and CI workflow`

Depends on: Wave 3 complete.

### Task 4.1 -- Create `.pre-commit-config.yaml`
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/.pre-commit-config.yaml` (new file)
- **What to change:**
  Create this file at the project root with the following content:
  ```yaml
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.9.9  # pin to latest stable at time of adoption
      hooks:
        - id: ruff
          args: [--fix]
        - id: ruff-format

    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.15.0  # pin to latest stable at time of adoption
      hooks:
        - id: mypy
          additional_dependencies: [blake3, Pillow]
          args: [--strict]
  ```
  Pin `rev` values to the actual latest stable versions available at the time of implementation. The versions above are placeholders -- the developer must check PyPI/GitHub for the current latest.
- **Acceptance criteria:**
  - `.pre-commit-config.yaml` exists at project root.
  - `pre-commit run --all-files` passes with zero failures.
  - Both ruff hooks (lint + format) and the mypy hook execute.

### Task 4.2 -- Create GitHub Actions CI workflow
- **Status:** [x] complete
- **Agent:** @developer
- **File:** `/Users/wells/Projects/tychons/.github/workflows/lint.yml` (new file; create `.github/workflows/` directory)
- **What to change:**
  Create the workflow file with this content:
  ```yaml
  name: Lint & Type Check
  on: [push, pull_request]
  jobs:
    check:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: "3.11"
        - run: pip install ruff mypy blake3 Pillow
        - run: ruff check src/ tests/
        - run: ruff format --check src/ tests/
        - run: mypy src/tychons/
  ```
- **Acceptance criteria:**
  - File exists at `.github/workflows/lint.yml`.
  - YAML is valid (no syntax errors).
  - Workflow triggers on push and pull_request events.
  - All four steps (checkout, setup-python, install, lint/format/mypy) are present.

### Task 4.3 -- Verify full pipeline passes
- **Status:** [x] complete
- **Agent:** @developer
- **Files:** None (verification only)
- **What to do:**
  Run the complete verification sequence locally:
  1. `ruff check src/ tests/` -- must exit 0
  2. `ruff format --check src/ tests/` -- must exit 0
  3. `mypy --strict src/tychons/` -- must exit 0
  4. `pytest tests/` -- must exit 0
  5. `pre-commit run --all-files` -- must exit 0
- **Acceptance criteria:**
  - All five commands exit with code 0.
  - No warnings or errors in any output.

---

## Parallelization Strategy

```
Wave 1: [Task 1.1, Task 1.2]           -- parallel, both edit pyproject.toml
                                           but in different sections; if using
                                           a single agent, do sequentially
                                           within the same commit

Wave 2: [Task 2.1, then Task 2.2]      -- sequential within wave (format after
                                           fix to avoid double-reformatting)

Wave 3: [Task 3.1]                     -- independent, can start immediately
         [Task 3.2]                     -- independent, can start immediately
         [Task 3.3]                     -- depends on Task 3.2 (needs __future__)
         [Task 3.4, Task 3.5, Task 3.6] -- independent of each other, can
                                           run in parallel after Task 3.3
         [Task 3.7]                     -- independent, can run in parallel
                                           with Tasks 3.4-3.6
         [Task 3.8]                     -- depends on ALL of 3.1-3.7 (catch-all
                                           verification pass)

Wave 4: [Task 4.1, Task 4.2]           -- parallel (different files)
         [Task 4.3]                     -- depends on 4.1 and 4.2 (verification)
```

---

## Key Risks

1. **PIL stub coverage**: `types-Pillow` may not cover all APIs used (e.g., `ImageFont.FreeTypeFont`). Task 3.5 addresses this with a targeted `# type: ignore`. Monitor upstream improvements.
2. **blake3 stubs**: No `types-blake3` package exists. The `ignore_missing_imports` override means mypy cannot verify the `blake3.blake3(...)` call. Accepted gap.
3. **Ruff version drift**: Pin versions in `.pre-commit-config.yaml` and CI. Update deliberately.
4. **`from __future__ import annotations`**: Changes `__annotations__` to strings at runtime. Safe for this codebase (no runtime annotation inspection via `get_type_hints()` or similar).
